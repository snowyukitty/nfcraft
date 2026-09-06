'use strict';

/** Inventory and review UI. Authority and export selection stay on the server. */
class CardLibrary {
  constructor({getState, json, api, notify, escapeHtml}) {
    Object.assign(this, {getState, json, api, notify, esc:escapeHtml});
    this.offset=0; this.limit=25; this.request=0; this.signature=''; this.tableMarkup='';
    this.fields=['name','headline','bio','email','website'];
    this.$=selector=>document.querySelector(selector);
    for(const id of ['inventory-batch','inventory-status','inventory-route'])this.$('#'+id).onchange=()=>this.changed();
    this.$('#inventory-search').oninput=()=>{clearTimeout(this.searchTimer);this.searchTimer=setTimeout(()=>this.changed(),180);};
    this.$('#clear-filters').onclick=()=>this.clear();
    this.$('#filter-all').onclick=()=>this.clear();
    this.$('#filter-review').onclick=()=>this.quick('quarantined');
    this.$('#filter-verified').onclick=()=>this.quick('verified');
    this.$('#inventory-prev').onclick=()=>{this.offset=Math.max(0,this.offset-this.limit);this.load();};
    this.$('#inventory-next').onclick=()=>{this.offset+=this.limit;this.load();};
    this.$('#profile-form').addEventListener('input',()=>this.preview());
    this.$('#discard-profile').onclick=()=>{if(this.savedProfile)this.saved(this.savedProfile);};
    this.$('#publication-refresh').onclick=()=>this.review().catch(e=>this.notify(e.message,true));
    this.$('#publication-download').onclick=()=>this.exportReviewed();
    this.previewReady=import('/public-card.mjs').then(module=>{
      this.publicView=module;
      this.shadow=this.$('#recipient-preview').attachShadow({mode:'open'});
      const style=new CSSStyleSheet();style.replaceSync(module.PUBLIC_CSS);
      this.shadow.adoptedStyleSheets=[style];this.preview();
    }).catch(()=>this.notify('The recipient preview could not load. Restart the app and try again.',true));
  }

  filters() {return {q:this.$('#inventory-search').value,batch:this.$('#inventory-batch').value,
    status:this.$('#inventory-status').value,route:this.$('#inventory-route').value};}
  query() {return new URLSearchParams(this.filters()).toString();}
  card(id) {return this.page?.cards.find(card=>card.id===id) || this.getState()?.cards.find(card=>card.id===id);}
  changed() {this.offset=0;this.signature='';this.load();}
  clear() {for(const id of ['inventory-search','inventory-batch','inventory-status','inventory-route'])this.$('#'+id).value='';this.changed();}
  quick(status) {
    for(const id of ['inventory-search','inventory-batch','inventory-route'])this.$('#'+id).value='';
    this.$('#inventory-status').value=status;this.changed();
  }

  render(state) {
    const batchSelect=this.$('#inventory-batch');
    const options='<option value="">All batches</option>'+state.batches.map(b=>`<option value="${this.esc(b.id)}">${this.esc(b.name)}</option>`).join('');
    if(this.batchOptions!==options){const value=batchSelect.value;batchSelect.innerHTML=options;batchSelect.value=value;this.batchOptions=options;}
    this.$('#count-all').textContent=state.cards.length;
    this.$('#count-review').textContent=state.cards.filter(c=>c.status==='quarantined').length;
    this.$('#count-verified').textContent=state.cards.filter(c=>c.status==='verified').length;
    const signature=JSON.stringify([this.filters(),state.cards.map(c=>[c.id,c.status,c.route_state,c.revision,c.last_error])]);
    if(signature!==this.signature){this.signature=signature;this.load();}
    const profile=state.profiles[0];
    if(profile && (!this.savedProfile || profile.revision!==this.savedProfile.revision)){
      const dirty=this.dirty();this.savedProfile=profile;if(!dirty)this.fill(profile);
    }
    this.preview();
    if(this.detailId && this.$('#card-dialog').open)this.renderDetails();
  }

