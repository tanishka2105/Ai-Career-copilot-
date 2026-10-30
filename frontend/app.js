const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const S={get:(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}},set:(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch{}}};
let st=Object.assign({chats:[],cur:{},bm:[],plan:{},an:[],docs:[],resume:'',match:null,skills:[],analyzed:false,answers:0,log:[]},S.get('st',{}));
let P=S.get('prof',{}),CF=Object.assign({theme:'dark',size:'15',round:'Mixed',level:'Standard',voice:'female',rate:'1',read:'off',lang:'en-US'},S.get('cfg',{}));
const base='';let tok=S.get('tok','');
let lastSync={},syncT={};
function sync(key,val){if(!tok)return;clearTimeout(syncT[key]);syncT[key]=setTimeout(()=>{const j=JSON.stringify(val);if(lastSync[key]===j)return;lastSync[key]=j;api('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:j.length?JSON.stringify({key,value:val}):''}).catch(()=>{})},800)}
const save=r=>{S.set('st',st);sync('plan',st.plan);sync('bm',st.bm);if(r!==false)render()};
const esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const toast=t=>{const d=document.createElement('div');d.className='toast';d.textContent=t;$('#toasts').append(d);setTimeout(()=>d.remove(),4000)};
const skel=n=>Array.from({length:n},(_,i)=>`<div class="sk" style="width:${96-i*13}%"></div>`).join('');
const log=t=>{st.log.unshift({t,d:Date.now()});st.log=st.log.slice(0,6)};
const ago=d=>{const m=Math.round((Date.now()-d)/6e4);return m<1?'now':m<60?m+' min':m<1440?Math.round(m/60)+' h':Math.round(m/1440)+' d'};

/* ---------- server and sign in ---------- */
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const wake=on=>{$('#wake').hidden=!on};
async function api(path,o={}){
  const safe=(o.method||'GET')==='GET'||o.retry,tries=safe?3:1;
  for(let i=0;i<tries;i++){
    const ctl=new AbortController(),tm=setTimeout(()=>ctl.abort(),o.timeout||70000);let r;
    try{const h=Object.assign({},o.headers||{});if(tok)h.Authorization='Bearer '+tok;r=await fetch(base+path,Object.assign({},o,{headers:h,signal:ctl.signal}))}
    catch(e){clearTimeout(tm);if(i<tries-1){wake(true);await wait(3000*(i+1));continue}wake(false);throw new Error('The server is not responding. It may be waking up, so please try again in a minute.')}
    clearTimeout(tm);
    if([502,503,504].includes(r.status)&&i<tries-1){wake(true);await wait(3000*(i+1));continue}
    wake(false);
    if(r.status===401&&!o.noauth){logout(true);throw new Error('Please sign in again.')}
    if(!r.ok){let d='';try{const j=await r.json();d=typeof j.detail==='string'?j.detail:JSON.stringify(j.detail)}catch{}throw new Error(d||('Request failed ('+r.status+')'))}
    return r.json();
  }
}
function wipeLocal(){
  try{Object.keys(localStorage).filter(k=>k==='tok'||k==='st'||k==='prof'||k.startsWith('cfg_')).forEach(k=>localStorage.removeItem(k))}catch{}
  tok='';st={chats:[],cur:{},bm:[],plan:{},an:[],docs:[],resume:'',match:null,skills:[],analyzed:false,answers:0,log:[]};P={};cur.coach=null;cur.kb=null;JOBS=[];$('#sc-out').innerHTML='';
  $$('#pform input,#pform select,#pform textarea,#resume,#jd,#c-basis').forEach(e=>e.value='');$('#aout').innerHTML='';$('#pres-s').textContent='';
}
const jpost=(p,b,o={})=>api(p,Object.assign({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)},o));
async function readFile(f){if(f.size>5*1024*1024)throw new Error('File is too large. The limit is 5 MB.');if(/\.txt$/i.test(f.name))return f.text();const fd=new FormData();fd.append('file',f);return (await api('/api/extract',{method:'POST',body:fd})).text}
const showAuth=on=>{$('#auth').style.display=on?'flex':'none'};
function logout(silent){wipeLocal();showAuth(false);showLand(true);render();if(!silent)toast('Signed out')}
let amode='in',rtok=location.hash.startsWith('#reset=')?location.hash.slice(7):'';
function setMode(m){amode=m;const T={in:['Sign in','Sign in'],up:['Create account','Create account'],forgot:['Reset password','Send reset link'],reset:['Choose a new password','Save new password']}[m];
  $('#a-h').textContent=T[0];$('#a-go').textContent=T[1];const er=$('#a-err');er.textContent='';er.style.color='var(--err)';
  $('#a-sw').textContent=m==='in'?'Create an account':m==='up'?'I already have an account':'Back to sign in';
  $('#a-fgw').hidden=m!=='in';$('#g-user').hidden=m==='reset';$('#g-pass').hidden=m==='forgot';$('#g-em').hidden=m!=='up';$('#a-hint').hidden=!(m==='up'||m==='reset');
  $('#gbtn').hidden=$('#a-or').hidden=!(m==='in'||m==='up');$('#l-user').textContent=m==='forgot'?'Username or email':'Username';$('#l-pass').textContent=m==='reset'?'New password':'Password';
  $('#a-pass').autocomplete=m==='in'?'current-password':'new-password'}
function openAuth(m){setMode(m);showAuth(true);renderG();setTimeout(()=>$('#a-user').focus(),50)}
const showLand=on=>{$('#land').style.display=on?'block':'none';if(on){$('#lmain').hidden=false;$('#llegal').hidden=true}};
$('#a-sw').onclick=()=>setMode(amode==='in'?'up':'in');
$('#a-fg').onclick=()=>setMode('forgot');
$('#a-x').onclick=()=>showAuth(false);
function renderG(){if(window._g&&window.google)google.accounts.id.renderButton($('#gbtn'),{theme:'outline',size:'large',text:'continue_with',width:300})}
function renderSample(){$('#lsample').innerHTML=[BANK[0],BANK[4]].map(b=>`<details style="border-top:0;border-bottom:1px solid var(--line)"><summary>${esc(b[1])}</summary><p style="margin-top:8px" class="mute">${esc(b[2])}</p></details>`).join('')}
document.addEventListener('click',e=>{
  const a=e.target.closest('[data-auth]');if(a){openAuth(a.dataset.auth);return}
  const l=e.target.closest('[data-l]');if(l&&$('#land').style.display==='block'){$('#llegal').innerHTML='<button class="btn ghost" id="lback" style="margin-bottom:18px"><i class="ph ph-arrow-left"></i>Back</button><div class="legal">'+$('#v-'+l.dataset.l).innerHTML+'</div>';$('#lmain').hidden=true;$('#llegal').hidden=false;$('#land').scrollTop=0;return}
  if(e.target.closest('#lback')){$('#lmain').hidden=false;$('#llegal').hidden=true;return}
  const sc=e.target.closest('[data-sc]');if(sc){$('#'+sc.dataset.sc).scrollIntoView({behavior:'smooth'})}});
$('#a-go').onclick=async()=>{const b=$('#a-go'),u=$('#a-user').value.trim(),p=$('#a-pass').value,em=$('#a-em').value.trim();if(b.disabled)return;$('#a-err').textContent='';b.disabled=true;
  try{
    if(amode==='forgot'){await jpost('/api/reset/request',{identifier:u},{noauth:true});$('#a-err').style.color='var(--acc)';$('#a-err').textContent='If an account with a saved email exists, a reset link has been sent.'}
    else if(amode==='reset'){await jpost('/api/reset/confirm',{token:rtok,password:p},{noauth:true});rtok='';history.replaceState(null,'',location.pathname);setMode('in');toast('Password updated. Please sign in.')}
    else{if(amode==='up')await jpost('/api/signup',{username:u,password:p},{noauth:true});
      const r=await jpost('/api/login',{username:u,password:p},{noauth:true,retry:true});tok=r.token;
      if(amode==='up'&&em){try{await jpost('/api/email',{email:em})}catch(e){toast(e.message)}}await enter(r.token)}
  }catch(e){$('#a-err').textContent=e.message}b.disabled=false};
$('#a-pass').addEventListener('keydown',e=>{if(e.key==='Enter')$('#a-go').click()});
async function enter(t){tok=t;S.set('tok',t);showAuth(false);showLand(false);$('#a-pass').value='';await boot2()}
async function initGoogle(){try{const c=await (await fetch('/api/config')).json();if(!c.google_client_id||!window.google)return;
  google.accounts.id.initialize({client_id:c.google_client_id,callback:async r=>{try{const j=await jpost('/api/google',{credential:r.credential},{noauth:true,retry:true});await enter(j.token)}catch(e){$('#a-err').textContent=e.message}}});
  window._g=true}catch{}}
async function boot2(){try{$('#acct').textContent=(await api('/api/me')).username}catch{return}
  await Promise.all([loadChats(),loadDocs(),loadState(),loadProgress()]);save();draw('coach');draw('kb')}
async function loadState(){try{const s=await api('/api/state');
  if(s.profile){P=s.profile;S.set('prof',P);PF.forEach(([k])=>{const e=$('#p_'+k);if(e)e.value=P[k]||''})}else if(Object.keys(P).length)sync('profile',P);
  if(s.plan)st.plan=s.plan;if(s.bm)st.bm=s.bm;lastSync={profile:JSON.stringify(P),plan:JSON.stringify(st.plan),bm:JSON.stringify(st.bm)}}catch{}}
async function loadProgress(){try{st.prog=await api('/api/progress');st.answers=st.prog.total}catch{}}
async function loadChats(){try{st.chats=await api('/api/sessions')}catch{}}
async function loadDocs(){try{st.docs=await api('/api/docs')}catch{}}

/* ---------- navigation ---------- */
function show(v){$$('.view').forEach(s=>s.classList.toggle('on',s.id==='v-'+v));$$('header nav button').forEach(a=>a.classList.toggle('on',a.dataset.v===v));$('.stage').scrollTop=0;if(v==='tools'&&!$('#t-resume').value)$('#t-resume').value=st.resume||'';if(v==='jobs')loadJobs();if(v==='coach'||v==='kb')draw(v)}
document.addEventListener('click',e=>{const a=e.target.closest('[data-v]');if(a)show(a.dataset.v)});

/* ---------- chats (saved on your account) ---------- */
const cur={},TY={coach:'chat',kb:'doc'},cfgKey=id=>'cfg_'+id;
function newC(k){cur[k]={id:null,kind:k,title:'New chat',msgs:[],cfg:{round:CF.round,level:CF.level,basis:'',files:[],res:false,lang:'English'}};return cur[k]}
const persist=c=>{if(c.id)S.set(cfgKey(c.id),c.cfg)};
function draw(k){
  const c=cur[k]||newC(k),q=($('#hq-'+k).value||'').toLowerCase();
  $('#hl-'+k).innerHTML=st.chats.filter(x=>x.type===TY[k]&&x.title.toLowerCase().includes(q)).map(x=>`<div class="it ${x.id===c.id?'on':''}"><button type="button" class="ob" data-open="${x.id}">${esc(x.title)}</button><button type="button" class="db" data-del="${x.id}" aria-label="Delete chat ${esc(x.title)}"><i class="ph ph-trash"></i></button></div>`).join('')||'<span class="sm mute">No saved chats.</span>';
  const intro=k==='coach'?(P.target?'Ready to practice for '+esc(P.target)+'. Set the basis on the right, or just say start.':'Tell me the role you are preparing for, or pick a starter above.'):'Add a PDF, then ask me about it.';
  const box=$('#m-'+k);
  box.innerHTML=(c.msgs.length?'':`<div class="m a">${intro}</div>`)+c.msgs.map(m=>`<div class="m ${m.role==='user'?'u':m.role==='error'?'e':'a'}">${esc(m.content)}</div>`).join('')+(c.busy?`<div class="m a" style="width:min(420px,80%)">${skel(3)}</div>`:'');
  box.scrollTop=box.scrollHeight;
  if(k==='coach'){$('#c-round').value=c.cfg.round;$('#c-lang').value=c.cfg.lang||'English';$('#c-level').value=c.cfg.level;$('#c-basis').value=c.cfg.basis;$('#c-res').checked=!!c.cfg.res;
    $('#c-files').innerHTML=c.cfg.files.map((f,i)=>`<div class="file"><span>${esc(f.name)}</span><button type="button" class="db" data-rf="${i}" aria-label="Remove ${esc(f.name)}"><i class="ph ph-x"></i></button></div>`).join('')}
}
['coach','kb'].forEach(k=>{
  $('#hq-'+k).oninput=()=>draw(k);$('#nc-'+k).onclick=()=>{newC(k);draw(k)};
  $('#hl-'+k).onclick=async e=>{
    const d=e.target.closest('[data-del]');
    if(d){if(!confirm('Delete this chat?'))return;try{await api('/api/sessions/'+d.dataset.del,{method:'DELETE'})}catch(err){toast(err.message)}if(cur[k]&&String(cur[k].id)===d.dataset.del)newC(k);await loadChats();save();draw(k);return}
    const o=e.target.closest('[data-open]');
    if(o){try{const r=await api('/api/sessions/'+o.dataset.open),id=+o.dataset.open,x=st.chats.find(z=>z.id===id&&z.type===TY[k]);
      cur[k]={id,kind:k,title:x?x.title:'Chat',msgs:r.messages,cfg:S.get(cfgKey(id),null)||{round:CF.round,level:CF.level,basis:'',files:[],res:false,lang:'English'}};draw(k)}catch(err){toast(err.message)}}};
  $('#s-'+k).onclick=()=>{const i=$('#i-'+k),t=i.value.trim();if(t){i.value='';send(k,t,true)}};
  $('#i-'+k).addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('#s-'+k).click()}});
});
async function send(k,t,real){
  if(k==='kb'&&!st.docs.length){toast('Add a PDF first.');return}
  const c=cur[k]||newC(k);c.msgs.push({role:'user',content:t});if(c.title==='New chat')c.title=t.slice(0,45);c.busy=true;draw(k);
  try{let r,a;
    if(k==='kb'){r=await jpost('/api/ask',{question:t,session_id:c.id});a=r.answer}
    else{const h=c.msgs.filter(m=>m.role!=='error').slice(-20).map(m=>({role:m.role,content:m.content}));r=await jpost('/api/coach',{messages:h,session_id:c.id,round:c.cfg.round,level:c.cfg.level,language:c.cfg.lang||'English',target:P.target||'',experience:P.exp||'',basis:c.cfg.basis||'',reference:c.cfg.files.map(x=>x.name+': '+x.text.slice(0,2500)).join('\n').slice(0,6000),resume:c.cfg.res?(st.resume||'').slice(0,4000):''});a=r.reply;if(real){st.answers++;if(st.answers%5===1)log('Practice session')}speak(a)}
    if(r.session_id)c.id=r.session_id;persist(c);c.msgs.push({role:'assistant',content:a})}
  catch(e){c.msgs.push({role:'error',content:e.message})}
  c.busy=false;await Promise.all([loadChats(),k==='coach'?loadProgress():0]);save();draw(k);
}
function apply(t){const c=cur.coach||newC('coach');persist(c);send('coach',t)}
$('#c-round').onchange=e=>{const c=cur.coach||newC('coach');c.cfg.round=e.target.value;apply('Switch the interview to the '+c.cfg.round+' round now. Confirm in one line and ask the first question of this round.')};
$('#c-level').onchange=e=>{const c=cur.coach||newC('coach');c.cfg.level=e.target.value;apply('Change the difficulty to '+c.cfg.level+' now. Confirm in one line and ask the next question at this level.')};
$('#c-lang').onchange=e=>{const c=cur.coach||newC('coach');c.cfg.lang=e.target.value;apply('Continue the interview in '+c.cfg.lang+' from now on. Confirm in one line and ask the next question.')};
$('#c-basis').onchange=e=>{const c=cur.coach||newC('coach');c.cfg.basis=e.target.value;persist(c);if(e.target.value.trim())apply('The interview basis has changed. Confirm in one line and ask the next question based on it.')};
$('#c-res').onchange=e=>{const c=cur.coach||newC('coach');c.cfg.res=e.target.checked;persist(c)};
$('#c-file').onchange=async e=>{const c=cur.coach||newC('coach');let n=0;for(const f of e.target.files){try{c.cfg.files.push({name:f.name,text:await readFile(f)});n++}catch(err){toast('Could not read '+f.name+'. '+err.message)}}
  e.target.value='';persist(c);draw('coach');if(n)apply('New reference files were attached. Confirm in one line and use them for the next question.')};
