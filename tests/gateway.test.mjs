import test from 'node:test';
import assert from 'node:assert/strict';
import gateway from '../deploy/gateway/index.mjs';
const env={KONAET_BACKEND_URL:'https://example-preview.trycloudflare.com',KONAET_GATEWAY_SECRET:'a-private-test-value-not-a-real-key'};
async function mocked(run,implementation){const original=globalThis.fetch;globalThis.fetch=implementation;try{await run();}finally{globalThis.fetch=original;}}

test('gateway forwards only the demo session and authenticates the origin',async()=>{
  await mocked(async()=>{
    const request=new Request('https://workspace.example/api/session',{headers:{Cookie:'platform_private=do-not-forward; emporio_session=example_session',Authorization:'must-not-forward','oai-authenticated-user-email':'private@example.org','X-Konaet-Gateway':'forged'}});
    const response=await gateway.fetch(request,env);assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');
  },async(url,options)=>{
    assert.equal(url.origin,env.KONAET_BACKEND_URL);assert.equal(options.headers.get('X-Konaet-Gateway'),env.KONAET_GATEWAY_SECRET);
    assert.equal(options.headers.get('cookie'),'emporio_session=example_session');assert.equal(options.headers.get('authorization'),null);assert.equal(options.headers.get('oai-authenticated-user-email'),null);
    return Response.json({ok:true});
  });
});
test('gateway denies foreign writes, unknown routes and nonconfigured origins',async()=>{
  await mocked(async()=>{
    assert.equal((await gateway.fetch(new Request('https://workspace.example/api/chat',{method:'POST',headers:{Origin:'https://foreign.example'},body:'{}'}),env)).status,403);
    assert.equal((await gateway.fetch(new Request('https://workspace.example/admin'),env)).status,404);
    assert.equal((await gateway.fetch(new Request('https://workspace.example/'),{...env,KONAET_BACKEND_URL:'https://127.0.0.1/'})).status,503);
  },async()=>assert.fail('Invalid request reached the origin'));
});
test('gateway rejects actual oversized bodies without trusting a Content-Length header',async()=>{
  await mocked(async()=>{
    const request=new Request('https://workspace.example/api/research',{method:'POST',body:'x'.repeat(17000)});
    assert.equal((await gateway.fetch(request,env)).status,413);
  },async()=>assert.fail('Oversized body reached the origin'));
});
test('an offline Python host is an availability failure, never a confirmed transaction',async()=>{
  await mocked(async()=>{
    const api=await gateway.fetch(new Request('https://workspace.example/api/sandbox/intents',{method:'POST',body:'{}'}),env);
    assert.equal(api.status,503);assert.match((await api.json()).detail,/No transaction was confirmed/);
    const page=await gateway.fetch(new Request('https://workspace.example/checkout/'+'a'.repeat(32)),env);
    assert.equal(page.status,503);assert.match(await page.text(),/does not establish whether its quote has expired/);
  },async()=>{throw Error('offline');});
});
test('upstream loopback redirects are rewritten and foreign redirects are rejected',async()=>{
  await mocked(async()=>{
    const response=await gateway.fetch(new Request('https://workspace.example/'),env);
    assert.equal(response.headers.get('location'),'https://workspace.example/checkout/example');
  },async()=>new Response(null,{status:307,headers:{Location:'http://localhost:8032/checkout/example'}}));
  await mocked(async()=>assert.equal((await gateway.fetch(new Request('https://workspace.example/'),env)).status,502),async()=>new Response(null,{status:307,headers:{Location:'https://foreign.example/'}}));
});
