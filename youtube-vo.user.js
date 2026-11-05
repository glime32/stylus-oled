// ==UserScript==
// @name         YouTube – audio et sous-titres toujours en VO
// @namespace    glime32
// @version      4.2
// @description  Piste audio originale (pas de doublage auto) + sous-titres dans la langue originale (pas de traduction auto).
// @match        https://www.youtube.com/*
// @run-at       document-start
// @inject-into  page
// @grant        none
// @updateURL    https://raw.githubusercontent.com/glime32/stylus-oled/main/youtube-vo.user.js
// @downloadURL  https://raw.githubusercontent.com/glime32/stylus-oled/main/youtube-vo.user.js
// ==/UserScript==

(() => {
  'use strict';

  const base = (l) => (l || '').split(/[-.]/)[0].toLowerCase();
  const lecteur = () => document.getElementById('movie_player');
  let attenteSt = 0, attenteAu = 0;

  // ---------- Piste audio ----------
  function idAudio(t) {
    try { const i = t?.getLanguageInfo?.(); if (i?.getId) return i.getId(); } catch {}
    return typeof t?.id === 'string' ? t.id : '';
  }
  function nomAudio(t) {
    try { const i = t?.getLanguageInfo?.(); if (i?.getName) return i.getName(); } catch {}
    return '';
  }

  // Piste audio originale (ex : « Français original », id fr.4)
  function audioOriginal(p) {
    const pistes = p.getAvailableAudioTracks?.() || [];
    if (pistes.length < 2) return null; // pas de doublage
    const formats = p.getPlayerResponse?.()?.streamingData?.adaptiveFormats || [];
    const def = formats.find((f) => f.audioTrack?.audioIsDefault)?.audioTrack;
    return (def && pistes.find((x) => idAudio(x) === def.id))
      || pistes.find((x) => /original/i.test(nomAudio(x)))
      || null;
  }

  function corrigerAudio() {
    const p = lecteur();
    if (!p?.getAudioTrack) return;
    const o = audioOriginal(p);
    if (o && idAudio(p.getAudioTrack()) !== idAudio(o)) {
      p.setAudioTrack(o);
      console.log('[VO] audio remis en', idAudio(o));
    }
    corrigerSousTitres();
  }

  // ---------- Sous-titres ----------
  // Un vrai id de langue audio ressemble à « fr-FR.4 », « en-US.3 », « fr.4 »
  const idValide = (id) => /^[a-z]{2,3}(-[a-z0-9]+)?\.\d+$/i.test(id || '');

  function langueOriginale(p, tracks) {
    const o = audioOriginal(p);
    if (o && idValide(idAudio(o))) return base(idAudio(o));
    const formats = p.getPlayerResponse?.()?.streamingData?.adaptiveFormats || [];
    const def = formats.find((f) => f.audioTrack?.audioIsDefault)?.audioTrack;
    if (idValide(def?.id)) return base(def.id);
    const pistes = p.getAvailableAudioTracks?.() || [];
    if (pistes.length === 1 && idValide(idAudio(pistes[0]))) return base(idAudio(pistes[0]));
    const ra = p.getPlayerResponse?.()?.captions?.playerCaptionsTracklistRenderer?.audioTracks;
    if (ra?.length === 1 && idValide(ra[0].audioTrackId)) return base(ra[0].audioTrackId);
    const asr = tracks.filter((t) => t.kind === 'asr');
    return asr.length === 1 ? base(asr[0].languageCode) : null;
  }

  function corrigerSousTitres() {
    const p = lecteur();
    if (!p?.getOption) return;
    const actuelle = p.getOption('captions', 'track');
    if (!actuelle?.languageCode) return; // sous-titres désactivés
    const tracks = p.getPlayerResponse?.()?.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
    const vo = langueOriginale(p, tracks);
    if (!vo) return;
    if (base(actuelle.languageCode) === vo && !actuelle.translationLanguage) return; // déjà bon
    const memes = tracks.filter((t) => base(t.languageCode) === vo);
    const c = memes.find((t) => t.kind !== 'asr') || memes[0];
    if (!c) return;
    const piste = { languageCode: c.languageCode, vss_id: c.vssId };
    if (c.kind) piste.kind = c.kind;
    p.setOption('captions', 'track', piste);
    console.log('[VO] sous-titres remis en', c.vssId);
  }

  // Ne s'exécute que quand YouTube télécharge des sous-titres
  function verifierUrl(url) {
    const s = String(url);
    if (!s.includes('/api/timedtext')) return url;
    clearTimeout(attenteSt);
    attenteSt = setTimeout(corrigerSousTitres, 300);
    try {
      const u = new URL(s, location.href);
      if (u.searchParams.has('tlang')) {
        u.searchParams.delete('tlang');
        return u.toString();
      }
    } catch {}
    return url;
  }

  const open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (m, url, ...r) {
    return open.call(this, m, verifierUrl(url), ...r);
  };
  const f = window.fetch;
  window.fetch = function (input, init) {
    if (input instanceof Request) {
      const n = verifierUrl(input.url);
      if (n !== input.url) input = new Request(n, input);
    } else if (input != null) {
      input = verifierUrl(input);
    }
    return f.call(this, input, init);
  };

  // ---------- Branchement (seulement au chargement d'une vidéo) ----------
  function surVideo() {
    clearTimeout(attenteAu);
    attenteAu = setTimeout(corrigerAudio, 500);
  }
  document.addEventListener('yt-navigate-finish', () => {
    const p = lecteur();
    if (p?.addEventListener && !p.__voBranche) {
      p.__voBranche = true;
      p.addEventListener('onVideoDataChange', surVideo);
    }
    surVideo();
  });
})();
