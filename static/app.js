// ================= Book Tracker frontend =================
let BOOKS = [];
let editingId = null;
const lib = { q: "", status: "all", format: "all", sort: "added_desc", layout: "grid" };
const COVERS = ["#4f52c9","#2f9e73","#c9704f","#8a4fc9","#4f8ac9","#c94f8a","#c9a24f","#4fb0a0","#7a7f8c","#b0574f"];

const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));

function coverColor(t){ let h=0; for(const c of t) h=(h*31+c.charCodeAt(0))>>>0; return COVERS[h%COVERS.length]; }
function initials(t){ return (t.trim().split(/\s+/).slice(0,2).map(w=>w[0]).join("")||"?").toUpperCase(); }
function shade(hex,pct){ const n=parseInt(hex.slice(1),16);
  const r=Math.round(((n>>16)&255)*(1-pct)), g=Math.round(((n>>8)&255)*(1-pct)), b=Math.round((n&255)*(1-pct));
  return "#"+((1<<24)+(r<<16)+(g<<8)+b).toString(16).slice(1); }
function coverHTML(b){ const c=coverColor(b.title);
  return `<div class="cover" style="background:linear-gradient(140deg,${c},${shade(c,.32)})">
    <span class="spine"></span><span class="wm">${initials(b.title)}</span>
    <span class="fmt">${esc(b.format)}</span><span class="jacket">${esc(b.title)}</span></div>`; }
function starsHTML(r){ let h=""; for(let i=1;i<=5;i++) h+=`<span class="${i<=r?'':'off'}">★</span>`; return `<span class="stars">${h}</span>`; }

async function api(path, opts){
  const r = await fetch(path, { headers:{ "Content-Type":"application/json" }, ...opts });
  const data = await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(data.error || "Request failed");
  return data;
}

function toast(msg){
  const t=$("#toast"); t.textContent=msg; t.classList.remove("hidden");
  clearTimeout(t._h); t._h=setTimeout(()=>t.classList.add("hidden"),2200);
}

// ---------- load + routing ----------
async function loadBooks(){ BOOKS = await api("/api/books"); renderSideFoot(); }

function renderSideFoot(){
  const total=BOOKS.length, read=BOOKS.filter(b=>b.status==="read").length;
  $("#sideFoot").innerHTML =
    `<b>${total}</b> books in library<br><b style="color:var(--green)">${read}</b> read &nbsp;·&nbsp; <b style="color:var(--accent)">${total-read}</b> to read`;
}

const TITLES = {
  dashboard:["Dashboard","A snapshot of your reading life"],
  library:["Library","Browse and manage every book you own"],
  stats:["Statistics","Trends and insights across your collection"],
};
function switchView(v){
  document.querySelectorAll(".nav-item").forEach(n=>n.classList.toggle("active",n.dataset.view===v));
  document.querySelectorAll(".view").forEach(s=>s.classList.add("hidden"));
  $("#view-"+v).classList.remove("hidden");
  $("#viewTitle").textContent=TITLES[v][0];
  $("#viewSub").textContent=TITLES[v][1];
  if(v==="dashboard") renderDashboard();
  if(v==="library") renderLibrary();
  if(v==="stats") renderStats();
}

// ---------- dashboard ----------
function renderDashboard(){
  const el=$("#view-dashboard");
  if(!BOOKS.length){ el.innerHTML=emptyState("Your library is empty","Add your first book to get started."); return; }
  const total=BOOKS.length, read=BOOKS.filter(b=>b.status==="read").length, tbr=total-read;
  const pct=Math.round(read/total*100);
  const rated=BOOKS.filter(b=>b.rating>0);
  const avg=rated.length?(rated.reduce((s,b)=>s+b.rating,0)/rated.length):0;

  const recent=[...BOOKS].sort((a,b)=>(b.date_added||"").localeCompare(a.date_added||"")||b.id-a.id).slice(0,6);
  const topAuthors=countTop(BOOKS.map(b=>b.author),5);

  el.innerHTML = `
    <div class="stat-row">
      ${stat("Total books",total,"")}
      ${stat("Read",read,pct+"% complete")}
      ${stat("To be read",tbr,"")}
      ${stat("Avg rating",avg?avg.toFixed(1):"—",rated.length?rated.length+" rated":"no ratings yet")}
    </div>
    <div class="cols">
      <div class="panel">
        <h3>Recently added</h3>
        ${recent.map(b=>`<div class="mini" data-id="${b.id}">
          <div><div class="t">${esc(b.title)}</div><div class="a">${esc(b.author)}</div></div>
          <span class="pill ${b.status==='read'?'pill-read':'pill-unread'}">${b.status==='read'?'Read':'To read'}</span>
        </div>`).join("")}
      </div>
      <div class="panel donut-wrap">
        <h3 style="align-self:flex-start">Reading progress</h3>
        ${donut(pct)}
        <div class="legend">
          <span><i style="background:var(--accent)"></i>Read ${read}</span>
          <span><i style="background:var(--track)"></i>To read ${tbr}</span>
        </div>
      </div>
    </div>
    <div class="panel" style="margin-top:1.3rem">
      <h3>Top authors</h3>
      ${barList(topAuthors)}
    </div>`;
  el.querySelectorAll(".mini").forEach(m=>m.onclick=()=>openDrawer(+m.dataset.id));
}

