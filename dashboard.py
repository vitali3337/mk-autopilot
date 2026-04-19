"""МК-ГРУПП Autopilot — Web Dashboard (aiohttp)"""
import os, json, asyncio
from datetime import datetime
from aiohttp import web
from engine import load_stats, WEEKLY_PLAN, BUSINESS

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>МК-ГРУПП | Autopilot</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#07070c;--s:#0f0f17;--s2:#161620;--b:#222230;--a:#f0a500;--a2:#ff5c35;--a3:#00e5b0;--t:#eeeef8;--m:#5a5a72;--ok:#22c55e;--purple:#a855f7}
body{background:var(--bg);color:var(--t);font-family:'Montserrat',sans-serif;min-height:100vh;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(240,165,0,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(240,165,0,.02) 1px,transparent 1px);background-size:44px 44px;pointer-events:none}
/* HEADER */
header{position:sticky;top:0;z-index:100;background:rgba(7,7,12,.95);backdrop-filter:blur(20px);border-bottom:1px solid var(--b);height:62px;display:flex;align-items:center;justify-content:space-between;padding:0 32px}
.logo{display:flex;align-items:center;gap:12px}
.logo-box{width:36px;height:36px;background:var(--a);border-radius:9px;display:flex;align-items:center;justify-content:center;font-family:'Bebas Neue';font-size:17px;color:#000;letter-spacing:0}
.logo-name{font-family:'Bebas Neue';font-size:21px;letter-spacing:2px}
.logo-sub{font-size:9px;color:var(--a);letter-spacing:3px;font-weight:700;margin-top:-2px}
.hdr-right{display:flex;align-items:center;gap:12px}
.live-badge{display:flex;align-items:center;gap:7px;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);border-radius:20px;padding:6px 14px;font-size:11px;color:var(--ok);font-weight:700;letter-spacing:1px}
.dot{width:6px;height:6px;background:var(--ok);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.5)}}
.uptime{font-family:'JetBrains Mono';font-size:11px;color:var(--m)}
/* MAIN */
main{max-width:1280px;margin:0 auto;padding:30px 28px 80px;position:relative;z-index:1}
/* STATS CARDS */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:30px}
.sc{background:var(--s);border:1px solid var(--b);border-radius:16px;padding:20px;position:relative;overflow:hidden;transition:border-color .2s}
.sc:hover{border-color:rgba(240,165,0,.25)}
.sc::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;border-radius:0 0 16px 16px}
.sc.a::after{background:linear-gradient(90deg,var(--a),#ffcc44)}
.sc.b::after{background:linear-gradient(90deg,var(--a2),#ff9060)}
.sc.c::after{background:linear-gradient(90deg,var(--a3),#00ffcc)}
.sc.d::after{background:linear-gradient(90deg,var(--purple),#d946ef)}
.sc-label{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--m);margin-bottom:8px}
.sc-val{font-family:'Bebas Neue';font-size:48px;line-height:1;letter-spacing:1px}
.sc.a .sc-val{color:var(--a)}.sc.b .sc-val{color:var(--a2)}.sc.c .sc-val{color:var(--a3)}.sc.d .sc-val{color:var(--purple)}
.sc-sub{font-size:10px;color:var(--m);margin-top:4px}
.sc-icon{position:absolute;right:18px;top:18px;font-size:28px;opacity:.15}
/* SECTION HEAD */
.sh{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.sh-title{font-family:'Bebas Neue';font-size:27px;letter-spacing:2px}
.sh-badge{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--a);background:rgba(240,165,0,.08);border:1px solid rgba(240,165,0,.18);border-radius:4px;padding:3px 8px}
/* GRID */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}
.grid-3{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:24px}
/* CARDS */
.card{background:var(--s);border:1px solid var(--b);border-radius:16px;overflow:hidden}
.card-hd{background:var(--s2);border-bottom:1px solid var(--b);padding:13px 18px;font-size:11px;font-weight:700;letter-spacing:.5px;color:var(--m);display:flex;justify-content:space-between;align-items:center}
.card-hd span:first-child{color:var(--t)}
.card-bd{padding:18px}
/* SCHEDULE TABLE */
.sch-table{width:100%;border-collapse:collapse}
.sch-table th{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--m);padding:0 0 10px;text-align:left}
.sch-table td{padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);vertical-align:middle}
.sch-table tr:last-child td{border:none}
.sch-day{font-family:'Bebas Neue';font-size:17px;color:var(--a);width:36px}
.sch-time{font-family:'JetBrains Mono';font-size:12px;color:var(--t);width:54px}
.sch-topic{font-size:12px;font-weight:600}
.sch-style{font-size:9px;padding:2px 8px;border-radius:4px;font-weight:700;letter-spacing:.5px;display:inline-block}
.st-sell{background:rgba(240,165,0,.1);color:var(--a)}
.st-emot{background:rgba(255,92,53,.1);color:var(--a2)}
.st-edu{background:rgba(0,229,176,.1);color:var(--a3)}
.st-urg{background:rgba(168,85,247,.1);color:var(--purple)}
/* HISTORY */
.hist-list{display:flex;flex-direction:column;gap:7px;max-height:340px;overflow-y:auto}
.hist-item{display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--s2);border-radius:9px;border:1px solid var(--b)}
.hist-icon{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;background:rgba(240,165,0,.08)}
.hist-body{flex:1;min-width:0}
.hist-title{font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hist-meta{font-size:10px;color:var(--m);font-family:'JetBrains Mono';margin-top:2px}
.hist-ok{font-size:10px;font-weight:700}
.ok-yes{color:var(--ok)}.ok-no{color:var(--a2)}
/* ENV */
.env-list{display:flex;flex-direction:column;gap:7px}
.env-row{display:flex;align-items:center;justify-content:space-between;padding:9px 13px;background:var(--s2);border-radius:8px;border:1px solid var(--b)}
.env-key{font-family:'JetBrains Mono';font-size:11px;color:var(--m)}
.env-val{font-size:10px;font-weight:700;padding:2px 9px;border-radius:4px}
.env-set{background:rgba(34,197,94,.1);color:var(--ok)}.env-no{background:rgba(255,92,53,.1);color:var(--a2)}
/* LOG */
.log-box{font-family:'JetBrains Mono';font-size:11px;line-height:1.85;color:var(--m);max-height:360px;overflow-y:auto;padding:2px 0;white-space:pre-wrap;word-break:break-all}
.log-ok{color:#4ade80}.log-err{color:#f87171}.log-info{color:var(--a)}.log-warn{color:#facc15}
/* MANUAL FIRE BUTTON */
.fire-section{background:var(--s);border:1px solid var(--b);border-radius:16px;padding:22px;margin-bottom:24px}
.fire-grid{display:grid;grid-template-columns:1fr 1fr auto;gap:12px;align-items:end}
.form-label{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--m);margin-bottom:7px;display:block}
select{width:100%;background:var(--s2);border:1px solid var(--b);border-radius:9px;padding:11px 13px;color:var(--t);font-family:'Montserrat';font-size:13px;font-weight:500;outline:none;cursor:pointer;-webkit-appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%235a5a72' stroke-width='1.5' fill='none'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 13px center;padding-right:34px;transition:border-color .2s}
select:focus{border-color:var(--a)}
.btn{border:none;border-radius:10px;padding:13px 22px;font-family:'Montserrat';font-size:13px;font-weight:700;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:7px;white-space:nowrap}
.btn-primary{background:var(--a);color:#000;box-shadow:0 4px 18px rgba(240,165,0,.22)}
.btn-primary:hover:not(:disabled){background:#ffb800;transform:translateY(-1px)}
.btn-primary:disabled{opacity:.5;cursor:not-allowed}
/* TOAST */
.toast{position:fixed;bottom:28px;right:28px;background:var(--s);border:1px solid var(--ok);border-radius:12px;padding:13px 20px;font-size:13px;font-weight:600;color:var(--ok);display:flex;align-items:center;gap:8px;z-index:999;transform:translateY(80px);opacity:0;transition:all .35s cubic-bezier(.34,1.56,.64,1);box-shadow:0 8px 30px rgba(0,0,0,.4)}
.toast.show{transform:translateY(0);opacity:1}
/* SCROLLBAR */
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--b);border-radius:2px}
@media(max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}.grid-2,.grid-3,.fire-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="logo-box">МК</div>
    <div>
      <div class="logo-name">МК-ГРУПП AUTOPILOT</div>
      <div class="logo-sub">AI MARKETING ENGINE</div>
    </div>
  </div>
  <div class="hdr-right">
    <span class="uptime" id="uptime-el">uptime: загрузка...</span>
    <div class="live-badge"><div class="dot"></div>РАБОТАЕТ</div>
  </div>
</header>

<main>
  <!-- STATS -->
  <div class="stats">
    <div class="sc a">
      <div class="sc-icon">📢</div>
      <div class="sc-label">Постов опубликовано</div>
      <div class="sc-val" id="st-posts">—</div>
      <div class="sc-sub">всего за всё время</div>
    </div>
    <div class="sc b">
      <div class="sc-icon">🎯</div>
      <div class="sc-label">Лидов собрано</div>
      <div class="sc-val" id="st-leads">—</div>
      <div class="sc-sub">в Google Sheets</div>
    </div>
    <div class="sc c">
      <div class="sc-icon">✅</div>
      <div class="sc-label">Последний пост</div>
      <div class="sc-val" id="st-last" style="font-size:20px;padding-top:10px">—</div>
      <div class="sc-sub" id="st-last-sub">нет данных</div>
    </div>
    <div class="sc d">
      <div class="sc-icon">⚡</div>
      <div class="sc-label">Ошибок</div>
      <div class="sc-val" id="st-errors">—</div>
      <div class="sc-sub">за всё время</div>
    </div>
  </div>

  <!-- MANUAL FIRE -->
  <div class="sh"><div class="sh-title">РУЧНОЙ ЗАПУСК</div><div class="sh-badge">FORCE PUBLISH</div></div>
  <div class="fire-section" style="margin-bottom:28px">
    <div class="fire-grid">
      <div>
        <span class="form-label">Тема поста</span>
        <select id="f-topic">
          <option value="windows">🪟 Металлопластиковые окна</option>
          <option value="doors">🚪 Входные двери</option>
          <option value="interior">🏠 Межкомнатные двери</option>
          <option value="balcony">🌿 Балкон / остекление</option>
          <option value="promo">🔥 Акция / Скидка</option>
          <option value="review">⭐ Отзыв клиента</option>
          <option value="before_after">✨ До и После</option>
          <option value="faq">❓ FAQ</option>
          <option value="seasonal">❄️ Сезонный</option>
        </select>
      </div>
      <div>
        <span class="form-label">Стиль</span>
        <select id="f-style">
          <option value="selling">💰 Продающий</option>
          <option value="emotional">❤️ Эмоциональный</option>
          <option value="educational">📚 Образовательный</option>
          <option value="urgent">⚡ Срочность</option>
        </select>
      </div>
      <button class="btn btn-primary" id="fire-btn" onclick="firePost()">
        <span id="fire-icon">🚀</span> <span id="fire-text">ОПУБЛИКОВАТЬ СЕЙЧАС</span>
      </button>
    </div>
  </div>

  <!-- SCHEDULE + ENV -->
  <div class="grid-3">
    <div class="card">
      <div class="card-hd"><span>📅 Расписание публикаций</span><span>10 постов / неделю</span></div>
      <div class="card-bd">
        <table class="sch-table">
          <thead><tr>
            <th>ДЕНЬ</th><th>ВРЕМЯ</th><th>ТЕМА</th><th>СТИЛЬ</th>
          </tr></thead>
          <tbody id="sch-body"></tbody>
        </table>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:16px">
      <div class="card" style="flex:1">
        <div class="card-hd"><span>⚙️ ENV переменные</span><span>Railway</span></div>
        <div class="card-bd">
          <div class="env-list" id="env-list">Загрузка...</div>
        </div>
      </div>
    </div>
  </div>

  <!-- HISTORY + LOGS -->
  <div class="grid-2">
    <div class="card">
      <div class="card-hd"><span>📋 История публикаций</span><span id="hist-count" style="color:var(--a)"></span></div>
      <div class="card-bd">
        <div class="hist-list" id="hist-list"><div style="color:var(--m);font-size:12px;padding:8px">Нет данных</div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-hd"><span>🖥️ Логи (autopilot.log)</span><span id="log-time" style="color:var(--m);font-size:10px;font-family:'JetBrains Mono'"></span></div>
      <div class="card-bd">
        <div class="log-box" id="log-box">Загрузка...</div>
      </div>
    </div>
  </div>

</main>

<div class="toast" id="toast"></div>

<script>
const SCHEDULE = [
  {day:'ПН',time:'10:00',topic:'Окна',style:'emotional'},
  {day:'ПН',time:'18:00',topic:'Акция',style:'urgent'},
  {day:'ВТ',time:'11:00',topic:'До/После',style:'selling'},
  {day:'СР',time:'10:00',topic:'Отзыв',style:'emotional'},
  {day:'СР',time:'17:00',topic:'Двери',style:'selling'},
  {day:'ЧТ',time:'10:00',topic:'Акция',style:'urgent'},
  {day:'ПТ',time:'11:00',topic:'Балкон',style:'selling'},
  {day:'ПТ',time:'16:00',topic:'FAQ',style:'educational'},
  {day:'СБ',time:'11:00',topic:'Сезон',style:'emotional'},
  {day:'ВС',time:'12:00',topic:'Окна',style:'selling'},
];
const STYLE_CLASS = {selling:'st-sell',emotional:'st-emot',educational:'st-edu',urgent:'st-urg'};
const STYLE_LABEL = {selling:'ПРОДАЖ.',emotional:'ЭМОЦ.',educational:'ОБУЧЕН.',urgent:'СРОЧН.'};

document.getElementById('sch-body').innerHTML = SCHEDULE.map(s => `
  <tr>
    <td class="sch-day">${s.day}</td>
    <td class="sch-time">${s.time}</td>
    <td class="sch-topic">${s.topic}</td>
    <td><span class="sch-style ${STYLE_CLASS[s.style]||''}">${STYLE_LABEL[s.style]||s.style}</span></td>
  </tr>`).join('');

let startTime = Date.now();
setInterval(()=>{
  const s = Math.floor((Date.now()-startTime)/1000);
  const h = String(Math.floor(s/3600)).padStart(2,'0');
  const m = String(Math.floor((s%3600)/60)).padStart(2,'0');
  const sc = String(s%60).padStart(2,'0');
  document.getElementById('uptime-el').textContent = `uptime: ${h}:${m}:${sc}`;
},1000);

function toast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2800);
}

async function loadStats(){
  try{
    const d = await fetch('/api/stats').then(r=>r.json());
    document.getElementById('st-posts').textContent = d.posts_sent??0;
    document.getElementById('st-leads').textContent = d.leads??0;
    document.getElementById('st-errors').textContent = d.errors??0;
    if(d.last_post){
      const dt=new Date(d.last_post);
      document.getElementById('st-last').textContent=dt.toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'});
      document.getElementById('st-last-sub').textContent=dt.toLocaleDateString('ru-RU',{day:'2-digit',month:'short',year:'numeric'});
    }
    const hist=(d.history||[]).slice().reverse().slice(0,25);
    document.getElementById('hist-count').textContent=`${d.history?.length||0} записей`;
    document.getElementById('hist-list').innerHTML = hist.length
      ? hist.map(h=>`
        <div class="hist-item">
          <div class="hist-icon">📢</div>
          <div class="hist-body">
            <div class="hist-title">${h.topic||'пост'} · ${STYLE_LABEL[h.style]||h.style||''} ${h.preview?'— '+h.preview:''}</div>
            <div class="hist-meta">${new Date(h.time).toLocaleString('ru-RU')}</div>
          </div>
          <div class="hist-ok ${h.ok?'ok-yes':'ok-no'}">${h.ok?'✅ OK':'❌ ERR'}</div>
        </div>`).join('')
      : '<div style="color:var(--m);font-size:12px;padding:8px">История пуста</div>';
  }catch(e){console.warn(e)}
}

async function loadEnv(){
  try{
    const d = await fetch('/api/env').then(r=>r.json());
    document.getElementById('env-list').innerHTML = Object.entries(d).map(([k,v])=>`
      <div class="env-row">
        <span class="env-key">${k}</span>
        <span class="env-val ${v?'env-set':'env-no'}">${v?'✓ SET':'✗ NOT SET'}</span>
      </div>`).join('');
  }catch(e){}
}

async function loadLogs(){
  try{
    const text = await fetch('/api/logs').then(r=>r.text());
    const box = document.getElementById('log-box');
    box.innerHTML = text.split('\n').map(l=>{
      if(l.includes('✅')||l.includes('INFO'))return`<span class="log-ok">${l}</span>`;
      if(l.includes('❌')||l.includes('ERROR'))return`<span class="log-err">${l}</span>`;
      if(l.includes('WARNING')||l.includes('⚠️'))return`<span class="log-warn">${l}</span>`;
      if(l.includes('🚀')||l.includes('📅'))return`<span class="log-info">${l}</span>`;
      return l;
    }).join('\n');
    box.scrollTop = box.scrollHeight;
    document.getElementById('log-time').textContent = new Date().toLocaleTimeString('ru-RU');
  }catch(e){}
}

async function firePost(){
  const btn = document.getElementById('fire-btn');
  const icon = document.getElementById('fire-icon');
  const txt  = document.getElementById('fire-text');
  btn.disabled=true; icon.textContent='⏳'; txt.textContent='ГЕНЕРИРУЮ...';
  try{
    const topic = document.getElementById('f-topic').value;
    const style = document.getElementById('f-style').value;
    const r = await fetch('/api/fire',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic,style})});
    const d = await r.json();
    if(d.ok){
      toast('✅ Пост опубликован в Telegram!');
      setTimeout(loadStats,2000);
    } else {
      toast('❌ Ошибка: '+d.error);
    }
  }catch(e){toast('❌ '+e.message)}
  finally{btn.disabled=false;icon.textContent='🚀';txt.textContent='ОПУБЛИКОВАТЬ СЕЙЧАС'}
}

