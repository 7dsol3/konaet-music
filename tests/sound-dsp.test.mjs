import test from 'node:test';
import assert from 'node:assert/strict';
import {performance} from 'node:perf_hooks';
import fs from 'node:fs';
import {pitch,analyze,chordFromChroma,chordMidi,levels,synthesize,originalStudy,wavPCM,tappedTempo,hardwareSamples} from '../emporio/web/sound-dsp.mjs';

// Independent sinusoidal fixtures, never learned by the estimator.
const tone=(hz,sr=48000,dc=0)=>Float32Array.from({length:16384},(_,i)=>dc+.3*Math.sin(2*Math.PI*hz*i/sr));
test('single-note tuning across native sample rates, bass and slight detuning',()=>{
  for(const sr of [16000,44100,48000])for(const hz of [41.2034,82.4069,110,261.6256,440,523.2511,880]){
    const result=pitch(tone(hz,sr,.1),sr);assert.ok(result,`${hz} Hz at ${sr}`);assert.ok(Math.abs(1200*Math.log2(result.hz/hz))<5,`${hz}: estimated ${result.hz}`);
  }
  const result=pitch(tone(440*2**(17/1200)),48000);assert.equal(result.name,'A4');assert.ok(Math.abs(result.cents-17)<2);
});
test('silence, DC, deterministic noise and a low-level input abstain',()=>{
  assert.equal(pitch(new Float32Array(16384),48000),null);assert.equal(pitch(new Float32Array(16384).fill(.3),48000),null);
  let state=12345;const noise=Float32Array.from({length:16384},()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return(state/2**32-.5)*.5;});
  assert.equal(pitch(noise,48000),null);assert.equal(pitch(tone(440).map(x=>x*.0001),48000),null);
  assert.equal(analyze(new Float32Array(16384),48000).chord,null);
});
test('all 24 root-position major/minor triads match independent clean tones',()=>{
  for(let root=0;root<12;root++)for(const quality of ['major','minor']){
    const notes=[48+root,48+root+(quality==='major'?4:3),55+root];
    const samples=Float32Array.from({length:16384},(_,i)=>notes.reduce((s,m)=>s+.12*Math.sin(2*Math.PI*(440*2**((m-69)/12))*i/48000),0));
    const result=analyze(samples,48000).chord;assert.equal(result?.root,root,`${root} ${quality}`);assert.equal(result?.quality,quality);
  }
});
test('single notes, dyads and ambiguous suspended templates do not invent a triad',()=>{
  assert.equal(analyze(tone(440),48000).chord,null);
  const dyad=new Float64Array(12);dyad[0]=1;dyad[7]=1;assert.equal(chordFromChroma(dyad),null);
  const ambiguous=new Float64Array(12);ambiguous[0]=ambiguous[2]=ambiguous[7]=1;assert.equal(chordFromChroma(ambiguous),null);
  assert.throws(()=>chordFromChroma([1,2]));assert.throws(()=>chordFromChroma(new Float64Array(12).fill(NaN)));
});
test('original study handles fractional segment boundaries and exports interoperable PCM16',()=>{
  for(const bpm of [40,90,137,173,200]){const samples=originalStudy(bpm);assert.equal(samples.length,Math.round(960/bpm*22050));assert.ok(levels(samples).peak<=.251);}
  const pcm=new Float32Array([-2,-1,-.5,0,.5,1,2]),buffer=wavPCM(pcm,22050),view=new DataView(buffer);
  assert.equal(Buffer.from(buffer).subarray(0,4).toString(),'RIFF');assert.equal(view.getUint16(20,true),1);assert.equal(view.getUint16(22,true),1);
  assert.equal(view.getUint32(24,true),22050);assert.equal(view.getUint32(40,true),14);assert.equal(view.getInt16(44,true),-32768);assert.equal(view.getInt16(56,true),32767);
  assert.throws(()=>wavPCM([NaN],22050));assert.throws(()=>originalStudy(0));assert.throws(()=>synthesize([100]));assert.throws(()=>chordMidi(12));
});
test('digital-core JavaScript preview matches independent integer recurrence',()=>{
  const steps=[0x7fffffff,0x80000000,0xffffffff],actual=hardwareSamples(steps,512),phase=[0x40000000,0x40000000,0x40000000];
  for(let n=0;n<actual.length;n++){let sum=0;for(let i=0;i<3;i++){const p=Math.floor(phase[i]/65536);sum+=p<32768?p*2-32768:98303-p*2;phase[i]=(phase[i]+steps[i])%4294967296;}assert.equal(actual[n]*32768,Math.floor(sum/8));}
  assert.throws(()=>hardwareSamples([NaN,1,2]));assert.throws(()=>hardwareSamples([1,2,3],100000));
});
test('tap tempo needs multiple sensible intervals',()=>{assert.equal(tappedTempo([0,500,1000,1500]),120);assert.equal(tappedTempo([0,1]),null);assert.equal(tappedTempo([0,5000,10000]),null);});
test('source-independent fixture benchmark reports measured work, without an accuracy claim on recordings',()=>{
  const samples=tone(440),started=performance.now();for(let i=0;i<20;i++)analyze(samples,48000);const duration=performance.now()-started;
  const report={scope:'20 clean synthetic frames; Node process only',elapsed_ms:duration,mean_ms:duration/20,frame_samples:16384,real_recordings_tested:false};
  fs.mkdirSync(new URL('../artifacts/',import.meta.url),{recursive:true});fs.writeFileSync(new URL('../artifacts/audio-dsp-timing.json',import.meta.url),JSON.stringify(report,null,2)+'\n');assert.ok(Number.isFinite(report.mean_ms));
});
