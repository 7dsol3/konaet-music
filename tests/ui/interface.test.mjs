import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Window } from 'happy-dom';

const html = fs.readFileSync(new URL('../../emporio/web/index.html', import.meta.url), 'utf8');
const script = fs.readFileSync(new URL('../../emporio/web/app.js', import.meta.url), 'utf8');
const workspaceScript = fs.readFileSync(new URL('../../emporio/web/workspace.js', import.meta.url), 'utf8');
const shellScript = fs.readFileSync(new URL('../../emporio/web/studio-shell.js', import.meta.url), 'utf8');
const first = { id:83, name:'Memphis AC-39', category_id:5, category:'Acoustic guitars', available:true, status:'active', stock:9,
  price_cents:65000, sale_cents:65000, discount_percent:0, specs:{strings:6,material:'Nylon'} };
const second = {...first,id:85,name:'Tagima TW-25',price_cents:89000,sale_cents:89000};

async function environment({recognition=true, message='Two acoustic guitars meet your budget.',researchFailure=false}={}) {
  const window = new Window({url:'http://localhost:8000',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true}});
  window.document.write(html);
  // Test doubles for browser-only APIs. These tests execute the real DOM event
  // handlers, but do not claim browser rendering, microphone or installation QA.
  for(const dialog of window.document.querySelectorAll('dialog')) {
    dialog.showModal=function(){this.setAttribute('open','');};
    dialog.close=function(){this.removeAttribute('open');this.dispatchEvent(new window.Event('close'));};
  }
  const requests=[];let cart=[];let chats=0;let speechStarts=0;let recognitionInstance;let testBalance=1000000;
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
    else if(path.pathname==='/api/capabilities')data={version:'2.1.0',catalog:{count:65},agent:{provider:'local',state:'local_tools_ready'},research:[{id:'wikipedia',name:'Wikipedia',configured:true,status:'not_checked'},{id:'brave',name:'Brave',configured:false,status:'not_checked'}],checkout:{mode:'sandbox'},protection:{max_inflight_per_process:24},hardware:{validation:{notice:'No physical device tested'}}};
    else if(path.pathname==='/api/research'){
      if(researchFailure)return {ok:false,json:async()=>({detail:'The provider is unavailable.'})};
      data={query:body.query,scope:body.scope,coverage:'Controlled public index',mode:'research_excerpts',message:'A public source brief [S1].',checked_at:'2026-11-11T21:00:00Z',from_cache:false,providers:[{name:'Wikipedia',status:'ok'}],sources:[{id:'S1',type:'online',label:'S1 · Source',title:'<img src=x onerror=alert(1)>',url:'https://example.org/source',excerpt:'A controlled excerpt',provider:'Wikipedia'},{id:'S2',type:'online',label:'S2 · Unsafe',title:'Unsafe link',url:'javascript:alert(1)',excerpt:'Must remain plain text',provider:'Example'}],receipt_sha256:'b'.repeat(64),notice:'Excerpts only.'};
    }
    else if(path.pathname==='/api/sandbox/wallet'||path.pathname==='/api/sandbox/wallet/topup'){
      if(options.method==='POST')testBalance+=1000000;
      data={address:'KNT_TEST_example',balance_cents:testBalance,transactions:[]};
    }
    else if(path.pathname==='/api/sandbox/intents')data={id:'t'.repeat(32),status:'pending_test'};
    else if(path.pathname==='/api/sandbox/intents/'+'t'.repeat(32)+'/confirm'||path.pathname==='/api/sandbox/intents/'+'t'.repeat(32))data={id:'t'.repeat(32),amount_cents:65000,status:'paid_test',seal_verified:true,funds_moved:false,receipt:{demo:true},sovereign_opening:{network_finalized:false,args:['1','2']}};
    else if(path.pathname==='/api/hardware/simulate')data={cycles:96,capacity:body.capacity,admitted:8,rejected:4,trace:[{cycle:0,credits:7,rejected:false},{cycle:1,credits:0,rejected:true}],notice:'Logical cycles.',validation:{status:'source_matched_record',vectors:1536,notice:'No physical device tested'}};
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
  window.eval(script);window.eval(workspaceScript);window.eval(shellScript);await flush();
  return {window,document:window.document,requests,get chats(){return chats;},get speechStarts(){return speechStarts;},get recognition(){return recognitionInstance;},async close(){await window.happyDOM.close();}};
}
async function flush(){for(let i=0;i<6;i++)await new Promise(resolve=>setTimeout(resolve,5));}