$('#c-files').onclick=e=>{const r=e.target.closest('[data-rf]');if(r){cur.coach.cfg.files.splice(+r.dataset.rf,1);persist(cur.coach);draw('coach')}};
['Start the interview','Ask me a behavioral question','Ask a technical question','Review my last answer','Give me a harder question'].forEach(t=>{const b=document.createElement('button');b.className='chip';b.textContent=t;b.onclick=()=>send('coach',t);$('#chips').append(b)});

/* ---------- documents ---------- */
$('#kbfile').onchange=async e=>{for(const f of e.target.files){const fd=new FormData();fd.append('doc',f);
  try{if(f.size>5*1024*1024)throw new Error('File is too large. The limit is 5 MB.');const r=await api('/api/docs',{method:'POST',body:fd});log('Added '+f.name);toast(f.name+' added')}catch(err){toast(f.name+': '+err.message)}}
  e.target.value='';await loadDocs();save()};
$('#kbclear').onclick=async()=>{if(!st.docs.length)return;if(confirm('Remove all documents?')){try{await api('/api/docs',{method:'DELETE'})}catch(e){toast(e.message)}await loadDocs();save()}};

/* ---------- voice ---------- */
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
$$('[data-dic]').forEach(b=>b.onclick=()=>{
  if(!SR){toast('Voice input needs Chrome or Edge.');return}
  if(b._r){b._r.stop();b._r=null;b.classList.remove('live');return}
  const el=$('#'+b.dataset.dic),r=new SR();r.continuous=true;r.lang=CF.lang;b._r=r;
  r.onresult=e=>{for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal){el.value+=(el.value?' ':'')+e.results[i][0].transcript.trim();el.dispatchEvent(new Event('input'))}};
  r.onend=()=>{if(b._r)try{r.start()}catch{}};
  r.onerror=x=>{if(x.error==='not-allowed'){b._r=null;b.classList.remove('live');toast('Microphone access is blocked.')}};
  b.classList.add('live');r.start()});
