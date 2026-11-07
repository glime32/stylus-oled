#!/usr/bin/env python3
"""Liste les sites de l'historique d'Helium que le thème ne couvre pas encore.

Lancement (marche aussi dans fish) :
  curl -fsSL https://raw.githubusercontent.com/glime32/stylus-oled/main/outils/sites-manquants.py | python3

Ne garde que le nom des sites et leur nombre de visites, jamais les pages.
Écrit ~/sites-manquants.txt et le sert une seule fois sur http://127.0.0.1:8765
(10 minutes maximum) pour que Claude puisse le lire avec l'extension.
"""
import collections, datetime, glob, http.server, ipaddress, os, re, shutil, sqlite3, sys, tempfile
import urllib.parse, urllib.request

THEME = os.environ.get("THEME", "https://raw.githubusercontent.com/glime32/stylus-oled/main/oled-violet.user.css")

# 1) historique : nom du site -> visites, dernière visite
fichiers = glob.glob(os.path.expanduser("~/.config/*elium*/*/History")) + \
           glob.glob(os.path.expanduser("~/.var/app/*elium*/config/*/*/History"))
if not fichiers:
    sys.exit("Historique d'Helium introuvable dans ~/.config")
vus, der = collections.Counter(), {}
for f in fichiers:
    tmp = tempfile.mktemp()
    shutil.copy(f, tmp)                      # copie : la base est verrouillée quand Helium tourne
    with sqlite3.connect(tmp) as db:
        for url, n, last in db.execute("select url, visit_count, last_visit_time from urls"):
            p = urllib.parse.urlsplit(url)
            if p.scheme in ("http", "https") and p.hostname:
                vus[p.hostname] += n
                der[p.hostname] = max(der.get(p.hostname, 0), last)
    os.remove(tmp)

# 2) ce que le thème couvre déjà (mêmes règles que Stylus)
css = urllib.request.urlopen(THEME, timeout=30).read().decode("utf-8")
regles = []
for ligne in css.splitlines():
    if ligne.startswith("@-moz-document"):
        for typ, val in re.findall(r'(domain|url-prefix|url|regexp)\("((?:[^"\\]|\\.)*)"\)', ligne):
            regles.append((typ, re.sub(r"\\(.)", r"\1", val)))

def couvert(hote):
    for typ, val in regles:
        if typ == "domain" and (hote == val or hote.endswith("." + val)):
            return True
        if typ in ("url-prefix", "url") and urllib.parse.urlsplit(val).hostname == hote:
            return True
        if typ == "regexp":
            try:
                if re.fullmatch(val, f"https://{hote}/") or re.fullmatch(val, f"https://{hote}/x"):
                    return True
            except re.error:
                pass
    return False

def local(hote):
    try:
        ipaddress.ip_address(hote)
        return True
    except ValueError:
        return hote == "localhost" or hote.endswith((".local", ".lan", ".home", ".internal", ".localhost"))

jour = lambda us: (datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=us)).strftime("%Y-%m-%d")
manquants = [(n, h) for h, n in vus.most_common() if not local(h) and not couvert(h)]
texte = "\n".join(f"{n}\t{h}\t{jour(der[h])}" for n, h in manquants)
open(os.path.expanduser("~/sites-manquants.txt"), "w", encoding="utf-8").write(texte + "\n")
print(f"{len(vus)} sites dans l'historique, {len(manquants)} pas encore dans le thème.")
print("Liste : ~/sites-manquants.txt")

# 3) servir la liste une fois (Claude la lit avec l'extension), puis s'arrêter
class Page(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        corps = texte.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(corps)
    def log_message(self, *a):
        pass

if "--sans-serveur" not in sys.argv:
    print("En attente de Claude sur http://127.0.0.1:8765 (10 min max, Ctrl+C pour arrêter)…")
    s = http.server.HTTPServer(("127.0.0.1", 8765), Page)
    s.timeout = 600
    s.handle_request()
    print("Liste lue, fini.")
