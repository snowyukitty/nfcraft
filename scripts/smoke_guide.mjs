/** Verify the bundled offline guide in isolated Edge, without an app capability. */
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const {chromium}=require(path.join(root,'.local/browser/node_modules/playwright'));
const out=path.join(root,'.local/evidence/guide');mkdirSync(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
try {
  const page=await browser.newPage();const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const file=process.argv.includes('--packaged')?'dist/nfcraft/_internal/nfcraft/web/guide.html':'nfcraft/web/guide.html';
  for (const width of [1440,375]) {
    await page.setViewportSize({width,height:1000});
    await page.goto(pathToFileURL(path.join(root,file)).href);
    for (const language of ['en','zh-Hant']) {
      await page.locator(`[data-language="${language}"]`).click();
      assert.equal(await page.locator('html').getAttribute('lang'),language);
      assert.equal(await page.locator('article:visible').count(),1);
      assert.equal(await page.locator('article:visible .steps li').count(),3);
      await page.locator('article:visible .button').click();
      await page.locator('article:visible details').nth(1).locator('summary').click();
      assert.equal(await page.locator('article:visible details').nth(1).getAttribute('open'),'');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      assert.equal(await page.locator('img').evaluateAll(images=>images.every(image=>image.complete&&image.naturalWidth>0)),true);
      await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
      await page.screenshot({path:path.join(out,`${process.argv.includes('--packaged')?'packaged':'source'}-${language}-${width}.png`),fullPage:true});
    }
  }
  assert.deepEqual(errors,[]);
  if (process.argv.includes('--icon-review')) {
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(pathToFileURL(path.join(root,'work/nfcraft/review.html')).href);
    await page.screenshot({path:path.join(out,'icon-review-lab.png'),fullPage:true});
    console.log(await page.locator('body').innerText());
  }
  writeFileSync(path.join(out,process.argv.includes('--packaged')?'packaged-summary.json':'summary.json'),JSON.stringify({status:'PASS',widths:[1440,375],languages:['en','zh-Hant'],checks:['offline assets','language switch','start anchors','FAQ interaction','no overflow','no page errors']},null,2));
  console.log('PASS: bilingual offline guide, desktop/mobile, both languages.');
} finally {await browser.close();}