let voices=[];const loadV=()=>{voices=speechSynthesis.getVoices().filter(v=>v.lang.startsWith('en'));$('#voice').innerHTML='<option value="female">Female (default)</option><option value="male">Deep male</option>'+voices.map((v,i)=>`<option value="${i}">${esc(v.name)}</option>`).join('');$('#voice').value=CF.voice};
if('speechSynthesis' in window){loadV();speechSynthesis.onvoiceschanged=loadV}
function speak(t){if(CF.read!=='on'||!('speechSynthesis' in window))return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t),v=CF.voice;
  const x=!isNaN(v)&&voices[v]?voices[v]:voices.find(a=>(v==='male'?/male|david|guy|daniel|james|mark/i:/female|zira|samantha|aria|jenny|susan|hazel/i).test(a.name))||voices[0];
  if(x)u.voice=x;u.rate=+CF.rate;if(v==='male')u.pitch=.7;speechSynthesis.speak(u)}

/* ---------- analyzer ---------- */
$$('input[data-t]').forEach(i=>i.onchange=async()=>{const f=i.files[0];if(!f)return;try{$('#'+i.dataset.t).value=await readFile(f);toast('File loaded')}catch(e){toast('Could not read the file. '+e.message)}i.value=''});
function gen(v){if(v==null)return'';if(typeof v!=='object')return `<p style="margin-bottom:6px">${esc(v)}</p>`;
  if(Array.isArray(v))return v.map(x=>x&&typeof x==='object'?item(x):gen(x)).join('');
  return Object.entries(v).map(([k,x])=>`<div style="margin-top:8px"><b class="sm" style="color:var(--acc);text-transform:capitalize">${esc(k.replace(/_/g,' '))}</b>${gen(x)}</div>`).join('')}