  async load() {
    const request=++this.request;
    this.$('#inventory-body').setAttribute('aria-busy','true');
    this.$('#inventory-count').textContent='Finding matching cards…';
    for(const id of ['export-csv','export-manifest','inventory-prev','inventory-next'])this.$('#'+id).disabled=true;
    const filters=this.filters();
    for(const [id,status] of [['filter-all',''],['filter-review','quarantined'],['filter-verified','verified']])
      this.$('#'+id).setAttribute('aria-pressed',String(filters.status===status));
    try {
      const page=await this.json(`inventory?${this.query()}&offset=${this.offset}&limit=${this.limit}`);
      if(request!==this.request)return;
      this.offset=page.offset;this.page=page;
      const body=this.$('#inventory-body'), demo=this.getState()?.mode==='demo';
      const html=page.cards.length?page.cards.map(c=>`<tr>
        <td><button class="card-label" data-action="details" data-id="${this.esc(c.id)}">${this.esc(c.batch_name)} / ${String(c.ordinal).padStart(4,'0')}</button><small>${demo?'Simulated card':'Physical workspace'}</small></td>
        <td class="url">${this.esc(c.url)}</td><td><span class="status-badge ${this.esc(c.status)}">${this.esc(c.status)}</span>${c.last_error?`<small>${this.esc(c.last_error)}</small>`:''}</td>
        <td>${this.esc(c.route_state)}<small>Local intent only</small></td><td><div class="actions">
        ${c.status==='verified'?`<button data-action="copy" data-id="${c.id}">Copy URL</button><button data-action="qr" data-id="${c.id}">QR SVG</button><button data-action="route" data-id="${c.id}">${c.route_state==='enabled'?'Suspend':'Enable'}</button>`:''}
        ${c.status==='quarantined'?`<button data-action="recover" data-id="${c.id}">Review & recover</button>`:''}
        ${demo?`<button data-action="present" data-id="${c.id}">Present again</button>`:''}</div></td></tr>`).join(''):
        `<tr><td colspan="5" class="library-empty"><strong>${page.total?'No cards match these filters.':'Your card library starts here.'}</strong><p>${page.total?'Clear a filter or try a batch name, label, URL or UID.':'Create a batch in the workbench. Every reserved identity will appear here, including cards that need review.'}</p></td></tr>`;
      if(this.tableMarkup!==html){
        const focused=body.contains(document.activeElement)?{...document.activeElement.dataset}:null;
        body.innerHTML=html;this.tableMarkup=html;
        if(focused?.id)Array.from(body.querySelectorAll('button')).find(b=>b.dataset.id===focused.id && b.dataset.action===focused.action)?.focus();
      }
      this.$('#inventory-count').textContent=`${page.matched} matching ${page.matched===1?'card':'cards'} · ${page.total} total`;
      this.$('#inventory-page').textContent=page.matched?`Showing ${page.offset+1}–${page.offset+page.cards.length} of ${page.matched}`:'No rows to show';
      this.$('#inventory-prev').disabled=page.offset===0;
      this.$('#inventory-next').disabled=page.offset+page.cards.length>=page.matched;
      this.$('#export-csv').disabled=!page.matched;
      this.$('#export-manifest').disabled=false;
      this.$('#export-csv').textContent=`Export ${page.matched} matching CSV`;
    } catch(error) {
      if(request!==this.request)return;
      this.signature='';this.$('#inventory-count').textContent='Inventory could not load. Retrying when connected.';
      this.notify(error.message,true);
    } finally {if(request===this.request)this.$('#inventory-body').setAttribute('aria-busy','false');}
  }

  formProfile() {return Object.fromEntries(this.fields.map(k=>[k,this.$('#profile-form').elements[k].value]));}
  dirty() {return Boolean(this.savedProfile && this.fields.some(k=>this.formProfile()[k].trim()!==this.savedProfile[k]));}
  fill(profile) {for(const key of this.fields)this.$('#profile-form').elements[key].value=profile[key];}
  saved(profile) {this.savedProfile=profile;this.fill(profile);this.preview();}
  preview() {
    const profile=this.formProfile(), dirty=this.dirty();
    this.$('#draft-state').textContent=dirty?'UNSAVED CHANGES':'SAVED LOCALLY';
    this.$('#draft-state').classList.toggle('unsaved',dirty);
    this.$('#discard-profile').disabled=!dirty;
    const signature=JSON.stringify(profile);
    if(this.shadow && signature!==this.previewSignature){
      this.shadow.innerHTML=this.publicView.renderCardMarkup(profile,'',{preview:true});this.previewSignature=signature;
    }
  }

