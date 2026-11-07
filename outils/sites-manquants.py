#!/usr/bin/env python3
"""Liste les sites de l'historique d'Helium que le thème ne couvre pas encore.

Lancement (marche aussi dans fish) :
  curl -fsSL https://raw.githubusercontent.com/glime32/stylus-oled/main/outils/sites-manquants.py | python3
  … | python3 - --sans-serveur        (sans le petit serveur de la fin)

Ne garde que le nom des sites, leur nombre de visites et le jour de la dernière
visite, jamais les pages. Écrit ~/sites-manquants.txt, puis le sert une seule fois
sur http://127.0.0.1:8765 pour qu'on puisse l'ouvrir dans le navigateur.

Réglages facultatifs :
  THEME=chemin/ou/url      thème à comparer (par défaut celui de la branche main)
  ATTENTE=secondes         durée max du serveur (600 par défaut)
  ~/.config/stylus-oled/ignorer.txt   un domaine par ligne (# pour commenter) :
                                      ces sites et leurs sous-domaines ne sont jamais listés
"""
import collections, datetime, glob, http.server, ipaddress, os, re, shutil, sqlite3, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request

THEME = os.environ.get("THEME", "https://raw.githubusercontent.com/glime32/stylus-oled/main/oled-violet.user.css")
CONFIG = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
try:
    ATTENTE = max(1, int(os.environ.get("ATTENTE", "600")))
except ValueError:
    ATTENTE = 600
PORT = 8765


def hote_de(url):
    """Nom du site d'une adresse http(s), en minuscules et sans point final ; None sinon."""
    try:
        p = urllib.parse.urlsplit(url)
        h = p.hostname
    except ValueError:                       # adresse mal formée, par ex. « http://[abc »
        return None
    if p.scheme not in ("http", "https") or not h:
        return None
    return h.rstrip(".") or None


# 1) historique : nom du site -> visites, dernière visite
fichiers = glob.glob(os.path.join(CONFIG, "*elium*", "*", "History")) + \
           glob.glob(os.path.expanduser("~/.var/app/*elium*/config/*/*/History"))
if not fichiers:
    sys.exit(f"Historique d'Helium introuvable (cherché dans {CONFIG} et ~/.var/app).")
vus, der = collections.Counter(), {}
for f in fichiers:
    with tempfile.TemporaryDirectory() as d:
        try:
            # copie : la base est verrouillée quand Helium tourne ; le journal suit pour rester cohérent
            for suffixe in ("", "-wal", "-journal"):
                if os.path.exists(f + suffixe):
                    shutil.copy(f + suffixe, os.path.join(d, "History" + suffixe))
            db = sqlite3.connect(os.path.join(d, "History"))
            try:
                lignes = db.execute("select url, visit_count, last_visit_time from urls").fetchall()
            finally:
                db.close()
        except (OSError, sqlite3.Error) as e:
            print(f"Ignoré (illisible) : {f} — {e}", file=sys.stderr)
            continue
    for url, n, last in lignes:
        h = hote_de(url)
        if h:
            vus[h] += n or 0
            der[h] = max(der.get(h, 0), last or 0)

# 2) ce que le thème couvre déjà (mêmes règles que Stylus)
try:
    if re.match(r"^https?://", THEME):
        css = urllib.request.urlopen(THEME, timeout=30).read().decode("utf-8")
    else:
        css = open(os.path.expanduser(THEME), encoding="utf-8").read()
except (OSError, urllib.error.URLError, UnicodeDecodeError) as e:
    sys.exit(f"Thème illisible ({THEME}) : {e}")

# commentaires retirés sans toucher aux chaînes (un /* peut être dans une regexp)
css = re.sub(r'("(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\')|/\*.*?\*/', lambda m: m.group(1) or " ", css, flags=re.S)
MATCHER = re.compile(r'[\s,]*(domain|url-prefix|url|regexp)\(\s*(["\'])((?:(?!\2)[^\\]|\\.)*)\2\s*\)')
UN_SEUL_ECHAPPEMENT = re.compile(r"([^\\]|^)\\([^\\]|$)")
regles = []
for debut in re.finditer(r"@-moz-document\b", css):
    pos = debut.end()
    while (m := MATCHER.match(css, pos)):
        typ, val = m.group(1), m.group(3)
        # comme Stylus : une regexp écrite avec de simples \ est prise telle quelle, sinon on décode le CSS
        if not (typ == "regexp" and UN_SEUL_ECHAPPEMENT.search(val)):
            val = re.sub(r"\\(.)", r"\1", val)
        regles.append((typ, val))
        pos = m.end()