function item(o){const ks=Object.keys(o),qk=ks.find(k=>/^(question|q|title|name)$/.test(k))||ks.find(k=>typeof o[k]==='string')||ks[0],rest={...o};delete rest[qk];
  return `<details><summary>${esc(o[qk])}<i class="ph ph-caret-down"></i></summary>${gen(rest)}</details>`}
function showResult(r){const K=['score','match_score','match','match_percentage'],k=K.find(x=>r[x]!=null),sc=k?r[k]:null,rest={...r};K.forEach(x=>delete rest[x]);delete rest.summary;
  return `<div class="box" style="display:flex;gap:22px;align-items:center"><b style="font-family:Fraunces,serif;font-size:52px;color:var(--acc)">${sc!=null?esc(typeof sc==='number'&&sc<=100?sc+'%':sc):'Result'}</b><p>${esc(r.summary||'Match between your resume and this job description.')}</p></div>`+Object.entries(rest).map(([k,v])=>`<h2 style="margin:22px 0 6px;text-transform:capitalize">${esc(k.replace(/_/g,' '))}</h2>${gen(v)}`).join('')}
$('#analyze').onclick=async()=>{const resume=$('#resume').value.trim(),jd=$('#jd').value.trim(),o=$('#aout');
  if(!resume||!jd){toast('Add both a resume and a job description.');return}
  o.innerHTML='<div class="box">'+skel(7)+'</div>';$('#analyze').disabled=true;
  try{const fd=new FormData();fd.append('resume_text',resume);fd.append('jd',jd);
    const r=await api('/api/analyze',{method:'POST',body:fd});
    st.resume=resume;st.analyzed=true;const K=['score','match_score','match','match_percentage'].find(x=>r[x]!=null);st.match=K&&typeof r[K]==='number'?r[K]:null;
    st.skills=Array.isArray(r.skills)?r.skills.filter(x=>x&&x.name).slice(0,8):[];
    o.innerHTML=showResult(r);log('Resume match '+(st.match!=null?st.match+'%':'run'));await loadChats();save()}
  catch(e){o.innerHTML='<div class="box" style="color:var(--err)">Analysis failed. '+esc(e.message)+'</div>'}$('#analyze').disabled=false};
$('#past').onclick=e=>{const a=e.target.closest('[data-an]');if(a){const x=st.chats.find(z=>z.type==='analysis'&&String(z.id)===a.dataset.an);if(x){$('#aout').innerHTML=showResult(x.result);$('#aout').scrollIntoView()}}};

/* ---------- question bank ---------- */
const BANK=[
['Behavioral','Tell me about a time you handled a conflict in your team.','Situation: two teammates disagreed on scope. Task: protect the deadline. Action: I met each separately, found the shared goal, and proposed a split. Result: shipped on time and the disagreement ended.'],
['Behavioral','Describe a project you are proud of.','Name the problem, your exact role, two decisions you made, and a measurable result such as time saved or users gained.'],
['Behavioral','Tell me about a failure and what you learned.','Pick a real, modest failure. Own it in one sentence, explain what you changed in your process, and show the next time it went right.'],
['Behavioral','How do you handle tight deadlines?','Describe how you cut scope with the owner, order tasks by risk, communicate early and protect quality on the core feature.'],
['Technical','Explain a system you designed end to end.','Start with requirements, then components, data flow, trade-offs you chose and rejected, and how you measured it in production.'],
['Technical','How do you debug a problem you cannot reproduce?','Add logging, narrow by time and input, compare working and failing environments, form one hypothesis at a time and test it.'],
['Technical','How do you decide between a SQL and a NoSQL database?','Start with access patterns and consistency needs. Choose SQL for relations and transactions, NoSQL for flexible schema or scale by key.'],
['Technical','How do you review someone else\'s code?','Check correctness and tests first, then readability and risk. Ask questions instead of giving orders, and approve small safe changes quickly.'],
['HR and salary','Why do you want to leave your current job?','Focus on what you want next: growth, scope or domain. Stay positive about your current employer.'],
['HR and salary','What are your salary expectations?','Share a researched range based on the role and market, say it is open to the full package, and ask about the band for the role.'],
['HR and salary','Where do you see yourself in five years?','Link your growth to the role: deeper skill, wider ownership, mentoring others. Avoid naming a specific title.'],
['Situational','A manager gives you two urgent tasks. What do you do?','Clarify impact and deadlines with the manager, show the trade-off, agree an order, and update stakeholders on the delayed task.'],
['Situational','You find a serious bug the day before release. What next?','Assess severity and users affected, tell the owner now, offer options (fix, patch, delay), and write a short post-release note.']];
let bcat='All';
function drawBank(){$('#bcats').innerHTML=['All','Saved',...new Set(BANK.map(b=>b[0]))].map(c=>`<button class="chip ${c===bcat?'on':''}" data-bc="${c}">${c}</button>`).join('');
  const q=$('#bq').value.toLowerCase();
  $('#blist').innerHTML=BANK.map((b,i)=>({b,i})).filter(({b,i})=>(bcat==='All'||(bcat==='Saved'?st.bm.includes(i):b[0]===bcat))&&b[1].toLowerCase().includes(q)).map(({b,i})=>`<details><summary><span>${esc(b[1])} <span class="sm mute">${b[0]}</span></span></summary><p style="margin:8px 0">${esc(b[2])}</p><button class="btn ghost" data-bm="${i}"><i class="ph ph-bookmark-simple"></i>${st.bm.includes(i)?'Saved':'Save'}</button> <button class="btn" data-bp="${i}">Practice in coach</button></details>`).join('')||'<p class="mute">No questions match.</p>'}