// ---------- library ----------
function renderLibrary(){
  const el=$("#view-library");
  el.innerHTML = `
    <div class="toolbar">
      <div class="search"><input id="q" placeholder="Search title, author or series…" value="${esc(lib.q)}"></div>
      <div class="chips" id="statusChips">
        ${["all","unread","read"].map(s=>`<button class="chip ${lib.status===s?'active':''}" data-s="${s}">${s==='all'?'All':s==='read'?'Read':'To read'}</button>`).join("")}
      </div>
      <select id="fmt"></select>
      <select id="sort">
        <option value="added_desc">Recently added</option>
        <option value="title">Title A–Z</option>
        <option value="author">Author A–Z</option>
        <option value="rating">Highest rated</option>
      </select>
      <div class="view-toggle">
        <button data-l="grid" class="${lib.layout==='grid'?'active':''}">▦</button>
        <button data-l="table" class="${lib.layout==='table'?'active':''}">▤</button>
      </div>
    </div>
    <div class="count" id="count"></div>
    <div id="results"></div>`;

  const formats=["all",...Array.from(new Set(BOOKS.map(b=>b.format))).sort()];
  $("#fmt").innerHTML=formats.map(f=>`<option value="${esc(f)}" ${lib.format===f?'selected':''}>${f==='all'?'All formats':esc(f)}</option>`).join("");
  $("#sort").value=lib.sort;

  $("#q").oninput=e=>{ lib.q=e.target.value; drawResults(); };
  $("#fmt").onchange=e=>{ lib.format=e.target.value; drawResults(); };
  $("#sort").onchange=e=>{ lib.sort=e.target.value; drawResults(); };
  $("#statusChips").querySelectorAll(".chip").forEach(c=>c.onclick=()=>{
    lib.status=c.dataset.s; $("#statusChips").querySelectorAll(".chip").forEach(x=>x.classList.toggle("active",x===c)); drawResults();
  });
  el.querySelectorAll(".view-toggle button").forEach(b=>b.onclick=()=>{
    lib.layout=b.dataset.l; el.querySelectorAll(".view-toggle button").forEach(x=>x.classList.toggle("active",x===b)); drawResults();
  });
  drawResults();
}

function filtered(){
  let list=[...BOOKS];
  const q=lib.q.trim().toLowerCase();
  if(q) list=list.filter(b=>(b.title+" "+b.author+" "+b.series).toLowerCase().includes(q));
  if(lib.status!=="all") list=list.filter(b=>b.status===lib.status);
  if(lib.format!=="all") list=list.filter(b=>b.format===lib.format);
  const s=lib.sort;
  list.sort((a,b)=>
    s==="title"?a.title.localeCompare(b.title):
    s==="author"?a.author.localeCompare(b.author)||a.title.localeCompare(b.title):
    s==="rating"?(b.rating-a.rating)||a.title.localeCompare(b.title):
    (b.date_added||"").localeCompare(a.date_added||"")||b.id-a.id);
  return list;
}

function drawResults(){
  const list=filtered();
  $("#count").textContent=`Showing ${list.length} of ${BOOKS.length} books`;
  const box=$("#results");
  if(!list.length){ box.innerHTML=emptyState("No matches","Try adjusting your search or filters."); return; }
  box.innerHTML = lib.layout==="grid"
    ? `<div class="grid">${list.map(cardHTML).join("")}</div>`
    : tableHTML(list);
  box.querySelectorAll("[data-id]").forEach(n=>n.onclick=()=>openDrawer(+n.dataset.id));
}

