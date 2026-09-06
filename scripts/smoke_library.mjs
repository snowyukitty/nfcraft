/** Card library and recipient preview acceptance with freshly simulated data only. */
import {spawn,spawnSync} from 'node:child_process';
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const {chromium}=require(path.join(root,'.local/browser/node_modules/playwright'));
const evidence=path.join(root,'.local/evidence');mkdirSync(evidence,{recursive:true});
const workspace=mkdtempSync(path.join(evidence,'library-'));
const python=path.join(root,'.venv/Scripts/python.exe');
const seed=`
import sys
from pathlib import Path
from nfcraft.store import Store
from nfcraft.engine import Engine
from nfcraft.adapters.mock import MockReader
root=Path(sys.argv[1])/'demo'
root.mkdir()
engine=Engine(Store(root/'journal.sqlite3'),MockReader(root/'virtual-tags'))
try:
    engine.store.update_profile({'name':'Robin Chen','headline':'Thoughtful things, made by hand.','bio':'Designer & maker. Building small objects that bring people a little closer.','email':'robin@example.com','website':'https://example.com'})
    for name,count in [('Studio cards',54),('Event cards',2)]:
        engine.reader.remove()
        batch=engine.create_batch({'name':name,'target':count,'base':'https://tap.example.com'})
        engine.arm({'batch_id':batch['id'],'confirmation':'ARM '+name})
        for i in range(count):
            engine.reader.insert('interrupted' if name=='Studio cards' and i==53 else 'blank')
            engine.tick();engine.reader.remove();engine.tick()
finally:
    engine.shutdown()
`;
const seeded=spawnSync(python,['-c',seed,workspace],{cwd:root,windowsHide:true,encoding:'utf8'});
assert.equal(seeded.status,0,'Synthetic library fixture failed');
const packaged=process.argv.includes('--packaged');
const proc=spawn(packaged?path.join(root,'dist/nfcraft/nfcraft.exe'):python,
  [...(packaged?[]:['run.py']),'--mode','demo','--data-dir',workspace,'--port','0','--no-browser'],
  {cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
const checks=[],errors=[];let browser;
try{
  const url=await new Promise((resolve,reject)=>{
    let output='';const timer=setTimeout(()=>reject(Error('Synthetic app startup timeout')),15000);
    proc.stdout.on('data',chunk=>{output+=chunk.toString('utf8');const m=output.match(/Operator app: (http:\/\/127\.0\.0\.1:\d+\/#\S+)/);if(m){clearTimeout(timer);resolve(m[1]);}});
    proc.on('exit',()=>{clearTimeout(timer);reject(Error('Synthetic app startup failed'));});
  });
  browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1080}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error' && /Content Security Policy|Refused to/.test(m.text()))errors.push('CSP rejected required local rendering');});
  await page.goto(url);await page.locator('#connection').filter({hasText:'Connected locally'}).waitFor();
  await page.locator('[data-view=inventory]').click();
  await page.locator('#inventory-page').filter({hasText:'Showing 1–25 of 56'}).waitFor();
  const first=await page.locator('#inventory-body .card-label').allTextContents();assert.equal(first.length,25);
  await page.locator('#inventory-next').click();await page.locator('#inventory-page').filter({hasText:'Showing 26–50 of 56'}).waitFor();
  const second=await page.locator('#inventory-body .card-label').allTextContents();assert(!second.some(label=>first.includes(label)));
  await page.locator('#inventory-next').click();await page.locator('#inventory-page').filter({hasText:'Showing 51–56 of 56'}).waitFor();
  assert(await page.locator('#inventory-next').isDisabled());checks.push('56-card library; bounded 25-row pages without duplicates');
  await page.locator('#filter-review').click();await page.locator('#inventory-count').filter({hasText:'1 matching card ·'}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Review & recover',exact:true}).count(),1);
  await page.locator('#export-manifest').click();await page.locator('#publication-body').filter({hasText:'No verified routes match'}).waitFor();
  assert(await page.locator('#publication-download').isDisabled());await page.locator('[data-close=publication-dialog]').click();
  checks.push('review queue is actionable; unverified-only public export is disabled');
  await page.locator('#clear-filters').click();await page.locator('#inventory-search').fill('not-present');
  await page.getByText('No cards match these filters.',{exact:true}).waitFor();assert(await page.locator('#export-csv').isDisabled());
  await page.locator('#inventory-search').fill('studio cards / 0001');
  await page.locator('#inventory-count').filter({hasText:'1 matching card ·'}).waitFor();
  assert.equal(await page.locator('#inventory-body .card-label').innerText(),'Studio cards / 0001');
  const csv=page.waitForEvent('download');await page.locator('#export-csv').click();await(await csv).saveAs(path.join(workspace,'matching.csv'));
  assert.equal(readFileSync(path.join(workspace,'matching.csv'),'utf8').trim().split(/\r?\n/).length,2);
  await page.locator('#inventory-body .card-label').click();
  await page.locator('#card-detail-body').filter({hasText:'Simulated · verified'}).waitFor();
  assert((await page.locator('#card-detail-body').innerText()).includes('Not checked'));
  await page.screenshot({path:path.join(workspace,'card-details.png'),fullPage:true});
  await page.locator('[data-close=card-dialog]').click();checks.push('case-insensitive label search; matching CSV; separate lifecycle facts');
  await page.locator('#export-manifest').click();await page.locator('#publication-body').filter({hasText:'Robin Chen'}).waitFor();
  assert((await page.locator('#publication-body').innerText()).includes('54 other locally verified cards'));
  await page.screenshot({path:path.join(workspace,'public-review.png'),fullPage:true});
  // A second synthetic operator edits the saved draft after the first reviewed it.
  const editor=await browser.newPage();await editor.goto(url);await editor.locator('#connection').filter({hasText:'Connected locally'}).waitFor();
  await editor.locator('[data-view=profile]').click();await editor.locator('#profile-form [name=name]').fill('Robin Chen — updated');
  await editor.getByRole('button',{name:'Save profile draft',exact:true}).click();
  await editor.locator('#toast').filter({hasText:'Profile draft saved locally'}).waitFor();await editor.close();
  const stale=page.waitForResponse(r=>r.url().endsWith('/api/publication/export'));
  await page.locator('#publication-download').click();assert.equal((await stale).status(),409);
  await page.locator('#publication-error').filter({hasText:'changed since review'}).waitFor();
  await page.locator('#publication-refresh').click();await page.locator('#publication-body').filter({hasText:'Robin Chen — updated'}).waitFor();
  const download=page.waitForEvent('download');await page.locator('#publication-download').click();await(await download).saveAs(path.join(workspace,'reviewed.json'));
  const manifest=JSON.parse(readFileSync(path.join(workspace,'reviewed.json'),'utf8'));
  assert.equal(manifest.routes.length,1);assert.equal(manifest.profiles[0].name,'Robin Chen — updated');assert(!JSON.stringify(manifest).includes('"uid"'));
  checks.push('review freezes public content; changed saved draft refuses stale export; re-review yields exact matching manifest');
  await page.locator('[data-view=profile]').click();
  await page.locator('#profile-form [name=name]').fill('<script>literal only</script> 測試');
  await page.locator('#recipient-preview h1').filter({hasText:'<script>literal only</script> 測試'}).waitFor();
  assert.equal(await page.locator('#recipient-preview script').count(),0);
  assert.equal(await page.locator('#recipient-preview a').count(),0);
  await page.locator('#draft-state').filter({hasText:'UNSAVED CHANGES'}).waitFor();
  await page.locator('#discard-profile').click();
  await page.locator('#recipient-preview h1').filter({hasText:'Robin Chen — updated'}).waitFor();
  await page.screenshot({path:path.join(workspace,'profile-preview.png'),fullPage:true});
  checks.push('live preview safely escapes markup; actions inert; saved/unsaved state and restore');
  await page.locator('[data-view=inventory]').click();await page.locator('#clear-filters').click();
  await page.locator('#inventory-page').filter({hasText:'Showing 1–25 of 56'}).waitFor();
  const focused=page.locator('#inventory-body .card-label').first();await focused.focus();
  await page.waitForResponse(r=>r.url().endsWith('/api/state'));assert(await focused.evaluate(e=>e===document.activeElement));
  await page.screenshot({path:path.join(workspace,'library.png'),fullPage:true});
  await page.setViewportSize({width:760,height:1000});await page.locator('[data-view=profile]').click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(workspace,'profile-narrow.png'),fullPage:true});
  checks.push('polling preserves focused row action; narrow desktop layout fits');
  assert.deepEqual(errors,[]);
  const summary={result:'PASS',scope:'isolated Edge; fresh synthetic library',packaged,checks,physical_nfc:'NOT_RUN',remote_deployment:'NOT_RUN'};
  writeFileSync(path.join(workspace,'summary.json'),JSON.stringify(summary,null,2));
  console.log(JSON.stringify(summary,null,2));console.log('Evidence:',path.relative(root,workspace));
}finally{
  if(browser)await browser.close();
  if(proc.exitCode===null){
    const done=new Promise(resolve=>proc.once('exit',resolve));
    if(process.platform==='win32')spawnSync('taskkill',['/PID',String(proc.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});else proc.kill();
    await done;
  }
}