$('#bcats').onclick=e=>{const c=e.target.dataset.bc;if(c){bcat=c;drawBank()}};$('#bq').oninput=drawBank;
$('#blist').onclick=e=>{const m=e.target.closest('[data-bm]'),p=e.target.closest('[data-bp]');
  if(m){const i=+m.dataset.bm;st.bm=st.bm.includes(i)?st.bm.filter(x=>x!==i):[...st.bm,i];save();drawBank()}
  if(p){const c=newC('coach');c.title='Practice: '+BANK[p.dataset.bp][1].slice(0,30);show('coach');send('coach','Ask me this question and score my answer: '+BANK[p.dataset.bp][1])}};

/* ---------- planner (built from your latest resume match) ---------- */
const hs=s=>{let x=0;for(const c of s)x=(x*31+c.charCodeAt(0))|0;return (x>>>0).toString(36)};
const lastAn=()=>{const a=st.chats.find(x=>x.type==='analysis');return a&&a.result};
function tasks(){const dl=P.date?Math.max(2,Math.ceil((new Date(P.date)-Date.now())/864e5)):14,d=f=>Math.max(1,Math.round(dl*f)),a=lastAn(),T=[];
  T.push(['p1','Complete your profile and add your resume','The coach and planner use these details.',1]);
  if(!a)T.push(['p2','Run a resume match against your target job description','Your plan is personalized from this analysis.',2]);
  else{
    (a.gaps||[]).slice(0,3).forEach((g,i)=>T.push(['g'+hs(g),'Close this gap: '+g,'Found in your latest resume match.',d(.15+.1*i)]));
    (a.suggestions||[]).slice(0,2).forEach((g,i)=>T.push(['s'+hs(g),'Update your resume: '+g,'Suggested in your latest resume match.',d(.2+.1*i)]));
    (a.interview_questions||[]).slice(0,3).forEach(q=>T.push(['q'+hs(q.question),'Practice in the coach: '+q.question,'Likely '+(q.type||'')+' question for this job.',d(.5)]))}
  T.push(['p4','Practice a Behavioral round in the coach at Standard level','Builds a base before harder rounds.',d(.35)],['p6','Practice the salary and HR questions','Commonly asked in every process.',d(.65)],['p7','Run a Mixed round at Hard level','Tests you under pressure.',d(.8)],['p8','Review weak answers and rewrite them','Use the coach feedback.',Math.max(d(.9),2)],['p9','Rest, and re-read your project story','Fresh and calm on the day.',dl]);
  return T}
function drawPlan(){const t=tasks(),n=t.filter(x=>st.plan[x[0]]).length;$('#pl-bar').style.width=n/t.length*100+'%';
  $('#pl-sub').textContent=(P.date?'Plan built for your interview on '+P.date+'. ':'Set your interview date in Profile for a plan that fits your timeline. Showing a 14 day plan. ')+(lastAn()?'Tasks come from your latest resume match. ':'Run a resume match to personalize it. ')+n+' of '+t.length+' tasks done.';
  $('#pl-list').innerHTML=t.map(x=>`<label class="task"><input type="checkbox" data-pt="${x[0]}" ${st.plan[x[0]]?'checked':''}><span>${esc(x[1])}<br><span class="sm mute">${esc(x[2])}</span></span><small>By day ${x[3]}</small></label>`).join('')}
$('#pl-list').onchange=e=>{const k=e.target.dataset.pt;if(k){st.plan[k]=e.target.checked;save()}};

/* ---------- profile ---------- */
const PF=[['name','Full name'],['email','Email','email'],['phone','Phone','tel'],['loc','Location'],['title','Current job title'],['company','Current company'],['exp','Years of experience','sel',['0 to 1','1 to 3','3 to 6','6 to 10','10 or more']],['edu','Highest education'],['target','Target role'],['tcomp','Target companies'],['sal','Expected salary'],['notice','Notice period','sel',['Immediate','15 days','30 days','60 days','90 days']],['mode','Work mode','sel',['Remote','Hybrid','On-site']],['date','Interview date','date'],['li','LinkedIn URL','url'],['gh','GitHub or portfolio URL','url'],['skills','Key skills, separated by commas','text','full'],['sum','Professional summary','ta','full']];
$('#pform').innerHTML=PF.map(([k,l,t,x])=>`<div class="${x==='full'?'full':''}"><label class="lbl" for="p_${k}">${l}</label>${t==='ta'?`<textarea id="p_${k}"></textarea>`:t==='sel'?`<select id="p_${k}"><option value="">Select</option>${x.map(o=>`<option>${o}</option>`).join('')}</select>`:`<input id="p_${k}" type="${t||'text'}">`}</div>`).join('');
PF.forEach(([k])=>{const e=$('#p_'+k);e.value=P[k]||'';e.oninput=e.onchange=()=>{P[k]=e.value;S.set('prof',P);sync('profile',P);render()}});
$('#pres').onchange=async e=>{const f=e.target.files[0];if(!f)return;const t=await readFile(f);if(t){st.resume=t;$('#pres-s').textContent=f.name+' saved';save()}else toast('Could not read the file.');e.target.value=''};

