import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {Window} from 'happy-dom';
import {setupSoundLab} from '../../emporio/web/sound-lab.mjs';
const html=fs.readFileSync(new URL('../../emporio/web/sound-lab.html',import.meta.url),'utf8');
const flush=async()=>{for(let i=0;i<4;i++)await new Promise(resolve=>setTimeout(resolve,2));};

function environment({denied=false,pendingMic=false}={}){
  const window=new Window({url:'https://music.example/sound-lab',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true}});window.document.write(html);
  const q=id=>window.document.getElementById(id),requests=[],nodes=[],revoked=[],created=[];let micCalls=0,stops=0,contexts=0,grant;
  const track={stop(){stops++;}};
  const node=()=>{const value={targets:[],connect(to){this.targets.push(to);},disconnect(){this.targets=[];},start(){},stop(){},gain:{value:0,setTargetAtTime(){}},frequency:{value:0},Q:{value:0}};nodes.push(value);return value;};
  window.AudioContext=class{
    constructor(){contexts++;this.sampleRate=48000;this.destination={destination:true};this.state='suspended';}
    createAnalyser(){const n=node();n.getFloatTimeDomainData=samples=>{for(let i=0;i<samples.length;i++)samples[i]=.3*Math.sin(2*Math.PI*440*i/48000);};return n;}
    createGain(){return node();}createBiquadFilter(){return node();}createBufferSource(){return node();}createMediaStreamSource(){const n=node();n.microphone=true;return n;}createMediaElementSource(){return node();}
    createBuffer(channels,length){const samples=new Float32Array(length);return{getChannelData:()=>samples};}
    async resume(){this.state='running';}async suspend(){this.state='suspended';}async close(){this.state='closed';}
  };
  window.navigator.mediaDevices={getUserMedia:async options=>{micCalls++;assert.equal(options.video,false);if(denied)throw Error('denied');if(pendingMic)return new Promise(resolve=>{grant=()=>resolve({getTracks:()=>[track]});});return{getTracks:()=>[track]};}};
  window.setInterval=()=>1;window.clearInterval=()=>{};
  window.URL.createObjectURL=()=>{const url='blob:local-'+created.length;created.push(url);return url;};window.URL.revokeObjectURL=url=>revoked.push(url);
  q('file-player').pause=()=>{};q('file-player').load=()=>{};q('file-player').play=async()=>{};
  window.fetch=async(path,options)=>{const body=JSON.parse(options.body);requests.push({path,body});const value=path==='/api/music/explain'?{facts:['<img src=x onerror=alert(1)>'],practice:'Try one note.',notice:'An estimate.',model_state:'unavailable'}:{phase_steps:[100,200,300],sample_rate:48000,rtl_parameters:'localparam STEP_0 = 100;',preview_pcm16:[0,1],meter_blocks:[{}],validation:{status:'record_unavailable'}};return{ok:true,json:async()=>value};};
  const controller=setupSoundLab(window.document,window);
  return{window,q,controller,requests,nodes,created,revoked,get micCalls(){return micCalls;},get stops(){return stops;},get contexts(){return contexts;},grant:()=>grant?.(),async close(){controller.dispose();await window.happyDOM.close();}};
}
test('studio loads without microphone, AudioContext, model requests or audio playback',async()=>{const e=environment();try{assert.equal(e.micCalls,0);assert.equal(e.contexts,0);assert.equal(e.requests.length,0);assert.equal(e.q('piano').children.length,24);assert.equal(e.q('tuning-notes').children.length,6);assert.equal(e.q('explain-sound').disabled,true);}finally{await e.close();}});
test('microphone is opt-in, has no speaker-monitor path, and every track stops',async()=>{const e=environment();try{e.q('start-mic').click();await flush();assert.equal(e.micCalls,1);assert.equal(e.controller.state.mode,'microphone');const mic=e.nodes.find(n=>n.microphone);assert.equal(mic.targets.length,1);assert.equal(mic.targets[0].type,'lowpass');e.q('stop-audio').click();assert.equal(e.stops,1);assert.equal(e.controller.state.mode,'off');}finally{await e.close();}});
test('stop also invalidates a pending permission request; a late track is released',async()=>{const e=environment({pendingMic:true});try{e.q('start-mic').click();await flush();e.q('stop-audio').click();e.grant();await flush();assert.equal(e.stops,1);assert.equal(e.controller.state.mode,'off');}finally{await e.close();}});
test('permission denial keeps generated and file controls usable',async()=>{const e=environment({denied:true});try{e.q('start-mic').click();await flush();assert.match(e.q('sound-error').textContent,/permission was denied/);assert.equal(e.q('start-mic').disabled,false);e.q('play-chord').click();await flush();assert.equal(e.controller.state.mode,'generated');assert.equal(e.q('explain-sound').disabled,false);}finally{await e.close();}});
test('coach sends typed estimates only and treats returned text as text',async()=>{const e=environment();try{e.q('play-chord').click();await flush();e.q('neural-coach').checked=true;e.q('explain-sound').click();await flush();const sent=e.requests.at(-1);assert.equal(sent.path,'/api/music/explain');assert.deepEqual(Object.keys(sent.body).sort(),['hz','midi','neural','reference']);assert.equal(sent.body.midi,69);assert.equal(e.q('coach-facts').querySelector('img'),null);assert.match(e.q('coach-facts').textContent,/<img/);assert.match(e.q('coach-model').textContent,/unavailable/);}finally{await e.close();}});
test('local file size and duration are bounded; removal revokes its object URL',async()=>{const e=environment();try{const input=e.q('audio-file');Object.defineProperty(input,'files',{configurable:true,value:[new e.window.File(['audio'],'private-name.wav',{type:'audio/wav'})]});input.dispatchEvent(new e.window.Event('change'));Object.defineProperty(e.q('file-player'),'duration',{configurable:true,value:30});e.q('file-player').onloadedmetadata();assert.equal(e.q('play-file').disabled,false);e.q('play-file').click();await flush();assert.equal(e.controller.state.mode,'file');assert.equal(e.requests.length,0);e.q('clear-file').click();assert.equal(e.revoked.length,1);assert.equal(e.q('play-file').disabled,true);
  Object.defineProperty(input,'files',{configurable:true,value:[{name:'too-big.wav',size:9*1024*1024}]});input.dispatchEvent(new e.window.Event('change'));assert.match(e.q('sound-error').textContent,/8 MiB/);
  Object.defineProperty(input,'files',{configurable:true,value:[new e.window.File(['audio'],'long.wav')]});input.dispatchEvent(new e.window.Event('change'));Object.defineProperty(e.q('file-player'),'duration',{configurable:true,value:100});e.q('file-player').onloadedmetadata();assert.match(e.q('sound-error').textContent,/90 seconds/);assert.equal(e.controller.state.fileReady,false);
}finally{await e.close();}});
test('program parameters reflect the selected chord and become stale after edits',async()=>{const e=environment();try{e.q('chord-root').value='9';e.q('chord-quality').value='minor';e.q('chord-root').dispatchEvent(new e.window.Event('change'));e.q('build-program').click();await flush();assert.deepEqual(e.requests[0],{path:'/api/audio/program',body:{root:9,quality:'minor',octave:3}});assert.equal(e.q('play-hardware').disabled,false);e.q('play-hardware').click();await flush();assert.equal(e.controller.state.mode,'generated');e.q('chord-root').value='1';e.q('chord-root').dispatchEvent(new e.window.Event('change'));assert.equal(e.q('play-hardware').disabled,true);assert.equal(e.q('download-program').disabled,true);}finally{await e.close();}});
test('pagehide releases active tracks, file URLs and audio resources',async()=>{const e=environment();try{e.q('start-mic').click();await flush();e.window.dispatchEvent(new e.window.Event('pagehide'));assert.equal(e.stops,1);assert.equal(e.controller.state.mode,'off');}finally{await e.close();}});