function refresh(){ loadStats(); loadEnv(); loadLogs(); }
refresh();
setInterval(refresh, 20000);
</script>
</body>
</html>"""

async def handle_index(req):
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")

async def handle_stats(req):
    return web.json_response(load_stats())

async def handle_env(req):
    keys = ["ANTHROPIC_API_KEY","TELEGRAM_BOT_TOKEN","TELEGRAM_CHANNEL_ID",
            "SHEETS_WEBHOOK_URL","LEAD_NOTIFY_CHAT_ID"]
    return web.json_response({k: bool(os.getenv(k)) for k in keys})

async def handle_logs(req):
    try:
        with open("autopilot.log", encoding="utf-8") as f:
            lines = f.readlines()
        return web.Response(text="".join(lines[-200:]))
    except Exception:
        return web.Response(text="Лог-файл пуст.")

async def handle_fire(req):
    try:
        data  = await req.json()
        topic = data.get("topic","windows")
        style = data.get("style","selling")
        from engine import generate_post, publish_telegram, STATS, save_stats
        from datetime import datetime
        post = await generate_post(topic, style)
        ok   = await publish_telegram(post)
        STATS["posts_sent" if ok else "errors"] += 1
        STATS["last_post"] = datetime.now().isoformat()
        STATS.setdefault("history",[]).append({
            "time":datetime.now().isoformat(),"topic":topic,"style":style,
            "preview":post.get("preview_text",""),"ok":ok
        })
        save_stats(STATS)
        return web.json_response({"ok":ok,"preview":post.get("preview_text","")})
    except Exception as e:
        return web.json_response({"ok":False,"error":str(e)}, status=500)

def create_app():
    app = web.Application()
    app.router.add_get("/",           handle_index)
    app.router.add_get("/api/stats",  handle_stats)
    app.router.add_get("/api/env",    handle_env)
    app.router.add_get("/api/logs",   handle_logs)
    app.router.add_post("/api/fire",  handle_fire)
    return app