/* ---------- settings ---------- */
function applyTheme(){const d=CF.theme==='dark'||(CF.theme==='system'&&matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.dataset.theme=d?'dark':'light';document.documentElement.style.setProperty('--fs',CF.size+'px')}
$$('[data-cf]').forEach(e=>{e.value=CF[e.dataset.cf];e.onchange=()=>{CF[e.dataset.cf]=e.value;S.set('cfg',CF);applyTheme();toast('Saved')}});
$('#out').onclick=()=>logout();
$('#exp').onclick=async()=>{const d={profile:P,chats:[],analyses:st.chats.filter(x=>x.type==='analysis')};for(const c of st.chats.filter(x=>x.type!=='analysis')){try{d.chats.push({...c,messages:(await api('/api/sessions/'+c.id)).messages})}catch{}}
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));a.download='ascendra-data.json';a.click()};
$('#clrc').onclick=async()=>{if(confirm('Delete all chats?')){try{await api('/api/sessions',{method:'DELETE'})}catch(e){toast(e.message);return}newC('coach');newC('kb');await loadChats();save();draw('coach');draw('kb');toast('Chats deleted')}};
$('#clra').onclick=async()=>{const v=prompt('This permanently deletes your account, chats, documents and analyses. Type DELETE to confirm.');if(v!=='DELETE')return;
  try{await jpost('/api/account/delete',{confirm:'DELETE'})}catch(e){toast(e.message);return}wipeLocal();showAuth(false);showLand(true);render();toast('Your account was deleted')};

/* ---------- overview ---------- */
function pdone(){const k=['name','email','title','target','exp','skills','date'];return k.filter(x=>(P[x]||'').trim()).length/k.length}
function score(){const t=tasks(),pl=t.filter(x=>st.plan[x[0]]).length/t.length;return Math.round(pdone()*20+(st.resume?15:0)+(st.analyzed?20:0)+Math.min(st.answers/10,1)*25+pl*20)}
function render(){
  const sc=score(),days=P.date?Math.ceil((new Date(P.date)-Date.now())/864e5):null;
  $('#h-title').textContent=P.name?'Welcome back, '+P.name.split(' ')[0]:'Overview';
  $('#h-sub').textContent=P.target?'Preparing for '+P.target+(P.tcomp?' at '+P.tcomp:'')+(days!=null?(days>=0?'. '+days+' days to your interview.':'. Your interview date has passed.'):'.'):'Fill in your profile to personalize practice, questions and the planner.';
  $('#strip').innerHTML=`<div><span class="mute sm">Preparation progress</span><b class="big">${sc}%</b></div><div><span class="mute sm">Chats saved</span><b>${st.chats.filter(x=>x.type!=='analysis').length}</b></div><div><span class="mute sm">Practice answers</span><b>${st.answers}</b></div><div><span class="mute sm">Match score</span><b>${st.match!=null?st.match+'%':'-'}</b></div><div><span class="mute sm">Saved questions</span><b>${st.bm.length}</b></div>`;
  const n=pdone()<.7?['Finish your profile','The coach and planner need your target role, experience and interview date.','profile','Open profile']:!st.analyzed?['Match your resume to a job','Paste both and get a score and six likely questions.','analyzer','Open resume match']:st.answers<10?['Answer '+(10-st.answers)+' more practice questions','Practice answers carry the largest share of your progress.','coach','Start interview']:['Run a harder round','Switch to Hard level and a different round type.','coach','Start interview'];
  $('#n-title').textContent=n[0];$('#n-text').textContent=n[1];$('#n-btn').textContent=n[3];$('#n-btn').onclick=()=>show(n[2]);
    const g=(lastAn()||{}).gaps||[];$('#bars').innerHTML=g.length?g.slice(0,6).map(x=>`<p style="padding:7px 0;border-top:1px solid var(--line);font-size:14px">${esc(x)}</p>`).join(''):'<p class="mute sm">Run a resume match and the gaps it finds show up here.</p>';
  $('#act').innerHTML=st.log.length?st.log.map(l=>`<tr><td>${esc(l.t)}</td><td class="mute" style="text-align:right">${ago(l.d)}</td></tr>`).join(''):'<tr><td class="mute">Nothing yet. Analyses and practice sessions appear here.</td></tr>';
    $('#kbd').innerHTML=st.docs.map(d=>`<div class="file"><span>${esc(d.doc_name)}</span><span class="mute">${d.chunks}</span></div>`).join('');
    const an=st.chats.filter(x=>x.type==='analysis');$('#past').innerHTML=an.length?an.map(a=>`<div class="task" style="cursor:pointer" data-an="${a.id}"><span>${esc(a.title)}</span><small>${a.created_at}</small></div>`).join(''):'<p class="mute sm">Saved analyses appear here.</p>';
  drawPlan();drawChart();
}
function drawChart(){const d=(st.prog&&st.prog.days)||[];
  if(!d.length){$('#chart').innerHTML='<p class="mute sm">Answers you type in the coach are counted per day here. Nothing yet.</p>';return}
  const m=Math.max(...d.map(x=>x.count)),W=560,H=140,sl=W/d.length,bw=Math.min(36,sl-6);
  $('#chart').innerHTML=`<svg viewBox="0 0 ${W} ${H+24}" role="img" aria-label="Answers you typed per day" style="width:100%;max-width:640px"><line x1="0" y1="${H}" x2="${W}" y2="${H}" stroke="var(--line)"/>`+d.map((x,i)=>{const h=Math.round(x.count/m*(H-20)),cx=i*sl+sl/2;return `<rect x="${cx-bw/2}" y="${H-h}" width="${bw}" height="${h}" rx="3" fill="var(--acc)"/><text x="${cx}" y="${H-h-4}" text-anchor="middle" font-size="11" fill="var(--mute)">${x.count}</text><text x="${cx}" y="${H+15}" text-anchor="middle" font-size="10" fill="var(--mute)">${x.date.slice(5)}</text>`}).join('')+`</svg><p class="mute sm">Answers you typed per day, last 14 active days. This counts activity, not skill.</p>`}
