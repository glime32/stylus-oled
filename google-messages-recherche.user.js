// ==UserScript==
// @name         Google Messages – barre de recherche
// @namespace    glime32
// @version      1.2
// @description  Ajoute une barre de recherche au-dessus de la liste des conversations (filtre par nom ou dernier message). Ctrl+K pour y aller. Couleurs : thème Stylus oled-violet.
// @match        https://messages.google.com/web/*
// @run-at       document-idle
// @grant        none
// @updateURL    https://raw.githubusercontent.com/glime32/stylus-oled/main/google-messages-recherche.user.js
// @downloadURL  https://raw.githubusercontent.com/glime32/stylus-oled/main/google-messages-recherche.user.js
// ==/UserScript==

(() => {
  'use strict';

  // enlève les accents : « é » -> « e »
  const norm = (s) => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
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
    box.style.padding = '8px 12px 4px';
    champ = document.createElement('input');
    champ.type = 'search';
    champ.placeholder = 'Rechercher une conversation  (Ctrl+K)';
    champ.autocomplete = 'off';
    box.append(champ);
    // mise en page seulement : les couleurs (et le rouge au focus) viennent du thème Stylus
    Object.assign(champ.style, {
      width: '100%', boxSizing: 'border-box', padding: '10px 16px', fontFamily: '"Google Sans", Roboto, sans-serif', fontSize: '15px',
      borderRadius: '24px',
    });
    champ.addEventListener('input', filtrer);
    champ.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { champ.value = ''; filtrer(); champ.blur(); }
      if (e.key === 'Enter') {
        const premier = [...document.querySelectorAll('mws-conversation-list-item')].find((x) => x.style.display !== 'none');
        premier?.querySelector('a')?.click();
      }
    });
    fab.after(box);
    filtrer();   // nouvelle barre vide : réaffiche ce qu'une ancienne barre aurait caché
  }

  // Quand la page change, un seul passage par image affichée (pas de boucle en fond)
  let prevu = false;
  new MutationObserver(() => {
    if (prevu) return;
    prevu = true;
    requestAnimationFrame(() => { prevu = false; installer(); if (champ?.value) filtrer(); });
  }).observe(document.body, { childList: true, subtree: true });
  installer();

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      installer();
      champ?.focus();
    }
  });
})();
