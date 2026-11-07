<p align="center"><img src="docs/banner-stylus-oled.png" alt="stylus-oled" width="100%"></p>

<p align="center"><img src="https://img.shields.io/badge/works%20with-Stylus%20·%20Violentmonkey-610089?style=flat-square" alt="works with"> <img src="https://img.shields.io/badge/sites-400+-000000?style=flat-square" alt="sites"> <img src="https://img.shields.io/badge/license-MIT-610089?style=flat-square" alt="license"></p>

<p align="center"><a href="README.fr.md">🇫🇷 Version française</a></p>

**My OLED black + purple theme for pretty much every site I use**, plus a few userscripts. Everything updates itself from this repo.

Palette: `#000000` background (pixels fully off on OLED screens), one single purple `#610089` for buttons, 2 px borders and highlights (darker shades `#2a003b` / `#14001e` for unread, selected and hover backgrounds, `#0a0010` for menus, fields and code blocks), white text and icons, links underlined in `#610089`, red `#ff3b3b` for hover, focus and "danger".

These colours are Stylus variables: change them all at once in Stylus → *Configure* on the style.

<table>
<tr><td><img src="docs/duckduckgo.jpg" alt="DuckDuckGo"></td><td><img src="docs/github.jpg" alt="GitHub"></td></tr>
<tr><td align="center"><sub>DuckDuckGo</sub></td><td align="center"><sub>GitHub</sub></td></tr>
<tr><td><img src="docs/wikipedia.jpg" alt="Wikipedia"></td><td><img src="docs/archwiki.jpg" alt="ArchWiki"></td></tr>
<tr><td align="center"><sub>Wikipédia</sub></td><td align="center"><sub>ArchWiki</sub></td></tr>
<tr><td><img src="docs/stackoverflow.jpg" alt="Stack Overflow"></td><td><img src="docs/mdn.jpg" alt="MDN"></td></tr>
<tr><td align="center"><sub>Stack Overflow</sub></td><td align="center"><sub>MDN</sub></td></tr>
</table>

## Install

| File | For | Install |
|---|---|---|
| `oled-violet.user.css` | [Stylus](https://github.com/openstyles/stylus) | [**install**](https://raw.githubusercontent.com/glime32/stylus-oled/main/oled-violet.user.css) |
| `youtube-vo.user.js` | Violentmonkey / Tampermonkey | [**install**](https://raw.githubusercontent.com/glime32/stylus-oled/main/youtube-vo.user.js) |
| `google-messages-recherche.user.js` | Violentmonkey / Tampermonkey | [**install**](https://raw.githubusercontent.com/glime32/stylus-oled/main/google-messages-recherche.user.js) |
| `pdfjs/oled-pdfjs.css` | PDF.js (*PDF Viewer* extension, unpacked copy) | one command, see [below](#pdfjs--pdf-viewer) |

One click opens the extension's install page. Each file has an `@updateURL` pointing here.

## oled-violet.user.css

One style with an `@-moz-document` block per site, applied automatically to the right domain. Some of the sites covered:

- **Google**: YouTube, Gmail, Gemini, Google accounts
- **Search / knowledge**: DuckDuckGo, Wikipedia and other Wikimedia wikis, ArchWiki, CachyOS wiki, Stack Exchange, WolframAlpha, Python docs, MDN, Minecraft Wiki, Fandom
- **Social / messaging**: Discord, WhatsApp Web, Instagram, Snapchat, TikTok, Reddit, LinkedIn
- **Other**: GitHub, Twitch, Spotify, SoundCloud, Steam, ProtonDB, Chess.com, Modrinth, Desmos, GeoGebra, Zoom, PayPal, MangaDex, Scribd, Amazon, AliExpress, claude.ai, Université de Montpellier (Moodle, CAS, ENT)…

Rules used everywhere: rounded borders are always **2 px with `background-clip: padding-box`** (1 px borders look thinner in the corners); Help / Privacy / Terms links and useless footers are hidden; unread messages stand out in purple; sites without a dark mode get a real dark theme instead of a colour inversion. Inversion is only kept where nothing else works: Desmos and GeoGebra graphs, the body of emails in Gmail (their HTML is too varied), two closed widgets (Zoom calendar, PayPal) and, only when you switch them to light mode, the NumPy / Matplotlib / pandas / SciPy docs, gouv.fr sites and Canva. Wikipedia, GitHub, GitLab and MDN: the theme dresses their own dark mode, so set them to *Dark* (or *Auto* with a dark system).

## youtube-vo.user.js

Forces the **original audio track** (no auto-dub) and **subtitles in the video's language** (no auto-translate). It only acts when YouTube loads a track or subtitles — no background loop.

## google-messages-recherche.user.js

Adds a search bar to [Google Messages for web](https://messages.google.com/web), like the Android app: filters conversations by name or last message.

## pdfjs/ — PDF viewer

Stylus can't touch `chrome-extension://` pages, so the PDF viewer (an unpacked copy of the *PDF Viewer* extension, PDF.js) gets its own layer: `oled-pdfjs.css`, loaded right after `viewer.css`.

- the same look as the rest of the theme: white icons (red on hover), active tool in a `#610089` circle, page number and zoom in black pills with a 2 px `#610089` border, menus with rounded corners;
- the top bar hides itself and slides down as soon as the mouse gets near the top of the page (48 px zone), with a thin purple line showing where it is; it stays open while a menu, the search or a tool is open.

```bash
curl -fsSL https://raw.githubusercontent.com/glime32/stylus-oled/main/pdfjs/install.sh | bash
```

The script finds the viewer folder (`~/pdfjs-custom` by default, or `PDFJS_DIR=...`), adds the CSS and an hourly update (systemd user timer, or cron when there is no systemd). Then reload the PDF tabs.

## Editing the theme

- one block per site, starting with `/*@@ Site name @@*/`;
- the `/*@@ modèle générique … @@*/` block is shared by about 120 sites that have no dark mode of their own: one edit there applies to all of them;
- colours are written `var(--ov-violet)`, `var(--ov-rouge)`… (list in the file header);
- `outils/sites-manquants.py` lists the sites of your Helium history that the theme doesn't cover yet (`curl -fsSL https://raw.githubusercontent.com/glime32/stylus-oled/main/outils/sites-manquants.py | python3`);
- Stylus only takes an update when `@version` goes up: run `git config core.hooksPath .githooks` once in your clone and every commit that touches the CSS bumps it automatically.

## License

MIT, see [LICENSE](LICENSE).

## See also

- [nouvel-onglet-oled](https://github.com/glime32/nouvel-onglet-oled) — matching New Tab page
- [soundcloud-mobile](https://github.com/glime32/soundcloud-mobile) — SoundCloud as a mobile app
