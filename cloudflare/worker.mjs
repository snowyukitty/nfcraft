/** Public read-only card site. No administration, AI calls, PII analytics or private tools. */
const esc = value => String(value ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const headers = {'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
 'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"};
export const vescape = s => String(s??'').replaceAll('\\','\\\\').replaceAll('\r\n','\\n').replaceAll('\n','\\n').replaceAll('\r','\\n').replaceAll(';','\\;').replaceAll(',','\\,');
export function foldVcard(line) {
  const encoder = new TextEncoder(); let out='', current='', bytes=0;
  for(const char of line){const size=encoder.encode(char).length;if(bytes+size>75){out+=current+'\r\n';current=' ';bytes=1;}current+=char;bytes+=size;}
  return out+current;
}
export function makeVcard(p) {
  return ['BEGIN:VCARD','VERSION:3.0',`FN:${vescape(p.name)}`,`N:;${vescape(p.name)};;;`,
    p.email?`EMAIL:${vescape(p.email)}`:'',p.website?`URL:${vescape(p.website)}`:'','END:VCARD'].filter(Boolean).map(foldVcard).join('\r\n')+'\r\n';
}
function publicHttps(value) {try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}}
export default {
 async fetch(request, env) {
  if(request.method!=='GET' && request.method!=='HEAD')return new Response('Method not allowed',{status:405,headers:{...headers,'Allow':'GET, HEAD'}});
  const url=new URL(request.url);
  const match=url.pathname.match(/^\/c\/([A-Za-z0-9_-]{22})(\/contact\.vcf)?$/);
  if(!match)return new Response('Card not found',{status:404,headers});
  const row=await env.DB.prepare('SELECT r.state,p.body FROM routes r JOIN profiles p ON p.id=r.profile_id WHERE r.slug=?').bind(match[1]).first();
  if(!row)return new Response('Card not found',{status:404,headers});
  if(row.state!=='enabled')return new Response('This card is unavailable.',{status:410,headers});
  let p;try{p=JSON.parse(row.body);}catch{return new Response('Profile unavailable',{status:503,headers});}
  if(!p || Array.isArray(p) || !['name','headline','bio','email','website'].every(k=>typeof p[k]==='string'))return new Response('Profile unavailable',{status:503,headers});
  if(match[2])return new Response(request.method==='HEAD'?null:makeVcard(p),{headers:{...headers,'Content-Type':'text/vcard; charset=utf-8','Content-Disposition':'attachment; filename="contact.vcf"'}});
  const website=publicHttps(p.website);
  const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(p.name)}</title><style>body{background:#f5f4ef;color:#263c31;font:16px/1.7 system-ui;margin:0;padding:60px 24px}main{max-width:540px;margin:6vh auto}small{font-size:10px;letter-spacing:2px;color:#7a8b72}h1{font:46px Georgia,serif;margin:24px 0 12px;overflow-wrap:anywhere}h2{font-size:17px;font-weight:400;color:#7c8774}p{white-space:pre-wrap;overflow-wrap:anywhere;color:#64715e}a{display:inline-block;border:1px solid #bdcbb0;padding:11px 18px;border-radius:5px;color:inherit;text-decoration:none;margin:8px 8px 8px 0}a:first-of-type{background:#315c4e;color:white;border-color:#315c4e}footer{font-size:11px;margin-top:60px;color:#9aa68e}</style></head><body><main><small>A SMALL INTRODUCTION</small><h1>${esc(p.name)}</h1><h2>${esc(p.headline)}</h2><p>${esc(p.bio)}</p><a href="/c/${match[1]}/contact.vcf">Save contact</a>${website?`<a href="${esc(website)}" rel="noopener noreferrer">Visit website</a>`:''}<footer>A simple connection. No visitor analytics are collected by this application.</footer></main></body></html>`;
  return new Response(request.method==='HEAD'?null:html,{headers:{...headers,'Content-Type':'text/html; charset=utf-8'}});
 }
};
