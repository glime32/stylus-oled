#!/usr/bin/env bash
# Theme OLED violet pour le lecteur PDF.js (copie non empaquetee de l extension "PDF Viewer").
# Ajoute oled-pdfjs.css juste apres viewer.css + mise a jour auto (timer systemd, sinon cron).
# Usage : curl -fsSL https://raw.githubusercontent.com/glime32/stylus-oled/main/pdfjs/install.sh | bash
set -euo pipefail

URL="https://raw.githubusercontent.com/glime32/stylus-oled/main/pdfjs/oled-pdfjs.css"

trouver() {
  if [ -n "${PDFJS_DIR:-}" ]; then echo "$PDFJS_DIR"; return; fi
  for d in "$HOME/pdfjs-custom" "$HOME/extensions/pdfjs" "$HOME/extensions/pdfjs-custom"; do
    if [ -f "$d/content/web/viewer.html" ]; then echo "$d"; return; fi
  done
  # sinon : cherche une copie non empaquetee (jamais celle du Web Store, dans .../Extensions/)
  local f
  f=$(find "$HOME" -maxdepth 5 -path "$HOME/.cache" -prune -o -path '*/content/web/viewer.html' -print 2>/dev/null \
      | grep -v '/Extensions/' | head -n1 || true)
  if [ -n "$f" ]; then echo "${f%/content/web/viewer.html}"; fi
}

DIR=$(trouver)
if [ -z "$DIR" ] || [ ! -f "$DIR/content/web/viewer.html" ]; then
  echo "Lecteur PDF.js non trouve."
  echo "Relance avec son dossier : curl -fsSL ... | PDFJS_DIR=/chemin/du/dossier bash"
  exit 1
fi
WEB="$DIR/content/web"

# Script local de mise a jour : telecharge seulement le CSS (aucun code distant execute)
mkdir -p "$HOME/.local/bin"
MAJ="$HOME/.local/bin/oled-pdfjs-maj"
cat > "$MAJ" <<EOF
#!/usr/bin/env bash
# Met a jour le theme OLED du lecteur PDF.js ($WEB)
set -eu
WEB="$WEB"
curl -fsSL --retry 2 "$URL" -o "\$WEB/oled-pdfjs.css.tmp"
mv -f "\$WEB/oled-pdfjs.css.tmp" "\$WEB/oled-pdfjs.css"
if ! grep -q 'oled-pdfjs.css' "\$WEB/viewer.html"; then
  sed -i '0,/href="viewer.css"[^>]*>/s//&\n    <link rel="stylesheet" href="oled-pdfjs.css" \/>/' "\$WEB/viewer.html"
fi
if ! grep -q 'oled-pdfjs.css' "\$WEB/viewer.html"; then
  sed -i '0,/<\/head>/s//  <link rel="stylesheet" href="oled-pdfjs.css" \/>\n<\/head>/' "\$WEB/viewer.html"
fi
EOF
chmod +x "$MAJ"
"$MAJ"

# Mise a jour auto, toutes les heures : timer systemd utilisateur si possible,
# sinon cron, sinon rien (le script de mise a jour reste utilisable a la main)
if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
# (les fichiers d'unite ne sont pas indentes : les fins de heredoc doivent etre en debut de ligne)
UNIT="$HOME/.config/systemd/user"
mkdir -p "$UNIT"

cat > "$UNIT/oled-pdfjs-maj.service" <<EOF
[Unit]
Description=Mise a jour du theme OLED du lecteur PDF.js

[Service]
Type=oneshot
ExecStart="$MAJ"
EOF

cat > "$UNIT/oled-pdfjs-maj.timer" <<EOF
[Unit]
Description=Mise a jour auto du theme OLED du lecteur PDF.js

[Timer]
OnStartupSec=45s
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now oled-pdfjs-maj.timer
AUTO="active (timer systemd, toutes les heures)"
elif command -v crontab >/dev/null 2>&1; then
  { crontab -l 2>/dev/null | grep -v -F "$MAJ" || true; echo "0 * * * * \"$MAJ\" >/dev/null 2>&1"; } | crontab -
  AUTO="active (cron, toutes les heures)"
else
  AUTO="impossible ici (ni systemd ni cron) : lance $MAJ pour mettre a jour"
fi

echo
echo "OK : theme applique dans $WEB"
echo "Mise a jour auto : $AUTO"
echo "Recharge tes onglets PDF. Si rien ne change : helium://extensions -> bouton recharger de PDF Viewer."
