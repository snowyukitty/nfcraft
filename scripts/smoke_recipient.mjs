/** Check the actual local Worker page at phone width. No remote destinations. */
import {chromium} from '../.local/browser/node_modules/playwright/index.mjs';
import path from 'node:path';
import assert from 'node:assert/strict';
const [origin,route,output]=process.argv.slice(2);
assert.match(origin,/^http:\/\/127\.0\.0\.1:\d+$/);
assert.match(route,/^\/c\/[A-Za-z0-9_-]{22}$/);
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
  const page=await browser.newPage({viewport:{width:375,height:812}});
  const response=await page.goto(origin+route);assert.equal(response.status(),200);
  await page.locator('h1').filter({hasText:'Local <script> & 測試'}).waitFor();
  assert.equal(await page.locator('script').count(),0);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const button=page.getByRole('link',{name:'Save contact',exact:true});
  const box=await button.boundingBox();assert(box.height>=44);
  await page.screenshot({path:path.join(output,'recipient-mobile.png'),fullPage:true});
  const download=page.waitForEvent('download');await button.click();
  await(await download).saveAs(path.join(output,'recipient.vcf'));
  console.log('PASS: actual local Worker at 375px; escaped content, no horizontal overflow, contact download.');
}finally{await browser.close();}
