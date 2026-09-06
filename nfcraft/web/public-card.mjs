/** The recipient view shared by the local draft preview and public Worker. */
export const escapeText = value => String(value ?? '').replace(/[&<>"']/g, char =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

export function publicHttps(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

export const PUBLIC_CSS = `
body{margin:0;background:#f5f4ef;color:#263c31}
.contact-card{box-sizing:border-box;max-width:560px;margin:0 auto;padding:48px 28px 32px;font:16px/1.7 system-ui,sans-serif;color:#263c31;text-align:left}
.contact-card *{box-sizing:border-box}
.contact-card .intro-mark{width:38px;height:3px;background:#a5ae88;margin-bottom:28px}
.contact-card small{font-size:10px;letter-spacing:2px;color:#66765f}
.contact-card h1{font:42px/1.16 Georgia,serif;margin:24px 0 14px;overflow-wrap:anywhere;letter-spacing:-1px}
.contact-card h2{font-size:17px;line-height:1.6;font-weight:400;color:#52664e;margin:0 0 24px;overflow-wrap:anywhere}
.contact-card p{white-space:pre-wrap;overflow-wrap:anywhere;color:#52614c;margin:0 0 24px}
.contact-card .contact-actions{display:flex;flex-direction:column;gap:10px;margin-top:32px}
.contact-card a,.contact-card button{display:block;border:1px solid #bdcbb0;padding:13px 18px;border-radius:6px;color:inherit;text-decoration:none;background:transparent;font:inherit;text-align:center;min-height:48px}
.contact-card .primary-contact{background:#315c4e;color:white;border-color:#315c4e}
.contact-card a:focus-visible{outline:3px solid #8aa378;outline-offset:3px}
.contact-card button:disabled{opacity:1;cursor:default}
.contact-card footer{font-size:11px;margin-top:40px;padding-top:20px;border-top:1px solid #dce2d5;color:#65745e;line-height:1.7}
@media(min-width:600px){body>.contact-card{margin-top:5vh}}
`;

export function renderCardMarkup(profile, slug, {preview = false} = {}) {
  const website = publicHttps(profile.website);
  // Never interpolate an unchecked route identifier into a link.
  const route = /^[A-Za-z0-9_-]{22}$/.test(slug) ? `/c/${slug}/contact.vcf` : null;
  const save = preview || !route ? '<button class="primary-contact" disabled>Save contact</button>' :
    `<a class="primary-contact" href="${route}">Save contact</a>`;
  const visit = website ? (preview ? '<button disabled>Visit website</button>' :
    `<a href="${escapeText(website)}" rel="noopener noreferrer">Visit website</a>`) : '';
  return `<main class="contact-card"><div class="intro-mark" aria-hidden="true"></div><small>A SMALL INTRODUCTION</small>
    <h1>${escapeText(profile.name || (preview ? 'Your name' : ''))}</h1>
    ${profile.headline ? `<h2>${escapeText(profile.headline)}</h2>` : ''}
    ${profile.bio ? `<p>${escapeText(profile.bio)}</p>` : ''}
    <div class="contact-actions">${save}${visit}</div>
    <footer>A simple connection. No visitor analytics are collected by this application.</footer></main>`;
}

export function renderCardDocument(profile, slug) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeText(profile.name)}</title><style>${PUBLIC_CSS}</style></head><body>${renderCardMarkup(profile, slug)}</body></html>`;
}