test('studio search returns from research to the filtered instrument shelf without contacting chat',async()=>{
  const e=await environment();try{
    e.document.querySelector('[data-desk-view-button="research"]').click();
    assert.equal(e.document.body.dataset.deskView,'research');
    assert.equal(e.document.activeElement.id,'workspace-query');
    e.document.querySelector('#studio-query').value='Memphis';
    e.document.querySelector('#studio-search').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    assert.equal(e.document.body.dataset.deskView,'discover');
    const query=new URLSearchParams(e.requests.filter(r=>r.path==='/api/shop').at(-1).query);
    assert.equal(query.get('query'),'Memphis');assert.equal(e.chats,0);
  }finally{await e.close();}
});

test('studio rail reaches existing wallet, guide and keyboard search; lighting follows its control',async()=>{
  const e=await environment();try{
    e.document.querySelector('[data-studio-target="wallet-open"]').click();await flush();
    assert.equal(e.document.querySelector('#wallet-dialog').hasAttribute('open'),true);
    e.document.querySelector('#wallet-dialog').close();
    e.document.querySelector('[data-desk-view-button="guide"]').click();
    assert.equal(e.document.body.dataset.deskView,'guide');
    e.document.activeElement?.blur();
    e.document.dispatchEvent(new e.window.KeyboardEvent('keydown',{key:'/',bubbles:true,cancelable:true}));
    assert.equal(e.document.activeElement.id,'studio-query');
    e.document.querySelector('#studio-light').click();
    assert.equal(e.document.body.classList.contains('ambient'),true);
    assert.equal(e.document.querySelector('#studio-light').getAttribute('aria-pressed'),'true');
    e.document.querySelector('#studio-light').click();assert.equal(e.document.body.classList.contains('ambient'),false);
  }finally{await e.close();}
});

