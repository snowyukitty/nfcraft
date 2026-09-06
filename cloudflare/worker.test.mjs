import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {makeVcard, foldVcard, vescape} from './worker.mjs';
const slug='A'.repeat(22), base=`https://tap.example.com/c/${slug}`;
const profile={name:'啓真',headline:'A small introduction',bio:'Hello',email:'hello@example.com',website:'https://example.com'};
function env(row={state:'enabled',body:JSON.stringify(profile)}) {return {DB:{prepare(sql){assert.ok(sql.includes('WHERE r.slug=?'));return {bind(key){assert.equal(key,slug);return {async first(){return row;}};}};}}};}
test('active route renders a contact page',async()=>{const r=await worker.fetch(new Request(base),env());assert.equal(r.status,200);assert.match(await r.text(),/Save contact/);});
test('unknown identity returns 404',async()=>{const r=await worker.fetch(new Request(base),env(null));assert.equal(r.status,404);});
test('unknown path returns 404',async()=>{const r=await worker.fetch(new Request('https://tap.example.com/admin'),{});assert.equal(r.status,404);});
test('suspended card returns 410',async()=>{const r=await worker.fetch(new Request(base),env({state:'suspended',body:'{}'}));assert.equal(r.status,410);});
test('no mutation endpoint',async()=>{const r=await worker.fetch(new Request(base,{method:'POST'}),env());assert.equal(r.status,405);});
test('HEAD body is empty',async()=>{const r=await worker.fetch(new Request(base,{method:'HEAD'}),env());assert.equal(await r.text(),'');});
test('invalid profile returns 503',async()=>{const r=await worker.fetch(new Request(base),env({state:'enabled',body:'garbled'}));assert.equal(r.status,503);});
test('html is escaped and javascript website is excluded',async()=>{const r=await worker.fetch(new Request(base),env({state:'enabled',body:JSON.stringify({...profile,name:'<script>alert(1)</script>',website:'javascript:alert(1)'})}));const html=await r.text();assert.ok(!html.includes('<script>'));assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('href="javascript:'));});
test('vcard UTF8 and safe filename',async()=>{const r=await worker.fetch(new Request(base+'/contact.vcf'),env());assert.match(r.headers.get('content-type'),/text\/vcard/);assert.match(await r.text(),/FN:啓真/);assert.match(r.headers.get('content-disposition'),/contact.vcf/);});
test('vcard fields cannot inject additional properties',()=>{const t=makeVcard({...profile,name:'Name\nURL:evil;comma,'});assert.ok(!t.includes('\r\nURL:evil'));assert.ok(t.includes('Name\\nURL:evil\\;comma\\,'));});
test('vcard folds at 75 UTF8 bytes and preserves unicode',()=>{const original='FN:'+'貓咪'.repeat(80),folded=foldVcard(original);for(const line of folded.split('\r\n'))assert.ok(Buffer.byteLength(line)<=75);assert.equal(folded.replaceAll('\r\n ',''),original);});
test('response is private-client agnostic, no analytics script',async()=>{const r=await worker.fetch(new Request(base),env());const html=await r.text();assert.equal(r.headers.get('cache-control'),'no-store');assert.match(r.headers.get('content-security-policy'),/default-src 'none'/);assert.ok(!html.includes('<script'));assert.ok(!html.includes('uid='));});
test('JSON null profile is handled without crashing',async()=>{const r=await worker.fetch(new Request(base),env({state:'enabled',body:'null'}));assert.equal(r.status,503);});
