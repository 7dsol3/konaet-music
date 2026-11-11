import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Window } from 'happy-dom';

const html = fs.readFileSync(new URL('../../emporio/web/index.html', import.meta.url), 'utf8');
const script = fs.readFileSync(new URL('../../emporio/web/app.js', import.meta.url), 'utf8');
const first = { id:83, name:'Memphis AC-39', category_id:5, category:'Acoustic guitars', available:true, status:'active', stock:9,
  price_cents:65000, sale_cents:65000, discount_percent:0, specs:{strings:6,material:'Nylon'} };
const second = {...first,id:85,name:'Tagima TW-25',price_cents:89000,sale_cents:89000};

async function environment({recognition=true, message='Two acoustic guitars meet your budget.'}={}) {
  const window = new Window({url:'http://localhost:8000',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true}});
  window.document.write(html);
  // Test doubles for browser-only APIs. These tests execute the real DOM event
  // handlers, but do not claim browser rendering, microphone or installation QA.
  for(const dialog of window.document.querySelectorAll('dialog')) {
    dialog.showModal=function(){this.setAttribute('open','');};
    dialog.close=function(){this.removeAttribute('open');this.dispatchEvent(new window.Event('close'));};
  }
  const requests=[];let cart=[];let chats=0;let speechStarts=0;let recognitionInstance;
  if(recognition) window.SpeechRecognition=class {
    constructor(){recognitionInstance=this;}
    start(){speechStarts++;this.onstart?.();}
    stop(){this.onend?.();}
    abort(){this.onend?.();}
  };
  function cartView(){return {items:cart.map(i=>({product:i.id===83?first:second,quantity:i.quantity,line_total_cents:(i.id===83?65000:89000)*i.quantity,available:true})),quantity:cart.reduce((a,i)=>a+i.quantity,0),subtotal_cents:cart.reduce((a,i)=>a+(i.id===83?65000:89000)*i.quantity,0),checkout_available:cart.length>0};}
  window.fetch=async (url,options={})=>{
    const path=new URL(String(url),'http://localhost:8000');const body=options.body?JSON.parse(options.body):null;
    requests.push({path:path.pathname,query:path.search,method:options.method||'GET',body});let data;
    if(path.pathname==='/api/session'){if(options.method==='DELETE')cart=[];data={history:[],verified:false};}
    else if(path.pathname==='/api/shop')data={products:[first,second]};
    else if(path.pathname==='/api/health')data={provider:'local'};
    else if(path.pathname==='/api/cart'){
      if(options.method==='PUT'){cart=cart.filter(i=>i.id!==body.product_id);if(body.quantity)cart.push({id:body.product_id,quantity:body.quantity});}
      data=cartView();
    }else if(path.pathname==='/api/chat'){
      chats++;data={message,mode:'local',tools:[{tool:'search_products',status:'checked'}],sources:[],latency_ms:5,audit_hash:'a'.repeat(64),results:[{kind:'catalog',products:[first,second]}]};
    }else if(path.pathname==='/api/compare')data={products:[first,second],spec_keys:['strings'],notice:'Recorded specifications.'};
    else if(path.pathname==='/api/checkout')data={id:'a'.repeat(32),items:cartView().items.map(i=>({name:i.product.name,quantity:i.quantity,line_total_cents:i.line_total_cents})),subtotal_cents:cartView().subtotal_cents,method:body.method,expires_at:new Date(Date.now()+900000).toISOString(),checkout_url:'http://localhost:8000/checkout/'+'a'.repeat(32),shipping:'Not included'};
    else throw Error('Unexpected route: '+url);
    return {ok:true,json:async()=>structuredClone(data)};
  };
  window.eval(script);await flush();
  return {window,document:window.document,requests,get chats(){return chats;},get speechStarts(){return speechStarts;},get recognition(){return recognitionInstance;},async close(){await window.happyDOM.close();}};
}
async function flush(){for(let i=0;i<6;i++)await new Promise(resolve=>setTimeout(resolve,5));}