test('voice research reveals the research desk while the instrument shelf is selected',async()=>{
  const e=await environment();try{
    e.document.querySelector('#assistant-scope').value='knowledge';
    e.document.querySelector('#message-input').value='acoustic resonance';
    e.document.querySelector('#chat-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    assert.equal(e.document.body.dataset.deskView,'research');
    assert.equal(e.document.querySelector('#research-panel').hidden,false);
    assert.ok(e.requests.some(r=>r.path==='/api/research'));
  }finally{await e.close();}
});

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
    const art=e.document.querySelector('.code-style-picker select');assert.ok(art);art.value='studio';art.dispatchEvent(new e.window.Event('change'));assert.match(e.document.querySelector('.checkout-code>img').src,/theme=studio/);assert.match(e.document.querySelector('.code-actions a').href,/theme=studio/);
    assert.equal(e.document.querySelector('.checkout-code img').getAttribute('src'),'/api/checkout/'+'a'.repeat(32)+'/code.svg?theme=studio');
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

test('workspace research sends the selected scope and renders safe source links as text',async()=>{
  const e=await environment();try{
    e.document.querySelector('#workspace-query').value='quantum computing';
    e.document.querySelector('#workspace-scope').value='knowledge';
    e.document.querySelector('#workspace-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    const sent=e.requests.find(r=>r.path==='/api/research');assert.equal(sent.body.scope,'knowledge');assert.equal(sent.body.query,'quantum computing');
    assert.equal(e.document.querySelector('#research-panel').hidden,false);assert.equal(e.document.querySelectorAll('.source-card').length,2);
    assert.equal(e.document.querySelector('.source-card img'),null);assert.match(e.document.querySelector('.source-card').textContent,/<img/);
    assert.equal(e.document.querySelectorAll('.source-card a').length,1);assert.equal(e.document.querySelector('.source-card a').getAttribute('rel'),'noopener noreferrer');
    assert.equal(e.document.querySelector('#research-export').disabled,false);
    assert.equal(e.document.querySelectorAll('#research-history button').length,1);
  }finally{await e.close();}
});

test('failed research restores the controls and does not display a stale answer',async()=>{
  const e=await environment({researchFailure:true});try{
    e.document.querySelector('#workspace-query').value='a public topic';
    e.document.querySelector('#workspace-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    assert.equal(e.document.querySelector('#workspace-run').disabled,false);assert.match(e.document.querySelector('#research-error').textContent,/unavailable/);
    assert.equal(e.document.querySelector('#research-answer').textContent,'');assert.equal(e.document.querySelector('#research-export').disabled,true);
  }finally{await e.close();}
});

test('research voice uses a reviewed draft and the explicit research desk',async()=>{
  const e=await environment();try{
    e.document.querySelector('#workspace-scope').value='science';e.document.querySelector('#workspace-voice').click();
    assert.equal(e.speechStarts,0);assert.equal(e.document.querySelector('#assistant-scope').value,'science');
    e.document.querySelector('#microphone-button').click();e.recognition.onresult({results:[[{transcript:'neural audio synthesis'}]]});e.recognition.onend();
    e.document.querySelector('#chat-form').dispatchEvent(new e.window.Event('submit',{cancelable:true}));await flush();
    assert.equal(e.chats,0);assert.equal(e.requests.find(r=>r.path==='/api/research').body.scope,'science');
    assert.match(e.document.querySelector('#assistant-mode').textContent,/SOURCE BRIEF/);
  }finally{await e.close();}
});

test('test wallet, application boundaries and logical hardware states remain explicit',async()=>{
  const e=await environment();try{
    e.document.querySelector('#wallet-open').click();await flush();assert.match(e.document.querySelector('#wallet-address').textContent,/KNT_TEST/);
    e.document.querySelector('#wallet-topup').click();await flush();assert.ok(e.requests.some(r=>r.path==='/api/sandbox/wallet/topup'));
    e.document.querySelector('#connections-open').click();await flush();assert.match(e.document.querySelector('#connection-grid').textContent,/Sandbox only/);assert.match(e.document.querySelector('#connection-grid').textContent,/Not configured/);
    e.document.querySelector('#hardware-open').click();await flush();assert.equal(e.document.querySelectorAll('#hardware-chart svg').length,1);assert.match(e.document.querySelector('#hardware-validation').textContent,/1536/);
    e.document.querySelector('#ambient-toggle').click();assert.equal(e.document.querySelector('#ambient-toggle').getAttribute('aria-pressed'),'true');
  }finally{await e.close();}
});

test('sandbox checkout asks the server for an intent and displays a test receipt',async()=>{
  const e=await environment();try{
    e.document.querySelectorAll('.add-small')[0].click();await flush();e.document.querySelector('#bag-button').click();await flush();
    e.document.querySelector('#checkout-button').click();await flush();
    const approve=[...e.document.querySelectorAll('.sandbox-actions button')].find(b=>b.textContent.startsWith('Approve'));
    assert.ok(approve);approve.click();await flush();
    assert.ok(e.requests.some(r=>r.path==='/api/sandbox/intents'));assert.match(e.document.querySelector('.sandbox-receipt').textContent,/TEST APPROVED/);assert.match(e.document.querySelector('.sandbox-receipt').textContent,/No money moved/);
    assert.ok([...e.document.querySelectorAll('.sandbox-actions button')].some(b=>b.textContent.includes('private Sovereign')));
  }finally{await e.close();}
});