$('#ics').onclick=()=>{if(!P.date){toast('Set your interview date first.');return}
  const f=x=>x.replace(/-/g,''),n=new Date(P.date);n.setDate(n.getDate()+1);const t=s=>s.replace(/[,;\\]/g,m=>'\\'+m);
  const ics=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Ascendra//EN','BEGIN:VEVENT','UID:'+f(P.date)+'@ascendra','DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z','DTSTART;VALUE=DATE:'+f(P.date),'DTEND;VALUE=DATE:'+f(n.toISOString().slice(0,10)),'SUMMARY:'+t('Interview'+(P.tcomp?' at '+P.tcomp:'')),'BEGIN:VALARM','TRIGGER:-P1D','ACTION:DISPLAY','DESCRIPTION:Interview tomorrow','END:VALARM','END:VEVENT','END:VCALENDAR'].join('\r\n')+'\r\n';
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([ics],{type:'text/calendar'}));a.download='interview.ics';a.click()};
$('#s-emb').onclick=async()=>{try{await jpost('/api/email',{email:$('#s-em').value.trim()});toast('Recovery email saved')}catch(e){toast(e.message)}};
async function tool(path,btn){const resume=$('#t-resume').value.trim(),jd=$('#t-jd').value.trim();
  if(resume.length<50||jd.length<30){toast('Add your resume and the job description.');return}
  btn.disabled=true;$('#t-out').innerHTML='<div class="box">'+skel(6)+'</div>';
  try{const r=await jpost(path,{resume,jd});$('#t-out').innerHTML='<div class="box"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><b>Review before you use it</b><button type="button" class="btn ghost" id="t-copy">Copy</button></div><div id="t-text" style="white-space:pre-wrap"></div></div>';
    $('#t-text').textContent=r.text;$('#t-copy').onclick=()=>navigator.clipboard.writeText(r.text).then(()=>toast('Copied'))}
  catch(e){$('#t-out').innerHTML='<div class="box" style="color:var(--err)">'+esc(e.message)+'</div>'}btn.disabled=false}
$('#t-rw').onclick=e=>tool('/api/rewrite',e.currentTarget);$('#t-cv').onclick=e=>tool('/api/cover',e.currentTarget);
let GEN=[];
function drawGen(){$('#bout').innerHTML=GEN.map((q,i)=>`<details><summary><span>${esc(q.question)} <span class="sm mute">${esc(q.category)}</span></span></summary><p style="margin:8px 0">${esc(q.answer)}</p><button type="button" class="btn" data-gp="${i}">Practice in coach</button></details>`).join('')}
$('#bgo').onclick=async()=>{const role=($('#brole').value.trim()||P.target||'').slice(0,80);if(!role){toast('Enter a role first.');return}
  const b=$('#bgo');b.disabled=true;$('#bout').innerHTML='<div class="box">'+skel(5)+'</div>';
  try{const r=await jpost('/api/bank',{role,category:$('#bcat2').value,level:$('#blev').value});GEN=r.questions.concat(GEN);drawGen()}
  catch(e){$('#bout').innerHTML='<p style="color:var(--err)">'+esc(e.message)+'</p>'}b.disabled=false};
$('#bout').onclick=e=>{const p=e.target.closest('[data-gp]');if(p){const q=GEN[p.dataset.gp].question,c=newC('coach');c.title='Practice: '+q.slice(0,30);show('coach');send('coach','Ask me this question and score my answer: '+q)}};
/* ---------- job tracker ---------- */
let JOBS=[],jedit=null;
async function loadJobs(){try{JOBS=await api('/api/jobs')}catch(e){toast(e.message)}drawJobs()}
function drawJobs(){const f=$('#jf').value,L=JOBS.filter(j=>!f||j.status===f);if($('#jo').value==='i')L.sort((a,b)=>(a.interview_on||'9').localeCompare(b.interview_on||'9'));
  const ST=['Applied','Interview','Offer','Rejected','Withdrawn'];
  $('#jlist').innerHTML=L.length?L.map(j=>`<tr><td><b>${esc(j.company)}</b><br><span class="sm mute">${esc(j.role)}</span></td><td><select data-js="${j.id}" aria-label="Status for ${esc(j.company)}" style="width:auto">${ST.map(s=>`<option ${s===j.status?'selected':''}>${s}</option>`).join('')}</select></td><td class="sm">${esc(j.applied_on||'-')}</td><td class="sm">${esc(j.interview_on||'-')}</td><td style="text-align:right;white-space:nowrap"><button type="button" class="btn ghost" data-je="${j.id}">Edit</button> <button type="button" class="btn ghost" data-jd="${j.id}" aria-label="Delete ${esc(j.company)}"><i class="ph ph-trash"></i></button></td></tr>${j.notes?`<tr><td colspan="5" class="sm mute">${esc(j.notes)}</td></tr>`:''}`).join(''):'<tr><td colspan="5" class="mute">No applications yet. Add your first one above.</td></tr>'}
const jbody=()=>({company:$('#jc').value.trim(),role:$('#jr').value.trim(),status:$('#js').value,applied_on:$('#ja').value,interview_on:$('#ji').value,notes:$('#jn').value});
function jreset(){jedit=null;['jc','jr','ja','ji','jn'].forEach(i=>$('#'+i).value='');$('#js').value='Applied';$('#jsave').textContent='Add application';$('#jcancel').hidden=true}
$('#jsave').onclick=async()=>{const b=jbody();if(!b.company||!b.role){toast('Add a company and a role.');return}
  try{await api(jedit?'/api/jobs/'+jedit:'/api/jobs',{method:jedit?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});jreset();await loadJobs()}catch(e){toast(e.message)}};
$('#jcancel').onclick=jreset;$('#jf').onchange=$('#jo').onchange=drawJobs;
$('#jlist').onclick=async e=>{const ed=e.target.closest('[data-je]'),de=e.target.closest('[data-jd]');
  if(ed){const j=JOBS.find(x=>x.id==ed.dataset.je);jedit=j.id;$('#jc').value=j.company;$('#jr').value=j.role;$('#js').value=j.status;$('#ja').value=j.applied_on||'';$('#ji').value=j.interview_on||'';$('#jn').value=j.notes||'';$('#jsave').textContent='Save changes';$('#jcancel').hidden=false;$('#jc').focus()}
  if(de&&confirm('Delete this application?')){try{await api('/api/jobs/'+de.dataset.jd,{method:'DELETE'});await loadJobs()}catch(err){toast(err.message)}}};