function cardHTML(b){
  return `<div class="card" data-id="${b.id}">
    ${coverHTML(b)}
    <div class="card-body">
      <div class="a">${esc(b.author)}</div>
      <div class="card-foot">
        <span class="pill ${b.status==='read'?'pill-read':'pill-unread'}">${b.status==='read'?'Read':'To read'}</span>
        ${b.rating?starsHTML(b.rating):''}
      </div>
    </div></div>`;
}

function tableHTML(list){
  return `<table class="tbl"><thead><tr>
    <th>Title</th><th>Author</th><th>Series</th><th>Format</th><th>Status</th><th>Rating</th>
    </tr></thead><tbody>${list.map(b=>`<tr data-id="${b.id}">
      <td><b>${esc(b.title)}</b></td><td>${esc(b.author)}</td>
      <td>${esc(b.series)||'—'}</td><td>${esc(b.format)}</td>
      <td><span class="pill ${b.status==='read'?'pill-read':'pill-unread'}">${b.status==='read'?'Read':'To read'}</span></td>
      <td>${b.rating?starsHTML(b.rating):'<span style="color:var(--muted)">—</span>'}</td>
    </tr>`).join("")}</tbody></table>`;
}

// ---------- stats ----------
function renderStats(){
  const el=$("#view-stats");
  if(!BOOKS.length){ el.innerHTML=emptyState("Nothing to chart yet","Add books to see statistics."); return; }
  const byFormat=countTop(BOOKS.map(b=>b.format),8);
  const topAuthors=countTop(BOOKS.map(b=>b.author),10);
  const read=BOOKS.filter(b=>b.status==="read").length, pct=Math.round(read/BOOKS.length*100);
  const dist=[5,4,3,2,1].map(r=>[r+"★",BOOKS.filter(b=>b.rating===r).length]);

  el.innerHTML=`
    <div class="cols-2">
      <div class="panel"><h3>By format</h3>${barList(byFormat)}</div>
      <div class="panel donut-wrap"><h3 style="align-self:flex-start">Completion</h3>
        ${donut(pct)}<div class="legend"><span><i style="background:var(--accent)"></i>Read ${read}</span>
        <span><i style="background:var(--track)"></i>To read ${BOOKS.length-read}</span></div></div>
    </div>
    <div class="panel" style="margin-top:1.3rem"><h3>Most collected authors</h3>${barList(topAuthors)}</div>
    <div class="panel" style="margin-top:1.3rem"><h3>Rating distribution</h3>${barList(dist)}</div>`;
}

// ---------- drawer (edit) ----------
function openDrawer(id){
  const b=BOOKS.find(x=>x.id===id); if(!b) return;
  editingId=id;
  const c=coverColor(b.title);
  $("#drawer").innerHTML=`
    <div style="display:flex;justify-content:flex-end"><button class="icon-btn" id="drawerClose">✕</button></div>
    <div class="d-cover" style="background:linear-gradient(140deg,${c},${shade(c,.32)})"><span class="spine"></span>${initials(b.title)}</div>
    <h2>${esc(b.title)}</h2>
    <div class="by">${esc(b.author)}${b.series?` · ${esc(b.series)}${b.book_number?` #${esc(b.book_number)}`:''}`:''}</div>

    <div class="field"><label>Status</label>
      <div class="seg" id="segStatus">
        <button data-v="unread" class="${b.status==='unread'?'on':''}">To read</button>
        <button data-v="read" class="${b.status==='read'?'on':''}">Read</button>
      </div>
    </div>
    <div class="field"><label>Format</label>
      <select id="dFormat">${["Kindle","Physical","PDF","Audio","Other"].map(f=>`<option ${b.format===f?'selected':''}>${f}</option>`).join("")}</select>
    </div>
    <div class="field"><label>Your rating</label>
      <div class="rate" id="rate">${[1,2,3,4,5].map(i=>`<span class="s ${i<=b.rating?'on':''}" data-r="${i}">★</span>`).join("")}</div>
    </div>
    <div class="field"><label>Review</label>
      <textarea id="dReview" placeholder="Your thoughts…">${esc(b.review)}</textarea>
    </div>
    <div class="drawer-actions">
      <button class="btn btn-danger" id="dDelete">Delete</button>
      <button class="btn btn-primary" id="dSave">Save changes</button>
    </div>`;

  let draft={ status:b.status, format:b.format, rating:b.rating };
  $("#drawer").classList.remove("hidden"); $("#scrim").classList.remove("hidden");
  $("#drawerClose").onclick=closeDrawer; $("#scrim").onclick=closeDrawer;
  $("#segStatus").querySelectorAll("button").forEach(btn=>btn.onclick=()=>{
    draft.status=btn.dataset.v; $("#segStatus").querySelectorAll("button").forEach(x=>x.classList.toggle("on",x===btn));
  });
  $("#dFormat").onchange=e=>draft.format=e.target.value;
  $("#rate").querySelectorAll(".s").forEach(s=>s.onclick=()=>{
    draft.rating=+s.dataset.r;
    $("#rate").querySelectorAll(".s").forEach(x=>x.classList.toggle("on",+x.dataset.r<=draft.rating));
  });
  $("#dSave").onclick=async()=>{
    try{
      await api(`/api/books/${id}`,{ method:"PUT", body:JSON.stringify({
        status:draft.status, format:draft.format, rating:draft.rating, review:$("#dReview").value }) });
      await loadBooks(); closeDrawer(); refreshCurrent(); toast("Saved");
    }catch(e){ toast(e.message); }
  };
  $("#dDelete").onclick=async()=>{
    if(!confirm(`Remove "${b.title}" from your library?`)) return;
    try{ await api(`/api/books/${id}`,{ method:"DELETE" }); await loadBooks(); closeDrawer(); refreshCurrent(); toast("Book removed"); }
    catch(e){ toast(e.message); }
  };
}
function closeDrawer(){ editingId=null; $("#drawer").classList.add("hidden"); $("#scrim").classList.add("hidden"); }