test('catalog renders checked prices and family illustrations with accessible controls',async()=>{
  const e=await environment();try{
    assert.equal(e.document.querySelectorAll('.product-card').length,2);
    assert.match(e.document.querySelector('#catalog-count').textContent,/2 of 2/);
    assert.match(e.document.querySelector('.product-price').textContent,/650/);
    assert.equal(e.document.querySelector('[data-compare-id="83"]').getAttribute('aria-pressed'),'false');
  }finally{await e.close();}
});
test('category, budget and availability controls are sent as structured filters',async()=>{
  const e=await environment();try{
    e.document.querySelector('[data-category="5"]').click();await flush();
    e.document.querySelector('#catalog-budget').value='1000';e.document.querySelector('#available-only').checked=true;
    e.document.querySelector('#catalog-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    const query=new URLSearchParams(e.requests.filter(r=>r.path==='/api/shop').at(-1).query);
    assert.equal(query.get('category_id'),'5');assert.equal(query.get('max_price_brl'),'1000');assert.equal(query.get('available_only'),'true');
  }finally{await e.close();}
});
test('bag and comparison controls use product IDs; a quote renders its actual server code URL',async()=>{
  const e=await environment();try{
    e.document.querySelectorAll('.add-small')[0].click();await flush();
    assert.equal(e.document.querySelector('#bag-count').textContent,'1');
    e.document.querySelector('[data-compare-id="83"]').click();e.document.querySelector('[data-compare-id="85"]').click();
    e.document.querySelector('#compare-open').click();await flush();
    assert.equal(e.document.querySelectorAll('.comparison-table thead td').length,2);
    e.document.querySelector('#bag-button').click();await flush();
    e.document.querySelector('#checkout-button').click();await flush();
    assert.equal(e.document.querySelector('.checkout-code img').getAttribute('src'),'/api/checkout/'+'a'.repeat(32)+'/code.svg');
    assert.equal(e.requests.filter(r=>r.path==='/api/checkout').at(-1).body.method,'pix');
    assert.match(e.document.querySelector('#checkout-content').textContent,/not a purchase/);
  }finally{await e.close();}
});
test('voice is opt-in, fills a draft, and never submits audio text automatically',async()=>{
  const e=await environment();try{
    assert.equal(e.speechStarts,0);e.document.querySelector('#assistant-launcher').click();
    assert.equal(e.speechStarts,0);e.document.querySelector('#microphone-button').click();assert.equal(e.speechStarts,1);
    e.recognition.onresult({results:[[{transcript:'Find acoustic guitars under 1000'}]]});e.recognition.onend();
    assert.equal(e.document.querySelector('#message-input').value,'Find acoustic guitars under 1000');assert.equal(e.chats,0);
    assert.match(e.document.querySelector('#voice-status').textContent,/Nothing was submitted automatically/);
    e.document.querySelector('#chat-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    assert.equal(e.chats,1);assert.equal(e.requests.find(r=>r.path==='/api/chat').body.locale,'en');
  }finally{await e.close();}
});
test('unsupported voice keeps typed chat available and reset clears conversation and bag',async()=>{
  const e=await environment({recognition:false});try{
    assert.equal(e.document.querySelector('#microphone-button').disabled,true);
    e.document.querySelector('#message-input').value='Find acoustic guitars';e.document.querySelector('#chat-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    assert.equal(e.chats,1);assert.equal(e.document.querySelectorAll('.message').length,2);
    e.document.querySelector('#new-chat').click();await flush();
    assert.equal(e.document.querySelectorAll('.message').length,0);assert.equal(e.document.querySelector('#bag-count').textContent,'0');
    assert.ok(e.requests.some(r=>r.path==='/api/session'&&r.method==='DELETE'));
  }finally{await e.close();}
});
test('assistant text is inserted as text, never interpreted as generated markup',async()=>{
  const e=await environment({message:'<img src=x onerror=alert(1)>'});try{
    e.document.querySelector('#message-input').value='Find acoustic guitars';e.document.querySelector('#chat-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    const message=e.document.querySelector('.message.assistant .message-text');assert.equal(message.querySelector('img'),null);assert.match(message.textContent,/<img/);
  }finally{await e.close();}
});
