import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRuntime,program,explain,simulate} from '../../deploy/browser/browser-runtime.mjs';
import {Window} from 'happy-dom';

const catalog=JSON.parse(fs.readFileSync(new URL('../../deploy/browser/catalog.json',import.meta.url),'utf8'));
const context=vm.createContext({});vm.runInContext(fs.readFileSync(new URL('../../deploy/browser/vendor/qrcode.js',import.meta.url),'utf8'),context);
const base='https://example.org/konaet-music/';
const memory=()=>{const data=new Map();return{getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)};};
function runtime(options={}){return createRuntime({catalog,base,crypto:globalThis.crypto,storage:memory(),fetch:async()=>{throw Error('No network allowed by this test');},qrcode:context.qrcode,...options});}
const put=(r,path,body,method='POST')=>r.request(path,{method,body:JSON.stringify(body)});
const request_key='request_1234567890123456';
async function quote(r,id=catalog.products.find(p=>p.available&&p.stock>=2).id){await put(r,'/api/cart',{product_id:id,quantity:2},'PUT');return put(r,'/api/checkout',{request_key,method:'pix'});}

test('browser catalog, stock, filters, comparison and per-unit pricing',async()=>{
 const r=runtime(),list=await r.request('/api/shop?available_only=true&sort=price_asc');assert(list.products.every(p=>p.available));assert(list.products.every((p,i)=>!i||p.sale_cents>=list.products[i-1].sale_cents));
 const q=await quote(r);for(const i of q.items){const p=catalog.products.find(p=>p.id===i.product_id);assert.equal(i.unit_total_cents,Math.floor((p.price_cents*(100-(p.discount_percent||5))+50)/100));assert.equal(i.line_total_cents,i.unit_total_cents*i.quantity);}
 assert.deepEqual(q,await put(r,'/api/checkout',{request_key,method:'pix'}));
 await assert.rejects(put(r,'/api/cart',{product_id:q.items[0].product_id,quantity:21},'PUT'),/quantity/);
 await assert.rejects(r.request('/api/compare?ids=1,1'),/different/);
});
test('quote opens on a fresh device, recalculates amounts and denies foreign test spending',async()=>{
 const owner=runtime(),q=await quote(owner),visitor=runtime({pageURL:q.checkout_url});await visitor.request('/api/session');assert.deepEqual(await visitor.request('/api/checkout/'+visitor.checkoutId()),q);
 await assert.rejects(put(visitor,'/api/sandbox/intents',{checkout_id:q.id,request_key}),/browser that created/);
 const token=new URL(q.checkout_url).searchParams.get('q'),bad=token.replace(catalog.fingerprint.slice(0,10),'outdatedxx'),broken=runtime({pageURL:base+'?q='+bad});await broken.request('/api/session');await assert.rejects(broken.request('/api/checkout/'+broken.checkoutId()),/older catalog/);
 const expired=runtime({now:()=>Date.now()+1000000,pageURL:q.checkout_url});await expired.request('/api/session');await assert.rejects(expired.request('/api/checkout/'+expired.checkoutId()),/expired/);
});
test('duplicate and concurrent confirms debit once; browser receipts never claim seals',async()=>{
 const r=runtime(),before=await r.request('/api/sandbox/wallet'),q=await quote(r),i=await put(r,'/api/sandbox/intents',{checkout_id:q.id,request_key});
 const [a,b]=await Promise.all([put(r,'/api/sandbox/intents/'+i.id+'/confirm',{decision:'approve'}),put(r,'/api/sandbox/intents/'+i.id+'/confirm',{decision:'approve'})]);assert.deepEqual(a,b);assert.equal(a.seal_verified,false);assert.equal(a.funds_moved,false);assert.equal((await r.request('/api/sandbox/wallet')).balance_cents,before.balance_cents-q.subtotal_cents);
 await r.request('/api/session',{method:'DELETE'});await assert.rejects(r.request('/api/sandbox/intents/'+i.id),/not found/);
});
test('state persists without sharing private customer fixtures; missing storage stays usable',async()=>{
 const storage=memory(),a=runtime({storage});await quote(a);assert.equal((await runtime({storage}).request('/api/cart')).quantity,2);
 const r=runtime({storage:{getItem(){throw Error('blocked')},setItem(){throw Error('blocked')}}});assert.equal((await r.request('/api/shop')).products.length,65);assert.equal((await r.request('/api/capabilities')).storage_available,false);assert.equal((await put(r,'/api/verify',{order_id:1,email:'example@example.org'})).verified,false);
 assert.deepEqual(Object.keys(catalog).sort(),['fingerprint','policies','products','schema']);
});
test('browser core and credit gate have deterministic known output and strict bounds',()=>{
 const p=program({root:9,quality:'minor',octave:3});assert.deepEqual(p.phase_steps,[19685267,23409859,29494575]);assert.equal(p.preview_pcm16.length,512);for(let i=0;i<8;i++){const b=p.preview_pcm16.slice(i*64,(i+1)*64);assert.equal(p.meter_blocks[i].energy,b.reduce((a,x)=>a+x*x,0));}
 assert(explain({midi:69,hz:440}).facts[0].includes('A4'));assert.throws(()=>explain({midi:69,hz:100}),/inconsistent/);assert.throws(()=>program({root:12}),/Choose/);const t=simulate();assert.equal(t.trace.length,96);assert(t.trace.every(x=>x.credits>=0&&x.credits<=8));
});
test('external research failure is explicit and never invents sources',async()=>{
 const r=await put(runtime(),'/api/research',{query:'guitar',scope:'knowledge'});assert.equal(r.sources.length,0);assert.equal(r.providers[0].status,'unavailable');assert.match(r.message,/No answer was invented/);
});
test('real DOM handlers work with the browser runtime, including shareable checkout and receipt',async()=>{
 const w=new Window({url:base,settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true}});w.document.write(fs.readFileSync(new URL('../../emporio/web/index.html',import.meta.url),'utf8'));
 for(const d of w.document.querySelectorAll('dialog')){d.showModal=function(){this.setAttribute('open','');};d.close=function(){this.removeAttribute('open');};}
 const r=runtime();w.KonaetRuntime=r;w.eval(fs.readFileSync(new URL('../../emporio/web/app.js',import.meta.url),'utf8'));w.eval(fs.readFileSync(new URL('../../emporio/web/workspace.js',import.meta.url),'utf8'));w.eval(fs.readFileSync(new URL('../../emporio/web/studio-shell.js',import.meta.url),'utf8'));
 const flush=async()=>{for(let i=0;i<12;i++)await new Promise(resolve=>setTimeout(resolve,5));};
 try{await flush();assert.equal(w.document.querySelectorAll('.product-card').length,12);w.document.querySelector('.add-small').click();await flush();w.document.querySelector('#bag-button').click();await flush();w.document.querySelector('#checkout-button').click();await flush();assert(w.document.querySelector('.checkout-link').href.startsWith(base+'?q='));assert(w.document.querySelector('.checkout-code img').src.startsWith('blob:'));w.document.querySelector('.sandbox-actions button').click();await flush();assert.match(w.document.querySelector('.sandbox-receipt').textContent,/TEST APPROVED/);assert.match(w.document.querySelector('.sandbox-receipt').textContent,/no server seal/);}
 finally{await w.happyDOM.close();}
});

// Export actual generated art so the independent Python/ZXing suite decodes
// these JavaScript QR matrices, rather than merely testing the encoder API.
if(process.env.KONAET_QR_EVIDENCE){
 const r=runtime(),q=await quote(r);fs.mkdirSync(process.env.KONAET_QR_EVIDENCE,{recursive:true});for(const theme of ['signature','orbit','studio'])fs.writeFileSync(process.env.KONAET_QR_EVIDENCE+'/'+theme+'.svg',r.codeSVG(q,theme));fs.writeFileSync(process.env.KONAET_QR_EVIDENCE+'/quote.json',JSON.stringify(q));
 fs.writeFileSync(process.env.KONAET_QR_EVIDENCE+'/audio.json',JSON.stringify(program({root:9,quality:'minor',octave:3})));
 fs.writeFileSync(process.env.KONAET_QR_EVIDENCE+'/gate.json',JSON.stringify(simulate()));
}
