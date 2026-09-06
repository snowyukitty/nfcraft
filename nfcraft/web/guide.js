/* Offline bilingual guide: no storage, remote requests or operator capabilities. */
(() => {
  const buttons = [...document.querySelectorAll('[data-language]')];
  function select(language) {
    if (!['en', 'zh-Hant'].includes(language)) return;
    document.documentElement.lang = language;
    document.querySelectorAll('[data-copy]').forEach(article => { article.hidden = article.dataset.copy !== language; });
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.language === language)));
  }
  buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.language)));
  select(location.hash === '#start-zh' || new URLSearchParams(location.search).get('lang') === 'zh-Hant' ? 'zh-Hant' : 'en');
})();
