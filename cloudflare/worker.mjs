/** Public read-only card site. No administration, AI calls, PII analytics or private tools. */
import {renderCardDocument} from '../nfcraft/web/public-card.mjs';
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
  const html=renderCardDocument(p, match[1]);
  return new Response(request.method==='HEAD'?null:html,{headers:{...headers,'Content-Type':'text/html; charset=utf-8'}});
 }
};