  details(id) {this.detailId=id;this.detailSignature='';this.renderDetails();this.$('#card-dialog').showModal();}
  renderDetails() {
    const state=this.getState(), c=this.card(this.detailId);if(!c)return;
    const signature=JSON.stringify(c);if(signature===this.detailSignature)return;this.detailSignature=signature;
    this.$('#card-detail-title').textContent=`${c.batch_name} / ${String(c.ordinal).padStart(4,'0')}`;
    const verified=c.status==='verified', demo=state.mode==='demo';
    this.$('#card-detail-body').innerHTML=`<p class="detail-url">${this.esc(c.url)}</p>
      <div class="lifecycle"><div><span>01 · WRITE & READ BACK</span><strong>${demo?'Simulated · ':''}${this.esc(c.status)}</strong><p>${verified?'Target bytes and preserved memory checked.':'This identity stays reserved. It cannot be reassigned.'}</p></div>
      <div><span>02 · PUBLIC EXPORT</span><strong>${verified?'Available for review':'Excluded from exports'}</strong><p>${verified?'Route intent: '+this.esc(c.route_state)+'. Export and publication are separate.':'Recover the original card before publishing this route.'}</p></div>
      <div><span>03 · PUBLIC AVAILABILITY</span><strong>Not checked</strong><p>No deployment or remote availability receipt is recorded.</p></div>
      <div><span>04 · PHONE & PRINT QA</span><strong>Not recorded</strong><p>Verify the final physical card and QR before distribution.</p></div></div>
      ${c.status==='quarantined'?'<div class="callout">Keep this original card and identity. Close this view and use Review & recover for the separately approved recovery.</div>':''}
      <details class="technical-details"><summary>Local identity & verification evidence</summary><dl><dt>UID · private</dt><dd>${this.esc(c.uid)}</dd><dt>Card ID</dt><dd>${this.esc(c.id)}</dd><dt>Verified at</dt><dd>${this.esc(c.verified_at||'Not verified')}</dd><dt>Payload SHA-256</dt><dd>${this.esc(c.payload_sha256||'Not available')}</dd><dt>Last error</dt><dd>${this.esc(c.last_error||'None recorded')}</dd></dl></details>`;
  }

  async review() {
    const filters=this.filters();
    this.reviewed=await this.json('publication/review',{filters});
    const r=this.reviewed,m=r.manifest;
    this.$('#publication-error').textContent='';
    this.$('#publication-download').disabled=!m.routes.length;
    this.$('#publication-body').innerHTML=`<div class="review-banner">${m.simulated?'SIMULATED · for local or disposable preview only':'PHYSICAL WORKSPACE · independent hardware/phone QA still required'}</div>
      <div class="review-counts"><div><strong>${r.enabled}</strong><span>Enabled routes</span></div><div><strong>${r.suspended}</strong><span>Suspension updates</span></div><div><strong>${r.excluded}</strong><span>Unverified matches excluded</span></div></div>
      <h3>Encoded destinations</h3><p class="review-origins">${r.origins.length?r.origins.map(this.esc).join('<br>'):'No verified routes match this selection.'}</p>
      <p class="field-help">Origins come from existing card URLs. Ownership, cloud destination and public availability are not verified.</p>
      <h3>Public content included in this file</h3>${m.profiles.map(p=>`<section class="review-profile"><strong>${this.esc(p.name)}</strong><span>Profile revision ${p.revision}</span><p>${this.esc(p.headline)}</p><p>${this.esc(p.bio)}</p><dl><dt>Public email</dt><dd>${this.esc(p.email||'Not set')}</dd><dt>Website</dt><dd>${this.esc(p.website||'Not set')}</dd></dl></section>`).join('')}
      <div class="callout">Profiles are shared. ${r.other_local_routes_sharing_profiles} other locally verified cards use the included profiles. Importing a changed profile updates every public route using it, including routes outside this selection. The public database may contain additional routes.</div>
      ${this.dirty()?'<div class="callout">You have unsaved profile changes. This export contains the saved draft shown above. Save your changes and review again to include them.</div>':''}
      <details class="technical-details"><summary>Exact routes and export checksum</summary><p class="checksum">${this.esc(m.sha256)}</p><ul class="review-routes">${m.routes.map(row=>`<li>${this.esc(row.url)}<small>${this.esc(row.state)} · revision ${row.revision}</small></li>`).join('')}</ul></details>
      <p class="footnote">${r.matched} matching cards across all pages. Raw UIDs, memory snapshots and operator credentials are excluded. Omitted routes are not deleted from a public database.</p>`;
    if(!this.$('#publication-dialog').open)this.$('#publication-dialog').showModal();
  }

  async exportReviewed() {
    if(!this.reviewed)return;
    const button=this.$('#publication-download');button.disabled=true;
    try {
      const response=await this.api('publication/export',{filters:this.reviewed.filters,sha256:this.reviewed.manifest.sha256});
      const blob=await response.blob(), url=URL.createObjectURL(blob), link=document.createElement('a');
      link.href=url;link.download='routes-manifest.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      this.$('#publication-dialog').close();this.notify('Reviewed file downloaded. Nothing was deployed.');
    } catch(error) {this.$('#publication-error').textContent=error.message;}
    finally {button.disabled=!this.reviewed?.manifest.routes.length;}
  }
}
