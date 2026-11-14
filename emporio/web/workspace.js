"use strict";
(() => {
  const q = s => document.querySelector(s);
  const node = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; };
  const button = (text, cls, run) => { const b = node("button", cls, text); b.type = "button"; b.addEventListener("click", run); return b; };
  const currentLocale = () => window.KonaetI18n?.locale() === "pt" ? "pt-BR" : "en-US";
  const funds = cents => new Intl.NumberFormat(currentLocale(), {style:"currency",currency:"BRL"}).format(cents/100);
  const stamp = value => { const d = new Date(value); return Number.isNaN(d.valueOf()) ? "Date not provided" : d.toLocaleString(currentLocale(), {dateStyle:"medium",timeStyle:"short"}); };
  const state = {busy:false, generation:0, recent:[], result:null, caps:null};
  async function request(path, options={}) {
    if (window.KonaetRuntime) return window.KonaetRuntime.request(path, options);
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 40000);
    try {
      const response = await fetch(path, {credentials:"same-origin",...options,headers:{"Content-Type":"application/json",...(options.headers||{})},signal:controller.signal});
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check the input and try again.");
      return data;
    } finally { clearTimeout(timer); }
  }
  const post = (path, body) => request(path, {method:"POST",body:JSON.stringify(body)});
  function modal(id) { for (const d of document.querySelectorAll("dialog[open]")) d.close(); const d = q("#"+id); if (!d.open) d.showModal(); }
  function error(id, message) { const n=q("#"+id); n.textContent=message||""; n.hidden=!message; }
  function download(name, text, type="application/json") { const url=URL.createObjectURL(new Blob([text],{type})), a=node("a"); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000); }
  function safeLink(value) { try { const u=new URL(value); return u.protocol==="https:"&&!u.username&&!u.password&&!/^(localhost|127\.|\[?::1)/i.test(u.hostname) ? u.href : null; } catch {return null;} }
  function renderResearch(result, remember=true) {
    state.result=result; q("#research-panel").hidden=false; q("#research-answer").textContent=result.message;
    q("#research-state").textContent=(result.mode==="research_model"?"Model explanation · ":"Source brief · ")+result.coverage+" · Retrieved "+stamp(result.checked_at)+(result.from_cache?" · cached for up to 2 minutes":"");
    q("#research-providers").replaceChildren(); q("#research-sources").replaceChildren();
    for (const p of result.providers) { const chip=node("span","provider-chip",p.name+" · "+p.status.replaceAll("_"," ")); chip.dataset.status=p.status; q("#research-providers").append(chip); }
    for (const s of result.sources) {
      const card=node("article","source-card"), link=safeLink(s.url);
      card.append(node("span","",s.id+" / "+s.provider));
      if (link) { const a=node("a","",s.title+" ↗"); a.href=link; a.target="_blank"; a.rel="noopener noreferrer"; card.append(a); } else card.append(node("strong","",s.title));
      card.append(node("p","",s.excerpt),node("small","",s.published_at?"Source date: "+s.published_at:"Source publication date not provided"));
      q("#research-sources").append(card);
    }
    q("#research-notice").textContent=result.notice+" Receipt hash: "+result.receipt_sha256.slice(0,16)+"…";
    q("#research-export").disabled=!result.sources.length;
    if (remember) state.recent=[result,...state.recent.filter(r=>r.query!==result.query||r.scope!==result.scope)].slice(0,5);
    q("#research-history").replaceChildren(...state.recent.map(r=>button(r.query,"",()=>renderResearch(r,false))));
    q("#core-research").textContent=result.sources.length+" source records retrieved";
  }
  async function research(query, scope) {
    if (state.busy) return;
    const generation=++state.generation; state.busy=true; q("#workspace-run").disabled=true;
    q("#research-panel").hidden=false; q("#research-progress").hidden=false; error("research-error","");
    state.result=null;q("#research-answer").textContent="";q("#research-sources").replaceChildren();q("#research-providers").replaceChildren();q("#research-notice").textContent="";q("#research-export").disabled=true;
    q("#research-state").textContent="Retrieving the selected public indexes…";
    try { const r=await post("/api/research",{query,scope,synthesize:q("#workspace-synthesize").checked}); if(generation===state.generation) renderResearch(r); }
    catch(e) { if(generation===state.generation) {error("research-error",e.name==="AbortError"?"The request timed out. Please try again.":e.message);q("#research-state").textContent="Research could not complete.";} }
    finally {if(generation===state.generation){state.busy=false;q("#workspace-run").disabled=false;q("#research-progress").hidden=true;}}
  }
  function clearResearch() { state.generation++;state.busy=false;state.recent=[];state.result=null;q("#workspace-run").disabled=false;q("#research-progress").hidden=true;q("#research-panel").hidden=true;q("#research-answer").textContent="";q("#research-sources").replaceChildren();q("#research-history").replaceChildren();q("#research-export").disabled=true; }
  q("#workspace-form").addEventListener("submit",e=>{e.preventDefault();const message=q("#workspace-query").value.trim(),scope=q("#workspace-scope").value;if(scope==="shop")document.dispatchEvent(new CustomEvent("konaet:ask",{detail:{message,scope}}));else research(message,scope);});
  for (const b of document.querySelectorAll("[data-research]")) b.addEventListener("click",()=>{q("#workspace-query").value=b.dataset.research;q("#workspace-scope").value=b.dataset.scope;research(b.dataset.research,b.dataset.scope);});
  q("#research-focus").addEventListener("click",()=>q("#workspace-query").focus());
  q("#workspace-voice").addEventListener("click",()=>document.dispatchEvent(new CustomEvent("konaet:open-assistant",{detail:{scope:q("#workspace-scope").value}})));
  q("#research-clear").addEventListener("click",clearResearch);
  q("#research-export").addEventListener("click",()=>{const r=state.result;if(!r)return;const text="# KONAET source brief\n\n"+r.query+"\n\nRetrieved: "+r.checked_at+"\nCoverage: "+r.coverage+"\n\n"+r.message+"\n\n"+r.sources.map(s=>"- ["+s.id+"] "+s.title+": "+s.url).join("\n")+"\n\n"+r.notice;download("konaet-source-brief.md",text,"text/markdown;charset=utf-8");});
  document.addEventListener("konaet:research-result",e=>renderResearch(e.detail));
  document.addEventListener("konaet:reset",()=>{clearResearch();q("#wallet-transactions").replaceChildren();q("#wallet-balance").textContent="Refresh this test wallet";q("#wallet-address").textContent="";});
  for (const b of document.querySelectorAll("[data-workspace-close]")) b.addEventListener("click",()=>q("#"+b.dataset.workspaceClose).close());
  q("#ambient-toggle").addEventListener("click",()=>{const on=document.body.classList.toggle("ambient");q("#ambient-toggle").setAttribute("aria-pressed",String(on));});
  document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"&&!document.querySelector("dialog[open]")){e.preventDefault();q("#workspace-query").focus();}});
  function connection(title, value, description) {const n=node("article","connection-card");n.append(node("span","",title),node("strong","",value),node("p","",description));return n;}
  async function connections(probe=false) {
    q("#connections-refresh").disabled=true;
    try {
      const c=await request("/api/capabilities"+(probe?"?probe_model=true":""));state.caps=c;
      q("#workspace-status").textContent="Workspace ready · "+c.version;
      q("#core-model").textContent=c.agent.provider==="local"?"Local tools ready":c.agent.state==="connected"?"Model connection checked":c.agent.state==="unavailable"?"Model unavailable":"Model configured";
      q("#workspace-synthesize").disabled=c.agent.provider==="local";if(c.agent.provider==="local")q("#workspace-synthesize").checked=false;
      const cards=[connection("Music desk",c.catalog.count+" case instruments","Catalog tools and checked store policies. The inventory is a supplied snapshot."),connection("Agent engine",c.agent.state.replaceAll("_"," "),c.agent.model||"Local deterministic routing with verified tools. No neural training occurs here."),connection("KONAET checkout","Sandbox only","Session wallet, server-calculated quotes and sealed test receipts. No real money moves."),connection("Sovereign","Commitment export","An opening compatible with SocialReceiptRegistry.ko. Not submitted or finalized on a validator network."),connection("Hardware","Logical simulation",c.hardware.validation.notice),connection("Application protection","Request limits active",c.protection.max_inflight_per_process+" concurrent requests per process; bounded bodies and read time. Internet DDoS edge: not provisioned.")];
      for(const p of c.research)cards.push(connection(p.name,!p.configured?"Not configured":p.status==="not_checked"?"Ready · not checked":p.status.replaceAll("_"," "),p.checked_at?"Last attempt: "+stamp(p.checked_at):p.id==="brave"?"A provider subscription key is required for general web search.":"Public metadata API; a successful lookup will update this state."));
      q("#connection-grid").replaceChildren(...cards);
    } catch(e){q("#workspace-status").textContent="Connection unavailable";q("#connection-grid").replaceChildren(connection("Connection", "Unavailable",e.message));}
    finally{q("#connections-refresh").disabled=false;}
  }
  for(const id of ["connections-open","core-connections-button"])q("#"+id).addEventListener("click",()=>{modal("connections-dialog");connections(true);});
  q("#connections-refresh").addEventListener("click",()=>connections(true));
  function receiptControls(root,intent) {
    root.replaceChildren();
    const receipt=node("p","sandbox-receipt",(intent.status==="paid_test"?"TEST APPROVED":"TEST DECLINED")+"\n"+funds(intent.amount_cents)+" · sandbox credits\n"+(window.KonaetRuntime?"Browser-only record; no server seal":"Server seal: "+(intent.seal_verified?"verified":"not yet available"))+"\nNo money moved. No bank settlement. No stock reservation.");receipt.dataset.status=intent.status;root.append(receipt);
    const actions=node("div","sandbox-actions");
    if(intent.receipt)actions.append(button("Download test receipt ↓","button secondary",()=>{const copy={...intent};delete copy.sovereign_opening;download("konaet-test-receipt.json",JSON.stringify(copy,null,2));}));
    if(intent.sovereign_opening)actions.append(button("Export private Sovereign opening ↓","button secondary",()=>download("konaet-private-test-opening.json",JSON.stringify(intent.sovereign_opening.private_opening,null,2))));
    actions.append(button("Verify stored receipt ↗","button secondary",async()=>{try{const fresh=await request("/api/sandbox/intents/"+intent.id);receiptControls(root,fresh);}catch(e){root.append(node("p","inline-error",e.message));}}));root.append(actions);
    root.append(node("p","mission-boundary","The server seal is not an independent bank certificate. Keep the Sovereign opening private; no network finalization has occurred."));
  }
  async function wallet(topup=false) {
    q("#wallet-topup").disabled=true;error("wallet-error","");
    try{
      const w=topup?await post("/api/sandbox/wallet/topup",{}):await request("/api/sandbox/wallet");
      q("#wallet-balance").textContent=funds(w.balance_cents)+" test";q("#wallet-address").textContent=w.address;
      const root=q("#wallet-transactions");root.replaceChildren();
      if(!w.transactions.length)root.append(node("p","mission-boundary","Your test transactions will appear here after preparing a quote and running a test payment."));
      for(const t of w.transactions){const row=node("div","wallet-transaction"),copy=node("div","",funds(t.amount_cents)+" · "+t.status.replaceAll("_"," "));copy.append(node("small","",stamp(t.created)));row.append(copy);if(t.status!=="pending_test")row.append(button("Inspect ↗","",async()=>{try{const r=await request("/api/sandbox/intents/"+t.id);let detail=root.querySelector(".wallet-receipt-detail");if(!detail){detail=node("div","wallet-receipt-detail");root.append(detail);}receiptControls(detail,r);}catch(e){error("wallet-error",e.message);}}));root.append(row);}
    }catch(e){error("wallet-error",e.message);}finally{q("#wallet-topup").disabled=false;}
  }
  q("#wallet-open").addEventListener("click",()=>{modal("wallet-dialog");wallet();});q("#wallet-topup").addEventListener("click",()=>wallet(true));
  document.addEventListener("konaet:quote",e=>{
    const quote=e.detail,root=q("#checkout-content"),panel=node("section","sandbox-test-panel"),actions=node("div","sandbox-actions"),result=node("div");let busy=false;
    const key="intent_"+crypto.randomUUID().replaceAll("-","");
    panel.append(node("h3","","Try the KONAET checkout flow"),node("p","","Only the workspace that created this quote can use its sandbox wallet. Choose a test outcome; this never sends a bank payment."));
    async function confirm(decision){if(busy)return;busy=true;for(const b of actions.children)b.disabled=true;result.textContent="Checking the quote and creating a test transaction…";try{const i=await post("/api/sandbox/intents",{checkout_id:quote.id,request_key:key});const r=await post("/api/sandbox/intents/"+i.id+"/confirm",{decision});receiptControls(result,r);actions.remove();}catch(err){result.replaceChildren(node("p","inline-error",err.message));for(const b of actions.children)b.disabled=false;}finally{busy=false;}}
    actions.append(button("Approve test payment ↗","button primary",()=>confirm("approve")),button("Decline test payment","button secondary",()=>confirm("decline")));panel.append(actions,result);root.append(panel);
  });
  const svgNode=(tag,attrs)=>{const n=document.createElementNS("http://www.w3.org/2000/svg",tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));return n;};
  async function hardware(){q("#hardware-run").disabled=true;error("hardware-error","");try{const r=await post("/api/hardware/simulate",{cycles:96,capacity:Number(q("#hardware-capacity").value),burst:Number(q("#hardware-burst").value),refill_every:Number(q("#hardware-refill").value)});q("#hardware-stats").replaceChildren(node("strong","",r.admitted+" admitted"),node("strong","",r.rejected+" rejected"),node("span","",r.cycles+" logical cycles · no physical device"));const svg=svgNode("svg",{viewBox:"0 0 660 185",role:"img","aria-label":"Credits remaining over 96 logical cycles; amber marks are rejected requests"});for(let n=0;n<5;n++)svg.append(svgNode("line",{x1:20,y1:20+n*32,x2:640,y2:20+n*32,class:"chart-grid"}));for(const t of r.trace)if(t.rejected)svg.append(svgNode("rect",{x:20+t.cycle/95*620,y:155,width:4,height:7,class:"chart-reject"}));svg.append(svgNode("polyline",{points:r.trace.map(t=>(20+t.cycle/95*620)+","+(148-t.credits/r.capacity*125)).join(" "),class:"chart-credits"}));const label=svgNode("text",{x:20,y:182,class:"chart-label"});label.textContent="GREEN / CREDITS REMAINING     AMBER / REJECTED REQUEST";svg.append(label);q("#hardware-chart").replaceChildren(svg);q("#hardware-validation").textContent=r.notice+" "+(r.validation.status==="source_matched_record"?r.validation.vectors+" RTL vectors matched the Python reference. ":"")+r.validation.notice;}catch(e){error("hardware-error",e.message);}finally{q("#hardware-run").disabled=false;}}
  q("#hardware-open").addEventListener("click",()=>{modal("hardware-dialog");hardware();});q("#hardware-form").addEventListener("submit",e=>{e.preventDefault();hardware();});
  if(document.documentElement.dataset.konaetReady)connections(true);else document.addEventListener("konaet:ready",()=>connections(true),{once:true});
})();