$('#jlist').onchange=async e=>{const id=e.target.dataset.js;if(!id)return;const j=JOBS.find(x=>x.id==id);
  try{await api('/api/jobs/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...j,status:e.target.value})});j.status=e.target.value}catch(err){toast(err.message);drawJobs()}};
/* ---------- scorecard ---------- */
$('#sc-go').onclick=async()=>{const c=cur.coach;if(!c||!c.id){toast('Answer at least one interview question first.');return}
  show('score');$('#sc-out').innerHTML='<div class="box">'+skel(8)+'</div>';
  try{const r=await jpost('/api/scorecard',{session_id:c.id}),L=a=>a.length?a.map(x=>`<p style="margin-bottom:6px">${esc(x)}</p>`).join(''):'<p class="mute sm">None listed.</p>';
    $('#sc-out').innerHTML=`<div class="box" style="display:flex;gap:22px;align-items:center;flex-wrap:wrap"><b style="font-family:Fraunces,serif;font-size:52px;color:var(--acc)">${r.average}/10</b><div><p>Average over ${r.count} answer${r.count>1?'s':''} you typed. ${esc(new Date().toLocaleDateString())}</p><p class="mute sm">${esc(r.note)}</p></div></div>
    <p class="mute sm" style="margin:10px 0">Scoring criteria: ${esc(r.criteria)}</p>
    <div class="cols"><div><h2>Strengths</h2>${L(r.strengths)}</div><div><h2>To improve</h2>${L(r.weaknesses)}</div></div>
    <h2 style="margin-top:22px">Recommendations</h2>${L(r.recommendations)}
    <h2 style="margin:22px 0 6px">Answer by answer</h2><table><tbody>${r.answers.map(a=>`<tr><td>${esc(a.question)}</td><td><b>${a.score}</b>/10</td><td class="sm">${esc(a.comment)}</td></tr>`).join('')}</tbody></table>
    <button type="button" class="btn no-print" id="sc-pdf" style="margin-top:18px"><i class="ph ph-file-pdf"></i>Save as PDF</button><p class="mute sm no-print">Opens your print dialog. Choose "Save as PDF" as the printer.</p>`;
    $('#sc-pdf').onclick=()=>window.print()}
  catch(e){$('#sc-out').innerHTML='<div class="box" style="color:var(--err)">'+esc(e.message)+'</div>'}};
/* ---------- guest resume match ---------- */
$('#g-go').onclick=async()=>{const r=$('#g-resume').value.trim(),j=$('#g-jd').value.trim(),o=$('#g-out');
  if(r.length<50||j.length<30){o.textContent='Paste a longer resume and job description.';return}
  const b=$('#g-go');b.disabled=true;o.innerHTML='<div class="box">'+skel(5)+'</div>';
  try{const fd=new FormData();fd.append('resume_text',r);fd.append('jd',j);const x=await api('/api/guest/analyze',{method:'POST',body:fd,noauth:true}),L=a=>(a||[]).map(t=>`<p style="margin-bottom:6px">${esc(t)}</p>`).join('')||'<p class="mute sm">None listed.</p>';
    o.innerHTML=`<div class="box"><b style="font-family:Fraunces,serif;font-size:44px;color:var(--acc)">${esc(x.score??'-')}%</b><div class="cols" style="margin-top:8px"><div><h3>Strengths</h3>${L(x.strengths)}</div><div><h3>Gaps</h3>${L(x.gaps)}</div></div><p class="mute sm" style="margin-top:10px">This is a short preview. <button type="button" class="lk" data-auth="up">Create an account</button> for interview questions, a resume rewrite and saved history.</p></div>`}
  catch(e){o.innerHTML='<p style="color:var(--err)">'+esc(e.message)+'</p>'}b.disabled=false};
let LG={};
function renderLegal(){
  const em=LG.contact_email?`<p>Contact: <a href="mailto:${esc(LG.contact_email)}" style="color:var(--acc)">${esc(LG.contact_email)}</a></p>`:'',nm=LG.legal_name?esc(LG.legal_name):'the operator of Ascendra',ai=LG.ai_provider?esc(LG.ai_provider):'a third-party AI language model provider';
  $('#v-privacy').innerHTML=`<h1>Privacy Policy</h1><p class="sub">Last updated 28 October 2026.</p>
<h2>Who we are</h2><p>Ascendra is operated by ${nm}.</p>${em}
<h2>What we collect and where it is stored</h2><p>On our servers: your username (or Google email address), a salted hash of your password, the resume and job description text you submit, the text of PDFs you add to the knowledge base, your chat messages and your analysis results. In your browser only: profile details, preferences, planner progress and practice counts. We do not run analytics or advertising trackers.</p>
<h2>How we use it</h2><p>Only to run the features you ask for: resume matching, mock interviews and answers from your documents. Text you submit is sent to ${ai} to generate replies.</p>
<h2>Service providers</h2><p>Hosting: Render. Database: Supabase (PostgreSQL). Optional sign-in: Google. AI processing: ${ai}. Your browser also loads fonts from Google Fonts and icons from jsDelivr. Voice dictation uses your browser's speech recognition service, which may send audio to its provider.</p>
<h2>Deleting your data</h2><p>In Settings you can clear your chat history, remove documents, or delete your account, which permanently removes your account, chats, documents and analyses from our database. Signing out only clears data stored in this browser. Copies may remain in provider backups for a limited time, and text already sent to the AI provider is handled under that provider's own policy.</p>`;
  $('#v-terms').innerHTML=`<h1>Terms of Use</h1><p class="sub">Last updated 28 October 2026.</p>
<h2>Use of the service</h2><p>Ascendra provides interview practice and resume feedback. Do not upload documents you have no right to share, or anyone else's personal data without permission.</p>
<h2>Your account</h2><p>Keep your password private. You can delete your account at any time in Settings.</p>
<h2>No guarantees</h2><p>Feedback is AI generated and can be wrong. It does not promise an interview or a job offer.</p>
<h2>Your content</h2><p>You keep ownership of what you upload and allow us to process it to run the service.</p>
<h2>Changes</h2><p>We may update these terms and will change the date above when we do.</p>${em}`}
async function start(){
  try{LG=await api('/api/config',{noauth:true});renderLegal();$('#dot').className='dot ok';$('#stxt').textContent='Server connected';if(!window._g)initGoogle()}catch{$('#dot').className='dot';$('#stxt').textContent='Server not reachable'}
  renderSample();if(tok)await boot2();else showLand(true);if(rtok){showLand(true);openAuth('reset')}}
applyTheme();render();drawBank();renderLegal();show('home');start();window.addEventListener('load',initGoogle);
if('serviceWorker' in navigator){const had=!!navigator.serviceWorker.controller;let rl=false;
  navigator.serviceWorker.register('sw.js',{updateViaCache:'none'}).then(r=>r.update()).catch(()=>{});
  navigator.serviceWorker.addEventListener('controllerchange',()=>{if(had&&!rl){rl=true;location.reload()}})}