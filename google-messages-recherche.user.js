// ==UserScript==
// @name         Google Messages – barre de recherche
// @namespace    glime32
// @version      1.0
// @description  Ajoute une barre de recherche au-dessus de la liste des conversations (filtre par nom ou dernier message). Ctrl+K pour y aller.
// @match        https://messages.google.com/web/*
// @run-at       document-idle
// @grant        none
// @updateURL    https://raw.githubusercontent.com/glime32/stylus-oled/main/google-messages-recherche.user.js
// @downloadURL  https://raw.githubusercontent.com/glime32/stylus-oled/main/google-messages-recherche.user.js
// ==/UserScript==

(() => {
  'use strict';

  const norm = (s) => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  let champ = null;

  function filtrer() {
    const q = norm(champ?.value).trim();
    document.querySelectorAll('mws-conversation-list-item').forEach((it) => {
      it.style.display = !q || norm(it.textContent).includes(q) ? '' : 'none';
    });
  }

  function installer() {
    if (document.getElementById('gm-recherche')) return;
    const fab = document.querySelector('mw-fab-link.start-chat');
    if (!fab) return;
    const box = document.createElement('div');
    box.id = 'gm-recherche';
    Object.assign(box.style, { padding: '8px 12px 4px' });
    champ = document.createElement('input');
    champ.type = 'search';
    champ.placeholder = 'Rechercher une conversation  (Ctrl+K)';
    champ.autocomplete = 'off';
    box.append(champ);
    Object.assign(champ.style, {
      width: '100%', boxSizing: 'border-box', padding: '10px 16px', fontFamily: '"Google Sans", Roboto, sans-serif', fontSize: '15px',
      color: '#fff', background: '#0a0010', border: '2px solid #610089', borderRadius: '24px',
      backgroundClip: 'padding-box', outline: 'none',
    });
    champ.addEventListener('focus', () => (champ.style.borderColor = '#c8a2ff'));
    champ.addEventListener('blur', () => (champ.style.borderColor = '#610089'));
    champ.addEventListener('input', filtrer);
    champ.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { champ.value = ''; filtrer(); champ.blur(); }
      if (e.key === 'Enter') {
        const premier = [...document.querySelectorAll('mws-conversation-list-item')].find((x) => x.style.display !== 'none');
        premier?.querySelector('a')?.click();
      }
    });
    fab.after(box);
  }

  // Seulement quand la liste change (pas de boucle en fond)
  new MutationObserver(() => { installer(); if (champ?.value) filtrer(); })
    .observe(document.body, { childList: true, subtree: true });
  installer();

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      installer();
      champ?.focus();
    }
  });
})();