if not regles:
    sys.exit(f"Aucun bloc @-moz-document trouvé dans {THEME}.")


def couvert(hote):
    for typ, val in regles:
        if typ == "domain" and (hote == val or hote.endswith("." + val)):
            return True
        if typ in ("url-prefix", "url") and hote_de(val) == hote:
            return True
        if typ == "regexp":
            try:
                if any(re.fullmatch(val, f"https://{hote}{chemin}") for chemin in ("/", "/x")):
                    return True
            except re.error:                 # syntaxe propre à JavaScript : on ne peut pas trancher ici
                pass
    return False


def local(hote):
    try:
        ipaddress.ip_address(hote)
        return True
    except ValueError:
        return hote == "localhost" or hote.endswith(
            (".local", ".lan", ".home", ".internal", ".localhost", ".home.arpa", ".test", ".invalid", ".example"))


ignores = []
try:
    with open(os.path.join(CONFIG, "stylus-oled", "ignorer.txt"), encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.split("#")[0].strip().lower().rstrip(".").lstrip("*.")
            if ligne:
                ignores.append(hote_de(ligne) or hote_de("https://" + ligne) or ligne)
except FileNotFoundError:
    pass
ignore = lambda h: any(h == i or h.endswith("." + i) for i in ignores)

jour = lambda us: (datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=us)).strftime("%Y-%m-%d") if us else "?"
candidats = [h for h in vus if not local(h) and not couvert(h)]
restants = {h for h in candidats if not ignore(h)}
# www.site.fr et site.fr ne font qu'une ligne quand les deux manquent
groupe = lambda h: h[4:] if h.startswith("www.") and h[4:] in restants else h
total, dernier = collections.Counter(), {}
for h in restants:
    total[groupe(h)] += vus[h]
    dernier[groupe(h)] = max(dernier.get(groupe(h), 0), der[h])
manquants = sorted(total.items(), key=lambda x: (-x[1], x[0]))
texte = "\n".join(f"{n}\t{h}\t{jour(dernier[h])}" for h, n in manquants)
sortie = os.path.expanduser("~/sites-manquants.txt")
with open(sortie, "w", encoding="utf-8") as f:
    f.write(texte + "\n")
autres = len(candidats) - len(restants)
print(f"{len(vus)} sites dans l'historique, {len(manquants)} pas encore dans le thème"
      + (f" ({autres} ignorés)." if autres else "."))
print(f"Liste : {sortie}")


# 3) servir la liste une fois, puis s'arrêter
class Page(http.server.BaseHTTPRequestHandler):
    servi = False

    def do_GET(self):
        if self.path.startswith("/favicon"):
            self.send_error(404)
            return
        corps = texte.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)
        Page.servi = True

    def log_message(self, *a):
        pass


if "--sans-serveur" not in sys.argv:
    try:
        s = http.server.HTTPServer(("127.0.0.1", PORT), Page)
    except OSError as e:
        sys.exit(f"Port {PORT} indisponible ({e.strerror}) : la liste est quand même dans {sortie}.")
    duree = f"{ATTENTE // 60} min" if ATTENTE >= 60 else f"{ATTENTE} s"
    print(f"Liste aussi sur http://127.0.0.1:{PORT} ({duree} max, Ctrl+C pour arrêter)…")
    fin = time.monotonic() + ATTENTE
    try:
        while not Page.servi and (reste := fin - time.monotonic()) > 0:
            s.timeout = reste                # une requête à côté (favicon…) ne coupe pas l'attente
            s.handle_request()
    except KeyboardInterrupt:
        print()
    finally:
        s.server_close()
    print("Liste lue, fini." if Page.servi else f"Serveur arrêté, la liste reste dans {sortie}.")
