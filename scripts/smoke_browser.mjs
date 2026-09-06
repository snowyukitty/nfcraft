/** Isolated Chromium acceptance. Only self-created disposable demo workspaces. */
import {spawn, spawnSync} from 'node:child_process';
import {cpSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
const {chromium} = require(path.join(root, '.local/browser/node_modules/playwright'));
const evidence = path.join(root, '.local/evidence');
mkdirSync(evidence, {recursive:true});
const workspace = mkdtempSync(path.join(evidence, 'browser space 測試-'));
const python = path.join(root, '.venv/Scripts/python.exe');
const packaged = process.argv.includes('--packaged');
if(packaged)cpSync(path.join(root,'dist/nfcraft'),path.join(workspace,'portable app 測試'),{recursive:true});
const checks = [], errors = [];
let proc, browser;
async function start() {
  proc = spawn(packaged?path.join(workspace,'portable app 測試/nfcraft.exe'):python,
    [...(packaged?[]:['run.py']),'--mode','demo','--data-dir',workspace,'--port','0','--no-browser'],
    {cwd:root, windowsHide:true, stdio:['ignore','pipe','pipe']});
  // Only the synthetic daemon's capability enters the isolated browser; never logged.
  return await new Promise((resolve,reject)=>{
    let output='';
    const timer=setTimeout(()=>reject(Error('Demo startup timeout')),15000);
    proc.stdout.on('data',chunk=>{output+=chunk.toString('utf8');const match=output.match(/Operator app: (http:\/\/127\.0\.0\.1:\d+\/#\S+)/);if(match){clearTimeout(timer);resolve(match[1]);}});
    proc.on('exit',()=>{clearTimeout(timer);reject(Error('Demo exited during startup'));});
  });
}
async function stop() {
  if(!proc || proc.exitCode!==null)return;
  const done = new Promise(resolve=>proc.once('exit',resolve));
  if(process.platform==='win32')spawnSync('taskkill',['/PID',String(proc.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});
  else proc.kill();
  await done;
}
try {
  const url=await start();
  browser=await chromium.launch({channel:'msedge',headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url);
  await page.locator('#connection').filter({hasText:'Connected locally'}).waitFor();
  assert(!page.url().includes('#'));
  checks.push('startup; operator fragment removed');
  await page.locator('#new-batch').click();
  await page.locator('#batch-form [name=name]').fill('Browser pilot');
  await page.locator('#batch-form [name=target]').fill('10');
  await page.getByRole('button',{name:'Create draft batch',exact:true}).click();
  await page.locator('#batch-dialog').waitFor({state:'hidden'});
  assert.equal(await page.locator('#m-reserved').innerText(),'0');
  async function arm(name='Browser pilot', seconds='600', limit=null) {
    await page.locator('#arm-button').click();
    await page.locator('#arm-seconds').fill(seconds);
    if(limit)await page.locator('#arm-limit').fill(limit);
    await page.locator('#arm-confirmation').fill('ARM '+name);
    await page.getByRole('button',{name:'Approve and arm',exact:true}).click();
    await page.locator('#arm-dialog').waitFor({state:'hidden'});
  }
  await arm();
  for(let i=1;i<=10;i++){
    await page.locator('#insert-card').click();
    await page.waitForFunction(n=>document.querySelector('#m-verified').textContent===String(n),i);
    if(i===1){
      await page.locator('#inspect-button').click();
      await page.locator('#inspection-output').filter({hasText:'safe_to_provision'}).waitFor();
      assert.equal(await page.locator('#m-reserved').innerText(),'1');
      await page.locator('[data-close=inspect-dialog]').click();
    }
    await page.locator('#remove-card').click();
  }
  checks.push('draft has zero writes; bounded ten distinct simulated cards; held card inspection');
  await page.screenshot({path:path.join(workspace,'workbench.png'),fullPage:true});
  await page.locator('[data-view=inventory]').click();
  assert.equal(await page.locator('#inventory-body tr').count(),10);
  const urls=await page.locator('#inventory-body .url').allTextContents();
  assert.equal(new Set(urls).size,10);
  for(const [id,file] of [['export-manifest','routes.json'],['export-csv','inventory.csv']]){
    const download=page.waitForEvent('download');await page.locator('#'+id).click();
    if(id==='export-manifest')await page.locator('#publication-download').click();
    await(await download).saveAs(path.join(workspace,file));
  }
  const manifest=JSON.parse(readFileSync(path.join(workspace,'routes.json'),'utf8'));
  assert.equal(manifest.routes.length,10);assert.equal(manifest.simulated,true);
  assert(!JSON.stringify(manifest).includes('"uid"'));
  const qr=page.waitForEvent('download');await page.getByRole('button',{name:'QR SVG',exact:true}).first().click();await(await qr).saveAs(path.join(workspace,'card.svg'));
  checks.push('unique URLs; CSV, public manifest without UID, QR SVG downloads');
  // A new approved batch must refuse a previously assigned card.
  await page.locator('#new-batch').click();
  await page.locator('#batch-form [name=name]').fill('Recovery pilot');
  await page.locator('#batch-form [name=target]').fill('2');
  await page.getByRole('button',{name:'Create draft batch',exact:true}).click();
  await page.locator('#batch-dialog').waitFor({state:'hidden'});
  await page.locator('[data-view=workbench]').click();await arm('Recovery pilot');
  await page.locator('[data-view=inventory]').click();
  await page.getByRole('button',{name:'Present again',exact:true}).first().click();
  await page.waitForFunction(()=>document.querySelector('#phase-chip').textContent==='ATTENTION');
  assert.equal(await page.locator('#m-reserved').innerText(),'10');
  checks.push('duplicate refused without new identity');
  await page.locator('[data-view=workbench]').click();await page.locator('#remove-card').click();
  for(const scenario of ['foreign','locked','ntag213']){
    await arm('Recovery pilot');await page.locator('#scenario').selectOption(scenario);await page.locator('#insert-card').click();
    await page.waitForFunction(()=>document.querySelector('#phase-chip').textContent==='ATTENTION');
    assert.equal(await page.locator('#m-reserved').innerText(),'10');await page.locator('#remove-card').click();
  }
  checks.push('foreign data, locked card, wrong chip refused without reservation');
  await arm('Recovery pilot','15','1');
  await page.waitForFunction(()=>document.querySelector('#station-message').textContent.includes('Arming window ended'),null,{timeout:20000});
  assert.equal(await page.locator('#m-reserved').innerText(),'10');
  checks.push('operator-selected attempt cap and 15-second expiry; no writes after expiry');
  await arm('Recovery pilot');await page.locator('#scenario').selectOption('interrupted');await page.locator('#insert-card').click();
  await page.waitForFunction(()=>document.querySelector('#m-review').textContent==='1');
  await page.locator('[data-view=inventory]').click();
  const uncertain=await page.locator('#inventory-body tr').filter({hasText:'quarantined'}).locator('.url').innerText();
  await page.getByRole('button',{name:'Review & recover',exact:true}).click();
  assert.equal(await page.locator('#arm-limit').inputValue(),'1');
  assert(await page.locator('#arm-limit').evaluate(element=>element.readOnly));
  await page.locator('#arm-confirmation').fill('ARM Recovery pilot');
  await page.getByRole('button',{name:'Approve and arm',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#m-verified').textContent==='11');
  await page.locator('[data-view=inventory]').click();
  assert((await page.locator('#inventory-body .url').allTextContents()).includes(uncertain));
  checks.push('interruption quarantines; explicit recovery preserves original URL');
  await page.locator('[data-view=profile]').click();
  await page.locator('#profile-form [name=name]').fill('Local browser 測試');
  await page.getByRole('button',{name:'Save profile draft',exact:true}).click();
  await page.locator('#toast').filter({hasText:'Profile draft saved locally'}).waitFor();
  await page.locator('[data-view=activity]').click();await page.locator('#backup-button').click();
  await page.locator('#toast').filter({hasText:'Saved:'}).waitFor();
  checks.push('Unicode profile draft; journal backup');
  await page.locator('[data-view=workbench]').click();await page.locator('#remove-card').click();await arm('Recovery pilot');
  await stop();
  const restarted=await start();await page.goto(restarted);
  await page.waitForFunction(()=>document.querySelector('#m-verified').textContent==='11');
  assert.equal(await page.locator('#arm-button').innerText(),'Arm this batch');
  assert.equal(await page.locator('#card-name').innerText(),'Local browser 測試');
  checks.push('restart preserves inventory/profile and does not re-arm');
  await page.locator('[data-view=inventory]').click();
  await page.screenshot({path:path.join(workspace,'inventory.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  const summary={result:'PASS',scope:'isolated Edge; disposable mock-only workspace',packaged,checks,physical_nfc:'NOT_RUN'};
  writeFileSync(path.join(workspace,'summary.json'),JSON.stringify(summary,null,2));
  console.log(JSON.stringify(summary,null,2));console.log('Evidence:',path.relative(root,workspace));
} finally {if(browser)await browser.close();await stop();}
