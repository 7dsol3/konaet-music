// KONAET public preview gateway. The Python/model host must remain online.
const buckets=new Map();
const allowed=(p,m)=> m==='GET'&&(/^\/(?:$|static\/|checkout\/[A-Za-z0-9_-]{32}$|service-worker\.js$|manual$|docs$|openapi\.json$)/.test(p)||/^\/api\/(?:health|capabilities|session|catalog|policies|shop|compare|cart)$/.test(p)||/^\/api\/checkout\/[A-Za-z0-9_-]{32}(?:\/code\.svg)?$/.test(p)||/^\/api\/sandbox\/(?:wallet|intents\/[A-Za-z0-9_-]{32})$/.test(p))
 || m==='POST'&&(/^\/api\/(?:chat|verify|checkout|research|hardware\/simulate|sandbox\/wallet\/topup|sandbox\/intents)$/.test(p)||/^\/api\/sandbox\/intents\/[A-Za-z0-9_-]{32}\/confirm$/.test(p))
 ||m==='PUT'&&p==='/api/cart'||m==='DELETE'&&p==='/api/session';
function fail(status,detail){return new Response(JSON.stringify({detail}),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});}
const resting=`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KONAET Music — live preview</title><style>body{margin:0;background:#eef5eb;color:#254c3a;font:16px system-ui;min-height:100vh;display:grid;place-items:center}main{padding:40px;max-width:600px;border:1px solid #cddcc6;border-radius:28px;background:#fbfdf8;margin:20px}small{letter-spacing:.15em}h1{font:52px Georgia;letter-spacing:-.04em}p{line-height:1.9;color:#60745a}a{color:#285539;display:inline-block;margin:15px 20px 10px 0}button{background:#244a35;color:#f2f8e9;padding:15px;border:0;border-radius:12px;font:inherit}</style><main><small>KONAET / LIVE PREVIEW</small><h1>The workspace is resting.</h1><p>The public gateway is available, but the demonstration's Python and local-model host is not responding. The preview depends on that host remaining online. No transaction is confirmed by this page.</p><p>A checkout link cannot be checked while the host is unavailable; this does not establish whether its quote has expired.</p><a href="https://github.com/7dsol3/konaet-music">Explore the source ↗</a><a href="/">Try the workspace again ↗</a></main></html>`;
export default {
  async fetch(request,env){
    const url=new URL(request.url), method=request.method;
    if(url.pathname.length+url.search.length>4096)return fail(414,'Request URL is too long');
    if(!allowed(url.pathname,method))return fail(404,'This workspace route is not available');
    if(request.headers.has('upgrade'))return fail(400,'Protocol upgrades are not available');
    const origin=request.headers.get('origin');
    if(!['GET','HEAD'].includes(method)&&origin&&origin!==url.origin)return fail(403,'Cross-origin writes are not allowed');
    const key=request.headers.get('cf-connecting-ip')||'anonymous',now=Date.now();
    if(buckets.size>=1024){for(const[k,v]of buckets)if(now-v.start>60000)buckets.delete(k);if(!buckets.has(key)&&buckets.size>=1024)return fail(503,'The preview is busy');}
    let bucket=buckets.get(key);if(!bucket||now-bucket.start>=60000){bucket={start:now,count:0};buckets.set(key,bucket);}
    if(++bucket.count>120)return new Response('Please retry shortly.',{status:429,headers:{'Retry-After':'60','Cache-Control':'no-store'}});
    let backend;
    try{backend=new URL(env.KONAET_BACKEND_URL);if(backend.protocol!=='https:'||!backend.hostname.endsWith('.trycloudflare.com')||backend.username||backend.password||backend.pathname!=='/'||backend.search||backend.hash||!env.KONAET_GATEWAY_SECRET)throw Error();}
    catch{return fail(503,'The preview origin is not configured');}
    let body;
    if(!['GET','HEAD'].includes(method)){
      const size=Number(request.headers.get('content-length')||0);if(!Number.isInteger(size)||size<0)return fail(400,'Invalid request length');if(size>16384)return fail(413,'Request body is too large');
      const reader=request.body?.getReader();const chunks=[];let total=0,timer;
      try{
        const consume=async()=>{if(reader)for(;;){const{done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>16384)throw Error('size');chunks.push(value);}};
        await Promise.race([consume(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('time')),5000);})]);
        body=new Uint8Array(total);let pos=0;for(const c of chunks){body.set(c,pos);pos+=c.byteLength;}
      }catch(e){reader?.cancel().catch(()=>{});return fail(e.message==='size'?413:408,e.message==='size'?'Request body is too large':'Request body timed out');}finally{clearTimeout(timer);}
    }
    const headers=new Headers({'X-Konaet-Gateway':env.KONAET_GATEWAY_SECRET,'X-Konaet-Client-IP':key,'Accept':request.headers.get('accept')||'*/*'});
    for(const name of ['content-type','origin','if-none-match','if-modified-since','range']){const v=request.headers.get(name);if(v)headers.set(name,v);}
    const cookie=(request.headers.get('cookie')||'').split(';').map(x=>x.trim()).find(x=>/^emporio_session=[A-Za-z0-9_-]{1,128}$/.test(x));if(cookie)headers.set('cookie',cookie);
    const target=new URL(url.pathname+url.search,backend);
    try{
      const upstream=await fetch(target,{method,headers,body,redirect:'manual',signal:AbortSignal.timeout(60000),cf:{cacheTtl:0,cacheEverything:false}});
      if(upstream.status>=500&&method==='GET'&&!url.pathname.startsWith('/api/'))throw Error('host');
      const responseHeaders=new Headers(upstream.headers);responseHeaders.delete('server');
      responseHeaders.set('X-Konaet-Preview','local-python-host');responseHeaders.set('Referrer-Policy','no-referrer');responseHeaders.set('X-Content-Type-Options','nosniff');
      if(url.pathname.startsWith('/api/')||url.pathname.startsWith('/checkout/'))responseHeaders.set('Cache-Control','no-store');
      if(upstream.status>=300&&upstream.status<400&&responseHeaders.has('location')){const location=new URL(responseHeaders.get('location'),backend);if(location.origin!==backend.origin&&!['localhost','127.0.0.1'].includes(location.hostname))return fail(502,'Unexpected upstream redirect');responseHeaders.set('location',url.origin+location.pathname+location.search);}
      return new Response(upstream.body,{status:upstream.status,headers:responseHeaders});
    }catch{
      if(url.pathname.startsWith('/api/'))return fail(503,'The local Python preview host is unavailable. No transaction was confirmed.');
      return new Response(resting,{status:503,headers:{'Content-Type':'text/html;charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
    }
  }
};
