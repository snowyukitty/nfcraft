'use strict';
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const escapeHtml = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let token = location.hash.slice(1) || sessionStorage.getItem('nfc-operator-token') || '';
if (location.hash.length > 1) { sessionStorage.setItem('nfc-operator-token', token); history.replaceState(null, '', '/'); }
let state = null, selected = localStorage.getItem('nfc-selected-batch') || '', profileLoaded = false, polling = false, toastTimer;
const titles = {
  workbench: ['WORKBENCH','From a blank card<br>to a lasting connection.','Prepare the batch. Place a card. Let the workbench take care of the details.'],
  inventory: ['CARD INVENTORY','Small cards.<br>A clear record.','One durable identity for each card. Every uncertain result stays visible.'],
  profile: ['PUBLIC PROFILE','An introduction<br>that grows with you.','The card holds a URL. Your story lives behind it.'],
  activity: ['ACTIVITY & AUDIT','No guesswork.<br>No missing steps.','A durable local journal, from reservation to verified readback.'],
  devices: ['READER & AGENTS','A simple station.<br>A carefully bounded system.','The model plans. The reader writes. You remain in control.']
};
function notify(message, error=false) { clearTimeout(toastTimer); $('#toast').textContent=message; $('#toast').className=error?'show error':'show'; toastTimer=setTimeout(()=>$('#toast').className='',6000); }
async function api(path, body) {
  const headers = {'Authorization': 'Bearer '+token};
  if (body !== undefined) headers['Content-Type']='application/json';
  const r = await fetch('/api/'+path, {method:body===undefined?'GET':'POST',headers,body:body===undefined?undefined:JSON.stringify(body)});
  if (!r.ok) { let d; try {d=await r.json();} catch {throw Error('The local app did not respond.');} throw Error(d.error?.message || 'Operation failed.'); }
  return r;
}
async function json(path,body) { return (await api(path,body)).json(); }
function changeView(view) {
  if (!titles[view]) return;
  $$('.view').forEach(e=>e.classList.toggle('hidden',e.id!=='view-'+view));
  $$('.nav').forEach(e=>e.classList.toggle('active',e.dataset.view===view));
  $('#page-name').textContent=titles[view][0]; $('#page-heading').innerHTML=titles[view][1]; $('#page-subtitle').textContent=titles[view][2];
}
function batch() { return state?.batches.find(b=>b.id===selected); }
function render() {
  const s=state, demo=s.mode==='demo';
  $('#connection').textContent='● Connected locally';
  $('#mode-banner').classList.toggle('hardware',!demo);
  $('#mode-title').textContent=demo?'Simulation workspace':'Experimental hardware workspace';
  $('#mode-description').textContent=demo?'No physical cards are being written.':s.writes_enabled?'Real writes enabled by launch flag. Hardware is NOT qualified.':'Read-only. Physical writing is disabled.';
  $('#simulator').classList.toggle('hidden',!demo);
  $('#nav-count').textContent=s.cards.length;
  $('#m-verified').textContent=s.cards.filter(c=>c.status==='verified').length;
  $('#m-reserved').textContent=s.cards.length;
  $('#m-review').textContent=s.cards.filter(c=>c.status==='quarantined').length;
  const oldOptions = [...$('#batch-select').options].map(o=>o.value).join(',');
  if (oldOptions !== s.batches.map(b=>b.id).join(',')) {
    $('#batch-select').innerHTML=s.batches.length?s.batches.map(b=>`<option value="${escapeHtml(b.id)}">${escapeHtml(b.name)}</option>`).join(''):'<option value="">Create your first batch</option>';
  }
  if (!s.batches.some(b=>b.id===selected)) selected=s.batches[0]?.id || '';
  $('#batch-select').value=selected;
  $('#batch-select').disabled=Boolean(s.armed);
  const b=batch(), percent=b?Math.round(b.verified/b.target*100):0;
  $('#batch-progress-text').textContent=b?`${b.verified} of ${b.target} verified`:'0 of 0 verified';
  $('#batch-percent').textContent=percent+'%'; $('#batch-progress').value=percent;
  $('#batch-base').textContent=b?.base || 'Not set';
  $('#arm-button').disabled=!b || Boolean(s.armed) || !s.writes_enabled || (b.allocated>=b.target);
  $('#arm-button').textContent=s.armed?'Run is armed':b?.allocated>=b?.target?'All identities allocated':'Arm this batch';
  $('#lease-status').textContent=s.armed?`${s.armed.remaining_attempts} attempts left · ${s.armed.seconds_remaining}s until disarmed`:'Writes are off until you approve a run.';
  $('#reader-label').textContent=s.reader; $('#device-name').textContent=s.reader;
  $('#phase-chip').textContent=s.phase.toUpperCase(); $('#phase-chip').className='chip '+s.phase;
  const phaseTitles={idle:'Ready when you are.',ready:'Place one card.',inspecting:'Checking the tag.',writing:'Writing your introduction.',verifying:'Reading it back.',remove:'Verified. One card closer.',paused:'A moment to pause.',attention:'This card needs attention.'};
  $('#station-title').textContent=phaseTitles[s.phase]||s.phase;
  $('#station-message').textContent=s.message;
  $('#card-name').textContent=s.profiles[0]?.name || 'Your name';
  if (s.last) {
    const r=s.last;
    $('#latest-result').className='result'+(r.ok?'':' error');
    $('#latest-result').innerHTML=`<span class="result-mark">${r.ok?'✓':'!'}</span><div><strong>${r.ok?escapeHtml(r.batch_name)+' / '+String(r.ordinal).padStart(4,'0'):escapeHtml(r.code)}</strong><p>${escapeHtml(r.ok?r.url:r.message)}</p></div>${r.ok?`<span class="elapsed">${r.simulated?'SIMULATED · ':''}${r.elapsed_ms} ms<br>NOT PUBLISHED</span>`:''}`;
  }
  $('#inventory-body').innerHTML=s.cards.length?s.cards.map(c=>`<tr><td><b>${escapeHtml(c.batch_name)} / ${String(c.ordinal).padStart(4,'0')}</b><small>${escapeHtml(c.uid)}</small></td><td class="url">${escapeHtml(c.url)}</td><td><span class="status-badge ${escapeHtml(c.status)}">${escapeHtml(c.status)}</span>${c.last_error?`<small>${escapeHtml(c.last_error)}</small>`:''}</td><td>${escapeHtml(c.route_state)}<small>Local intent only</small></td><td><div class="actions">${c.status==='verified'?`<button data-action="copy" data-id="${c.id}">Copy URL</button><button data-action="qr" data-id="${c.id}">QR SVG</button><button data-action="route" data-id="${c.id}">${c.route_state==='enabled'?'Suspend':'Enable'}</button>`:''}${c.status==='quarantined'?`<button data-action="recover" data-id="${c.id}">Review & recover</button>`:''}${demo?`<button data-action="present" data-id="${c.id}">Present again</button>`:''}</div></td></tr>`).join(''):'<tr><td colspan="5" class="empty-state">No assignments yet. Create a batch in the workbench.</td></tr>';
  if (!profileLoaded && s.profiles[0]) { for (const k of ['name','headline','bio','email','website']) $('#profile-form').elements[k].value=s.profiles[0][k]; profileLoaded=true; }
  $('#audit-status').textContent=s.audit.ok?`Audit chain intact · ${s.audit.count} recorded events`:`Audit check failed near event ${s.audit.bad_seq}. Stop and investigate.`;
  $('#events').innerHTML=s.events.length?s.events.map(e=>`<div class="event-row"><time>${escapeHtml(new Date(e.at).toLocaleString())}</time><b>${escapeHtml(e.kind.replaceAll('_',' '))}</b><code>${escapeHtml(e.data)}</code></div>`).join(''):'<p>No events yet.</p>';
}
async function refresh() {
  if(polling) return;
  polling=true;
  try {state=await json('state');render();} catch(e) {$('#connection').textContent='○ Disconnected'; if(!state)notify(e.message,true);} finally {polling=false;}
}
async function action(fn) {try {await fn();await refresh();} catch(e){notify(e.message,true);}}
async function download(path,name) {const blob=await (await api(path)).blob();const href=URL.createObjectURL(blob);const a=document.createElement('a');a.href=href;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(href),1000);}
function openArm(recover=null) {
  const b=batch(); if(!b)return notify('Create a batch first.',true);
  $('#recover-uid').value=recover || '';
  $('#arm-summary').textContent=`${b.name} · ${recover?'Recover one reserved identity':b.target-b.allocated+' remaining new cards'} · ${b.base}`;
  $('#confirm-label').firstChild.textContent=`Type ARM ${b.name}`;
  $('#arm-confirmation').value=''; $('#arm-confirmation').placeholder=`ARM ${b.name}`;
  $('#arm-dialog').showModal(); $('#arm-confirmation').focus();
}
$$('.nav').forEach(b=>b.addEventListener('click',()=>changeView(b.dataset.view)));
$$('[data-goto]').forEach(b=>b.addEventListener('click',()=>changeView(b.dataset.goto)));
$$('[data-close]').forEach(b=>b.addEventListener('click',()=>$('#'+b.dataset.close).close()));
$('#new-batch').onclick=()=>{if(state?.mode==='hardware')$('#batch-form').elements.base.value='';$('#batch-dialog').showModal();};
$('#batch-form').onsubmit=e=>{e.preventDefault();action(async()=>{const data=Object.fromEntries(new FormData(e.target));data.target=Number(data.target);const created=await json('batches',data);selected=created.id;localStorage.setItem('nfc-selected-batch',selected);$('#batch-dialog').close();notify('Draft batch created. No cards written.');});};
$('#batch-select').onchange=e=>{selected=e.target.value;localStorage.setItem('nfc-selected-batch',selected);render();};
$('#arm-button').onclick=()=>openArm();
$('#arm-form').onsubmit=e=>{e.preventDefault();action(async()=>{const b=batch(), uid=$('#recover-uid').value;if(uid && state.mode==='demo'){await json('mock/remove',{});await json('mock/insert',{uid});await json('mock/clear-fault',{});}await json('arm',{batch_id:b.id,confirmation:$('#arm-confirmation').value,limit:uid?1:Math.max(1,b.target-b.allocated),seconds:600,recover_uid:uid||null});$('#arm-dialog').close();changeView('workbench');notify('Run armed. Only the approved batch can be written.');});};
$('#pause-top').onclick=()=>action(()=>json('pause',{}));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!document.querySelector('dialog[open]')) action(()=>json('pause',{}));});
$('#insert-card').onclick=()=>action(async()=>{await json('mock/insert',{scenario:$('#scenario').value});notify('Virtual card presented.');});
$('#remove-card').onclick=()=>action(()=>json('mock/remove',{}));
$('#inspect-button').onclick=()=>action(async()=>{const d=await json('inspect',{});$('#inspection-output').textContent=JSON.stringify(d,null,2);$('#inspect-dialog').showModal();});
$('#export-csv').onclick=()=>action(()=>download('inventory.csv','nfc-inventory.csv'));
$('#export-manifest').onclick=()=>action(()=>download('manifest','routes-manifest.json'));
$('#profile-form').onsubmit=e=>{e.preventDefault();action(async()=>{await json('profile',Object.fromEntries(new FormData(e.target)));notify('Profile draft saved locally. Export and deploy to publish.');});};
$('#backup-button').onclick=()=>action(async()=>{const d=await json('backup',{});notify('Saved: '+d.saved_to);});
$('#inventory-body').onclick=e=>{const button=e.target.closest('button[data-action]');if(!button)return;const c=state.cards.find(c=>c.id===button.dataset.id);if(!c)return;action(async()=>{
  switch(button.dataset.action){
    case 'copy': await navigator.clipboard.writeText(c.url);notify('Card URL copied.');break;
    case 'qr': await download('qr?id='+encodeURIComponent(c.id),`${c.id}.svg`);break;
    case 'route': await json('route',{card_id:c.id,state:c.route_state==='enabled'?'suspended':'enabled'});notify('Local route intent changed. Export and deploy to apply publicly.');break;
    case 'present': await json('mock/remove',{});await json('mock/insert',{uid:c.uid});notify('Previously assigned virtual card presented.');break;
    case 'recover': selected=c.batch_id;render();openArm(c.uid);break;
  }
});};
refresh();setInterval(refresh,1200);