// ---------- add modal ----------
function openModal(){ $("#modal").classList.remove("hidden"); $("#addForm").reset(); }
function closeModal(){ $("#modal").classList.add("hidden"); }
async function submitAdd(e){
  e.preventDefault();
  const f=e.target;
  try{
    await api("/api/books",{ method:"POST", body:JSON.stringify({
      title:f.title.value, author:f.author.value, series:f.series.value,
      book_number:f.book_number.value, format:f.format.value,
      status:f.read.checked?"read":"unread" }) });
    await loadBooks(); closeModal(); refreshCurrent(); toast("Book added");
  }catch(err){ toast(err.message); }
}

// ---------- helpers ----------
function stat(l,v,m){ return `<div class="stat"><div class="lab">${l}</div><div class="val">${v}</div><div class="meta">${m}</div></div>`; }
function donut(pct){
  return `<div class="donut" style="background:conic-gradient(var(--accent) 0 ${pct}%, var(--track) ${pct}% 100%)">
    <div class="center"><b>${pct}%</b><span>complete</span></div></div>`;
}
function countTop(arr,n){
  const m={}; arr.forEach(v=>{ v=v||"Unknown"; m[v]=(m[v]||0)+1; });
  return Object.entries(m).sort((a,b)=>b[1]-a[1]).slice(0,n);
}
function barList(pairs){
  const max=Math.max(1,...pairs.map(p=>p[1]));
  return pairs.map(([name,val])=>`<div class="bar-row">
    <span class="name" title="${esc(name)}">${esc(name)}</span>
    <span class="bar-track"><span class="bar-fill" style="width:${val/max*100}%"></span></span>
    <span class="num">${val}</span></div>`).join("") || `<div class="count">No data</div>`;
}
function emptyState(t,s){ return `<div class="empty"><div class="big">📚</div><h3>${t}</h3><p class="sub">${s}</p></div>`; }
function refreshCurrent(){
  const v=document.querySelector(".nav-item.active").dataset.view;
  if(v==="dashboard") renderDashboard(); else if(v==="library") drawResults(); else renderStats();
}

// ---------- init ----------
document.querySelectorAll(".nav-item").forEach(n=>n.onclick=()=>switchView(n.dataset.view));
$("#addBtn").onclick=openModal;
$("#modalClose").onclick=closeModal;
$("#modalCancel").onclick=closeModal;
$("#modal").onclick=e=>{ if(e.target.id==="modal") closeModal(); };
$("#addForm").onsubmit=submitAdd;
document.addEventListener("keydown",e=>{ if(e.key==="Escape"){ closeDrawer(); closeModal(); } });

(async function(){ await loadBooks(); switchView("dashboard"); })();
