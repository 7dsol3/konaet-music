// Standalone demonstration: all balances/receipts are editable browser data.
// No account credentials, customer records, server seals or model keys are bundled.
export const QUALITIES={major:[0,4,7],minor:[0,3,7],sus2:[0,2,7],sus4:[0,5,7],diminished:[0,3,6]};
const NOTES=['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'];
const clone=x=>structuredClone(x), money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'BRL'}).format(n/100);
const check=(ok,message)=>{if(!ok)throw Error(message);};
const integer=(n,min,max)=>Number.isSafeInteger(n)&&n>=min&&n<=max;
const note=n=>NOTES[n%12]+(Math.floor(n/12)-1);
export function program({root=0,quality='major',octave=3}={}) {
  check(integer(root,0,11)&&Object.hasOwn(QUALITIES,quality)&&integer(octave,2,5),'Choose a root, supported triad and octave 2–5.');
  const midi=QUALITIES[quality].map(n=>(octave+1)*12+root+n),steps=midi.map(n=>Math.round(440*2**((n-69)/12)*2**32/48000)),phases=[0x40000000,0x40000000,0x40000000],pcm=[],blocks=[];
  for(let n=0;n<512;n++){let sum=0;for(let i=0;i<3;i++){const p=phases[i]>>>16;sum+=p<32768?2*p-32768:98303-2*p;phases[i]=(phases[i]+steps[i])>>>0;}pcm.push(sum>>3);}
  for(let i=0;i<512;i+=64){const b=pcm.slice(i,i+64);blocks.push({valid:true,peak:Math.max(...b.map(Math.abs)),energy:b.reduce((a,x)=>a+x*x,0),clipped:b.filter(x=>Math.abs(x)>=32700).length});}
  return{schema:'konaet.audio-program.v1',mode:'browser_reference',core:'KONAET H-01',physical_device_connected:false,sample_rate:48000,master_clock_hz:12288000,root,quality,octave,midi,notes:midi.map(note),phase_steps:steps,voice_mask:7,preview_pcm16:pcm,meter_blocks:blocks,rtl_parameters:steps.map((s,i)=>`localparam logic [31:0] STEP_${i} = 32'd${s};`).join('\n'),validation:{status:'browser_reference',physical_device_tested:false},notice:'Computed in this browser. No physical FPGA or DAC is connected.'};
}
export function simulate({cycles=96,capacity=8,refill_every=5,burst=40}={}) {
  check(integer(cycles,16,192)&&integer(capacity,1,32)&&integer(refill_every,1,32)&&integer(burst,1,cycles),'Invalid bounded simulation inputs.');
  let credits=capacity;const trace=[];
  for(let n=0;n<cycles;n++){const request=n<burst||n%7===0,refill=n%refill_every===0,available=Math.min(capacity,credits+Number(refill)),admitted=request&&available>0;credits=available-Number(admitted);trace.push({cycle:n,request,refill,admitted,rejected:request&&!admitted,credits});}
  return{mode:'browser_simulation',cycles,capacity,trace,admitted:trace.filter(t=>t.admitted).length,rejected:trace.filter(t=>t.rejected).length,physical_device_connected:false,notice:'Logical browser reference; not real network traffic.',validation:{status:'browser_reference',notice:'No physical board is connected.'}};
}
export function explain(b) {
  const {midi,hz,root,quality,reference=440}=b;const facts=[];let practice;
  if(integer(root,0,11)&&Object.hasOwn(QUALITIES,quality)){
    facts.push(`The browser matched ${NOTES[root]} ${quality}: ${QUALITIES[quality].map(i=>NOTES[(root+i)%12]).join(', ')}.`,'This is a triad-template estimate, not song identification.');
    practice='Play the root alone, then add the other two notes. Listen for a stable balance.';
  }else{
    check(integer(midi,0,127)&&Number.isFinite(hz)&&hz>0&&Number.isFinite(reference)&&reference>=430&&reference<=450,'Provide a valid pitch or triad.');
    const target=reference*2**((midi-69)/12),cents=1200*Math.log2(hz/target);check(Math.abs(cents)<=50.01,'Frequency and nearest MIDI note are inconsistent.');
    facts.push(`The browser estimated ${note(midi)} at ${hz.toFixed(2)} Hz; target ${target.toFixed(2)} Hz at A4 = ${reference} Hz.`,`Tuning offset: ${cents.toFixed(1)} cents.`);practice='Use small tuning adjustments and recheck one sustained note in a quiet room.';
  }
  return{mode:'checked_music_rules',facts,practice,audio_uploaded:false,model_message:null,model_state:b.neural?'not_available_in_browser_demo':undefined,notice:'Browser DSP estimates can be wrong. No trained model or raw audio upload is used.'};
}
export function createRuntime({catalog,base,storage,crypto,fetch,qrcode,now=()=>Date.now(),pageURL=globalThis.location?.href||base}) {
  base=new URL(base);check(['https:','http:'].includes(base.protocol),'Serve the browser demo over HTTP or HTTPS.');
  const key='konaet.music.browser.v1:'+base.pathname,products=catalog.products,map=new Map(products.map(p=>[p.id,p]));
  const random=()=>Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
  const fresh=()=>({cart:{},history:[],balance:1000000,intents:{},attempts:{},id:random()});
  let s=fresh(),storageAvailable=true,importedId=null;const quotes=new Map(),images=new Map();let queue=Promise.resolve();
  try{const saved=JSON.parse(storage.getItem(key)||'null');if(saved&&typeof saved==='object'&&saved.cart&&Array.isArray(saved.history)&&integer(saved.balance,0,1e12)&&saved.intents&&saved.attempts&&/^[a-f0-9]{32}$/.test(saved.id))s=saved;}catch{storageAvailable=false;}
  function save(){try{storage.setItem(key,JSON.stringify(s));}catch{storageAvailable=false;}}
  const hash=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),b=>b.toString(16).padStart(2,'0')).join('');
  function product(id){const p=map.get(id);check(p,'Product not found.');return clone(p);}
  function shop(params=new URLSearchParams()){
    const query=(params.get('query')||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().split(/\s+/).filter(Boolean),category=params.get('category_id'),budget=params.get('max_price_brl'),sort=params.get('sort')||'featured';
    const found=products.filter(p=>(!category||p.category_id===Number(category))&&(!budget||p.sale_cents<=Math.round(Number(budget)*100))&&(params.get('available_only')!=='true'||p.available)&&query.every(q=>(p.name+' '+p.category+' '+p.description).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(q)));
    found.sort(sort==='name'?(a,b)=>a.name.localeCompare(b.name):sort==='price_desc'?(a,b)=>b.sale_cents-a.sale_cents:sort==='price_asc'?(a,b)=>a.sale_cents-b.sale_cents:(a,b)=>Number(b.available)-Number(a.available)||b.discount_percent-a.discount_percent||a.sale_cents-b.sale_cents);
    return{products:clone(found),total_matches:found.length,currency:'BRL',snapshot:'Bundled fictional case catalog'};
  }
  function cart(){const items=Object.entries(s.cart).filter(([id,qty])=>map.has(Number(id))&&integer(qty,1,20)).map(([id,qty])=>{const p=product(Number(id));return{product:p,quantity:qty,line_total_cents:p.sale_cents*qty,available:p.available&&qty<=p.stock};});return{items,quantity:items.reduce((a,i)=>a+i.quantity,0),subtotal_cents:items.reduce((a,i)=>a+i.line_total_cents,0),checkout_available:items.length>0&&items.every(i=>i.available)};}
  async function fromToken(token){
    check(typeof token==='string'&&token.length<400,'Invalid quote link.');
    const fields=token.split('~');check(fields.length===6&&fields[0]==='1'&&fields[1]===catalog.fingerprint.slice(0,10),'This quote uses an older catalog. Prepare a new one.');
    const created=Number.parseInt(fields[2],36)*1000;check(Number.isSafeInteger(created)&&created<=now()+30000&&created+900000>now(),'This quote has expired. Prepare a new one.');
    check(['p','c'].includes(fields[3])&&/^[a-f0-9]{16}$/.test(fields[5]),'Invalid quote data.');
    const pairs=fields[4].split(',');check(pairs.length>=1&&pairs.length<=12,'Choose up to twelve different instruments.');
    const ids=new Set(),method=fields[3]==='p'?'pix':'card';
    const items=pairs.map(pair=>{check(/^[0-9a-z]+\.[0-9a-z]+$/.test(pair),'Invalid product selection.');const [id,qty]=pair.split('.').map(n=>Number.parseInt(n,36)),p=product(id);check(!ids.has(id)&&integer(qty,1,20)&&p.available&&qty<=p.stock,'This quantity is unavailable.');ids.add(id);const discount=p.discount_percent||(method==='pix'?5:0),unit=Math.floor((p.price_cents*(100-discount)+50)/100);return{product_id:id,name:p.name,quantity:qty,unit_total_cents:unit,line_total_cents:unit*qty,list_total_cents:p.price_cents*qty,discount_percent:discount,promotion_applied:!!p.discount_percent};});
    const id=(await hash(token)).slice(0,32),url=new URL(base);url.searchParams.set('q',token);
    const result={id,items,method,currency:'BRL',schema:'konaet.browser-quote.v1',pricing_policy:'unit_round_v1',subtotal_cents:items.reduce((a,i)=>a+i.line_total_cents,0),created_at:new Date(created).toISOString(),expires_at:new Date(created+900000).toISOString(),status:'quote',demo:true,browser_only:true,shipping:'Delivery is not included. This is an unsigned browser demonstration.',checkout_url:url.href};
    quotes.set(id,result);return result;
  }
  async function prepare(b){
    check(typeof b.request_key==='string'&&/^[A-Za-z0-9_-]{16,80}$/.test(b.request_key)&&['pix','card'].includes(b.method),'Invalid checkout request.');
    const c=cart();check(c.checkout_available,'Your bag is empty or contains unavailable quantities.');
    const selection=c.items.map(i=>i.product.id.toString(36)+'.'+i.quantity.toString(36)).join(','),selectionKey=b.method+':'+selection;
    const old=s.attempts[b.request_key];if(old){check(old.selection===selectionKey,'The bag changed. Prepare a new checkout.');return fromToken(old.token);}
    const token=['1',catalog.fingerprint.slice(0,10),Math.floor(now()/1000).toString(36),b.method==='pix'?'p':'c',selection,random().slice(0,16)].join('~');
    const quote=await fromToken(token);s.attempts[b.request_key]={selection:selectionKey,token,id:quote.id};
    if(Object.keys(s.attempts).length>40)delete s.attempts[Object.keys(s.attempts)[0]];save();return quote;
  }
  function ownedQuote(id){return Object.values(s.attempts).some(a=>a.id===id);}
  function codeSVG(quote,theme){
    check(['signature','orbit','studio'].includes(theme),'Unknown code artwork.');
    const qr=qrcode(0,'H');qr.addData(quote.checkout_url,'Byte');qr.make();const n=qr.getModuleCount(),unit=8,symbol=(n+8)*unit,w=symbol+64,h=symbol+220,colors={signature:['#f7f7ef','#143f36'],orbit:['#eef3fb','#172f4c'],studio:['#fff7e9','#3e3425']}[theme];
    let data='';for(let y=0;y<n;y++)for(let x=0;x<n;x++)if(qr.isDark(y,x))data+=`M${32+(x+4)*unit} ${106+(y+4)*unit}h8v8h-8z`;
    const art=theme==='orbit'?`<g transform="translate(${w-56} 49)" stroke="#658aaf" fill="none"><ellipse rx="28" ry="12" transform="rotate(-28)"/><ellipse rx="12" ry="28" transform="rotate(-28)"/><circle r="5" fill="#a8c9ed"/></g>`:theme==='studio'?`<g transform="translate(${w-59} 44)" stroke="#9b7545" fill="none" stroke-width="2"><path d="M0-15V20M12-20V15M0-15L12-20"/><ellipse cx="-5" cy="20" rx="6" ry="4" fill="#efdfbd"/><ellipse cx="7" cy="15" rx="6" ry="4" fill="#efdfbd"/></g>`:`<circle cx="${w-48}" cy="49" r="8" fill="#c5f075"/>`;
    return`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><title>KONAET browser quote ${quote.id.slice(-10)}</title><rect x="1" y="1" width="${w-2}" height="${h-2}" rx="30" fill="${colors[0]}" stroke="#d7dfcc" stroke-width="2"/><path d="M38 39 53 30 68 39 68 57 53 66 38 57Z M38 39 53 48 68 39 M53 48V66" fill="none" stroke="#164c41" stroke-width="3"/><text x="82" y="48" font-family="Arial,sans-serif" font-size="24" font-weight="700" letter-spacing="3" fill="#164c41">KONAET</text><text x="83" y="68" font-family="Arial,sans-serif" font-size="10" letter-spacing="2" fill="#64796a">BROWSER / DEMO CHECKOUT</text>${art}<rect x="32" y="106" width="${symbol}" height="${symbol}" fill="white"/><path fill="${colors[1]}" d="${data}"/><text x="32" y="${symbol+158}" font-family="Arial,sans-serif" font-size="20" fill="#164c41">${money(quote.subtotal_cents)}</text><text x="32" y="${symbol+188}" font-family="Arial,sans-serif" font-size="12" fill="#64796a">Unsigned preview. Never proof of payment.</text></svg>`;
  }
  const ready=(async()=>{const token=new URL(pageURL).searchParams.get('q');if(token){try{importedId=(await fromToken(token)).id;}catch(e){importedId='invalid';quotes.set('invalid',{error:e.message});}}})();
  async function research(b,signal){
    check(typeof b.query==='string'&&b.query.trim().length>=2&&b.query.length<=240,'Use a research query of 2–240 characters.');
    const sources=[],providers=[],scope=b.scope||'open';
    const get=async(url,name,convert)=>{try{const r=await fetch(url,{signal});check(r.ok,'Provider unavailable');convert(await r.json());providers.push({name,status:'ok'});}catch(e){if(e.name==='AbortError')throw e;providers.push({name,status:'unavailable'});}};
    if(['open','knowledge','web'].includes(scope))await get('https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch='+encodeURIComponent(b.query)+'&gsrlimit=4&prop=extracts&exintro=1&explaintext=1&exlimit=4&format=json&origin=*','Wikipedia',j=>{for(const p of Object.values(j.query?.pages||{}))sources.push({title:p.title,url:'https://en.wikipedia.org/?curid='+p.pageid,excerpt:(p.extract||'').slice(0,650),provider:'Wikipedia'});});
    if(scope==='code')await get('https://api.github.com/search/repositories?q='+encodeURIComponent(b.query)+'&per_page=4','GitHub',j=>{for(const p of j.items||[])sources.push({title:p.full_name,url:p.html_url,excerpt:(p.description||'Public source repository').slice(0,650),published_at:p.updated_at,provider:'GitHub'});});
    if(scope==='science')await get('https://api.crossref.org/works?rows=4&query='+encodeURIComponent(b.query),'Crossref',j=>{for(const p of j.message?.items||[])sources.push({title:p.title?.[0]||p.DOI,url:p.URL,excerpt:(p.author||[]).slice(0,3).map(a=>[a.given,a.family].filter(Boolean).join(' ')).join(', '),provider:'Crossref'});});
    sources.forEach((s,i)=>Object.assign(s,{id:'S'+(i+1),type:'online',label:'S'+(i+1)+' · '+s.title}));
    const message=sources.length?'Public source records for “'+b.query+'”:\n\n'+sources.map(s=>s.id+' · '+s.title+'\n'+s.excerpt).join('\n\n'):'The selected public index could not return sources. Try another scope or query. No answer was invented.';
    return{query:b.query,scope,coverage:'Browser requests to selected public APIs',mode:'research_excerpts',message,sources,providers,checked_at:new Date(now()).toISOString(),from_cache:false,receipt_sha256:await hash(JSON.stringify(sources)),notice:'Network access and provider CORS/rate limits apply. This is not exhaustive web search or model synthesis.'};
  }
  async function route(path,options={}){
    await ready;if(options.signal?.aborted)throw new DOMException('Aborted','AbortError');
    const u=new URL(path,base),p=u.pathname,method=options.method||'GET',b=options.body?JSON.parse(options.body):{};
    if(p==='/api/health')return{status:'ok',provider:'local',version:'2.3.0-browser',counts:{products:products.length}};
    if(p==='/api/capabilities')return{version:'2.3.0-browser',catalog:{count:products.length},agent:{provider:'local',state:'browser_rules_ready',model:null},research:[{id:'wikipedia',name:'Wikipedia',configured:true,status:'not_checked'},{id:'github',name:'GitHub',configured:true,status:'not_checked'},{id:'crossref',name:'Crossref',configured:true,status:'not_checked'}],checkout:{mode:'browser_simulation',can_charge_real_money:false},protection:{max_inflight_per_process:0},hardware:{validation:{notice:'JavaScript logical reference only. No physical device connected.'}},storage_available:storageAvailable};
    if(p==='/api/session'){if(method==='DELETE'){s=fresh();save();return{status:'cleared'};}return{history:clone(s.history),verified:false};}
    if(p==='/api/shop'||p==='/api/catalog')return shop(u.searchParams);
    if(p==='/api/compare'){const ids=(u.searchParams.get('ids')||'').split(',').map(Number);check(ids.length>=2&&ids.length<=3&&new Set(ids).size===ids.length,'Choose two or three different instruments.');const ps=ids.map(product);return{products:ps,spec_keys:[...new Set(ps.flatMap(p=>Object.keys(p.specs)))].sort(),notice:'Bundled case specifications. Missing data is not inferred.'};}
    if(p==='/api/cart'){if(method==='PUT'){check(integer(b.product_id,1,1e6)&&integer(b.quantity,0,20),'Invalid item or quantity.');const item=product(b.product_id);check(!b.quantity||item.available&&item.stock>=b.quantity,'This quantity is unavailable.');check(!b.quantity||s.cart[b.product_id]||Object.keys(s.cart).length<12,'A bag can hold up to twelve instruments.');if(b.quantity)s.cart[b.product_id]=b.quantity;else delete s.cart[b.product_id];save();}return cart();}
    if(p==='/api/checkout')return prepare(b);
    if(p.startsWith('/api/checkout/')){const q=quotes.get(p.split('/')[3]);check(q,'Quote not found. Use its complete link or prepare a new one.');check(!q.error,q.error);check(Date.parse(q.expires_at)>now(),'This quote has expired. Prepare a new one.');return clone(q);}
    if(p==='/api/policies')return clone(catalog.policies);
    if(p==='/api/verify')return{verified:false,message:'Private order records are available only in the downloadable Python application. They are never published in this browser demo.'};
    if(p==='/api/research')return research(b,options.signal?AbortSignal.any([options.signal,AbortSignal.timeout(12000)]):AbortSignal.timeout(12000));
    if(p==='/api/hardware/simulate')return simulate(b);
    if(p==='/api/audio/program')return program(b);
    if(p==='/api/music/explain')return explain(b);
    if(p==='/api/chat'){
      check(typeof b.message==='string'&&b.message.length<=2000,'Use a message under 2,000 characters.');
      const text=b.message.toLowerCase(),policy=catalog.policies.find(p=>text.includes(p.topic)||text.includes(p.title.toLowerCase()));
      const aliases={guitar:'guitar',acoustic:'acoustic',bass:'bass',piano:'piano',keyboard:'keys',drum:'drum',ukulele:'ukulele',violin:'violin',trumpet:'brass',flute:'woodwind',saxophone:'woodwind'},word=Object.keys(aliases).find(w=>text.includes(w)),budget=text.match(/(?:under|below|budget|up to)\s*(?:r\$|brl|\$)?\s*([\d,]+(?:\.\d{1,2})?)/i);
      const params=new URLSearchParams({available_only:'true',sort:'price_asc'});if(word)params.set('query',aliases[word]);if(budget)params.set('max_price_brl',budget[1].replaceAll(',',''));const found=shop(params).products.slice(0,4);
      const selected=policy?[]:found,message=policy?policy.summary:found.length?'From the bundled case catalog:\n'+found.map(p=>p.name+' — '+money(p.sale_cents)).join('\n')+'\nUse View to inspect details, add an instrument to your bag or compare results.':'No bundled instrument meets that search. Try a different category or budget.';
      const result={mode:'local',message,tools:[{tool:policy?'bundled_policies':'bundled_catalog',status:'checked'}],results:selected.length?[{kind:'catalog',products:selected}]:[],sources:policy?policy.pages.map(page=>({type:'policy',label:'Store manual · page '+page,page})):[],latency_ms:0,audit_hash:await hash(message)};
      s.history.push({role:'user',content:b.message},{role:'assistant',content:message});s.history=s.history.slice(-30);save();return result;
    }
    if(p==='/api/sandbox/wallet'||p==='/api/sandbox/wallet/topup'){if(method==='POST'){check(s.balance<1e9,'Demo balance limit reached.');s.balance+=1000000;save();}return{address:'KNT_BROWSER_'+s.id.slice(0,12),balance_cents:s.balance,transactions:clone(Object.values(s.intents).slice(-40).reverse())};}
    if(p==='/api/sandbox/intents'){
      check(ownedQuote(b.checkout_id),'Only the browser that created this quote can simulate its payment.');const quote=quotes.get(b.checkout_id);check(quote&&Date.parse(quote.expires_at)>now(),'Quote expired.');check(typeof b.request_key==='string'&&/^[A-Za-z0-9_-]{16,80}$/.test(b.request_key),'Invalid request key.');
      const old=Object.values(s.intents).find(i=>i.request_key===b.request_key||i.checkout_id===b.checkout_id);if(old){check(old.checkout_id===b.checkout_id,'Request key used for another quote.');return clone(old);}
      check(Object.keys(s.intents).length<100,'Reset this demo to clear older transactions.');const i={id:random(),checkout_id:b.checkout_id,amount_cents:quote.subtotal_cents,status:'pending_test',created:new Date(now()).toISOString(),request_key:b.request_key};s.intents[i.id]=i;save();return clone(i);
    }
    if(p.startsWith('/api/sandbox/intents/')){
      const id=p.split('/')[4],i=s.intents[id];check(i,'Test receipt not found on this browser.');
      if(p.endsWith('/confirm')){check(['approve','decline'].includes(b.decision),'Choose approve or decline.');if(i.status!=='pending_test')return clone(i);const q=quotes.get(i.checkout_id);check(q&&Date.parse(q.expires_at)>now(),'Quote expired.');if(b.decision==='approve'){check(s.balance>=i.amount_cents,'Insufficient test credits.');s.balance-=i.amount_cents;}Object.assign(i,{status:b.decision==='approve'?'paid_test':'declined_test',funds_moved:false,seal_verified:false,browser_only:true,receipt:{demo:true,browser_only:true,amount_cents:i.amount_cents,bank_settlement:false}});save();}return clone(i);
    }
    throw Error('This operation requires the downloadable Python application.');
  }
  return{request(path,options={}){const run=()=>route(path,options).then(clone);const result=queue.then(run,run);queue=result.catch(()=>{});return result;},checkoutId:()=>importedId,codeSVG,codeURL(quote,theme='signature'){const id=quote.id+theme;if(!images.has(id)){if(images.size>=120){URL.revokeObjectURL(images.values().next().value);images.delete(images.keys().next().value);}images.set(id,URL.createObjectURL(new Blob([codeSVG(quote,theme)],{type:'image/svg+xml'})));}return images.get(id);}};
}
