#!/usr/bin/env python3
"""Fabrique les pages du site à partir de _src/site.html (source en une page) et de _src/legal/.

Usage : python3 _src/build.py   (depuis la racine du dépôt ; nécessite playwright et Chrome)
Sortie : *.html à la racine, assets/site.css, assets/site.js, sitemap.xml, robots.txt
"""
import functools, http.server, pathlib, re, socketserver, sys, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
DOMAIN = "https://www.eranosinstitute.com"

PAGES = {  # vue -> (fichier, titre, description)
    "accueil": ("index.html", "ERANOS Institute : formations, recherche et publications", "ERANOS Institute, à Nice : formations, accompagnement, recherche et publications en psychologie positive, éducation, médiation et intelligence spirituelle des dirigeants."),
    "eranos": ("a-propos.html", "À propos d'ERANOS Institute : du banquet grec aux rencontres d'Ascona", "L'histoire du mot eranos, des banquets grecs aux rencontres d'Ascona sur le lac Majeur, et la présentation de l'institut fondé en 2013 par Alain Ruffion."),
    "fondateur": ("fondateur.html", "Alain Ruffion, fondateur d'ERANOS Institute", "Biographie d'Alain Ruffion : docteur en sciences de l'éducation, psychanalyste, auteur, professeur à l'Université Ibn Tofail, fondateur d'ERANOS Institute."),
    "equipe": ("equipe.html", "L'équipe d'ERANOS Institute", "Les formateurs et partenaires d'ERANOS Institute."),
    "chaire": ("chaire.html", "Chaire d'éducation spirituelle pour la paix", "Le projet de chaires universitaires d'éducation spirituelle pour la paix porté par ERANOS Institute et ses partenaires."),
    "formations": ("formations.html", "Formations ERANOS Institute : quarante modules", "Quarante modules de formation : travail social et socio-éducatif, prévention des radicalisations, psychologie positive, éducation positive."),
    "prestations": ("prestations.html", "Prestations ERANOS Institute", "Intelligence émotionnelle et efficacité managériale, ressources face à l'incertitude, médiation professionnelle, soft skills des jeunes en insertion."),
    "fudoshin": ("fudoshin.html", "Fudōshin, programme d'accompagnement des managers", "Fudōshin : trois mois en groupe de douze pour les managers, d'après le livre Le Manager Fudōshin d'Alain Ruffion."),
    "intelligence-spirituelle": ("intelligence-spirituelle.html", "L'intelligence spirituelle des dirigeants et managers du XXIe siècle", "Définition, mesure, preuves et garde-fous de l'intelligence spirituelle des dirigeants, d'après l'ouvrage d'Alain Ruffion."),
    "publications": ("publications.html", "Publications d'Alain Ruffion et d'ERANOS Institute", "Les livres d'Alain Ruffion : Le Manager Fudōshin, Existential Education for the Age of Collapse, Les orphelins de la République, et les autres."),
    "ressources": ("ressources.html", "Ressources en psychologie positive et psychopathologie", "Dix dossiers en psychologie clinique, psychopathologie et psychologie positive."),
    "contact": ("contact.html", "Contacter ERANOS Institute", "Adresse, téléphone et courriel d'ERANOS Institute, à Nice."),
}
LEGAL = {  # fichier -> (titre, chapeau, fragment)
    "mentions-legales.html": ("Mentions légales", "Éditeur, propriété intellectuelle, données personnelles.", "mentions-legales.html"),
    "cgv.html": ("Conditions générales de vente", "Les conditions applicables aux formations et prestations d'ERANOS Institute.", "cgv.html"),
    "confidentialite.html": ("Politique de confidentialité", "Données personnelles et cookies.", "confidentialite.html"),
}
GROUP = {"fondateur": "eranos", "equipe": "eranos", "chaire": "eranos"}
DYNAMIC = ["home-shelf", "pub-list", "home-presta", "presta-list", "catalogue", "arts"]


def prerender(html):
    """Charge la page source et récupère le HTML des listes produites par le script."""
    from playwright.sync_api import sync_playwright

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    (ROOT / "_tmp.html").write_text(html, encoding="utf-8")
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
            pg = b.new_page()
            pg.goto("http://127.0.0.1:%d/_tmp.html" % srv.server_address[1])
            pg.wait_for_timeout(500)
            for i in DYNAMIC:
                out[i] = pg.evaluate("document.getElementById(%r).innerHTML" % i)
            out["amz"] = pg.evaluate("[...document.querySelectorAll('[data-amz]')].map(a=>[a.getAttribute('data-amz'),a.href])")
            b.close()
    finally:
        srv.shutdown()
        (ROOT / "_tmp.html").unlink()
    return out


def links(s):
    """Remplace les ancres de vues par des liens vers les pages."""
    s = re.sub(r'href="#prestations" data-jump="([\w-]+)"', r'href="prestations.html#\1"', s)
    for v, (f, _, _) in PAGES.items():
        s = s.replace('href="#%s"' % v, 'href="%s"' % f)
    return s


def main():
    src = (SRC / "site.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    js = re.search(r"<script>(.*?)</script>\s*</body>", src, re.S).group(1)
    bar = re.search(r'(<div class="bar">.*?</div>\s*</div>)\s*<main>', src, re.S).group(1)
    footer = re.search(r"(<footer>.*?</footer>)", src, re.S).group(1)
    main_html = re.search(r"<main>(.*?)</main>", src, re.S).group(1)
    fonts = "\n".join(re.findall(r'<link [^>]*fonts[^>]*>', src))

    dyn = prerender(src)
    for i in DYNAMIC:
        main_html, n = re.subn(r'(id="%s"[^>]*>)(</(?:div|ul)>)' % i, lambda m: m.group(1) + dyn[i] + m.group(2), main_html)
        assert n == 1, i
    for asin, href in dict(map(tuple, dyn["amz"])).items():
        main_html = main_html.replace('data-amz="%s" href="#"' % asin, 'href="%s"' % href)
    assert "data-amz" not in main_html

    views = dict(re.findall(r'<div class="view" id="v-([\w-]+)">(.*?)\n</div>\s*(?=<!--|$)', main_html, re.S))
    assert set(views) == set(PAGES), set(PAGES) ^ set(views)

    # feuille de style : les vues sont toujours visibles, plus le style des pages légales
    css = css.replace(".view{display:none}\n.view.on{display:block;animation:rise .7s cubic-bezier(.2,.7,.2,1)}", ".view{animation:rise .7s cubic-bezier(.2,.7,.2,1)}")
    css += """
.legaltxt{max-width:46em}
.legaltxt h2{font-size:28px;margin:44px 0 12px;padding-top:22px;border-top:1px solid var(--rule)}
.legaltxt h2:first-child{margin-top:0;border-top:0;padding-top:0}
.legaltxt p{margin-top:12px;font-size:16.5px}
.legaltxt ul{margin-top:12px;display:grid;gap:8px}
.legaltxt li{position:relative;padding-left:22px;font-size:16.5px}
.legaltxt li::before{content:"";position:absolute;left:0;top:.8em;width:9px;height:1.5px;background:var(--alp)}
.legaltxt a{color:var(--azure);text-underline-offset:4px}
.lnk{display:flex;gap:18px;flex-wrap:wrap}
"""
    (ROOT / "assets" / "site.css").write_text(css.strip() + "\n", encoding="utf-8")

    # script : contact, paysage, parallaxe, menu, apparition (les listes sont déjà dans le HTML)
    contact = js[js.index("/* ---------- contact ---------- */"):js.index("/* ---------- paysage")]
    contact = contact.replace('var mail = document.getElementById("mail");', 'var mail = document.getElementById("mail");\nif (mail){').rstrip() + "\n}\n\n"
    land = js[js.index("/* ---------- paysage"):js.index("/* ---------- vues ---------- */")]
    tail = """/* ---------- menu et apparition ---------- */
var navEl = document.getElementById("nav"), burger = document.getElementById("burger");
burger.addEventListener("click", function(){ var o = navEl.classList.toggle("open"); burger.setAttribute("aria-expanded", o ? "true" : "false"); });
var io = ("IntersectionObserver" in window) ? new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } }); }, {rootMargin:"0px 0px -8% 0px"}) : null;
document.querySelectorAll(".rv").forEach(function(el){ if (io) io.observe(el); else el.classList.add("in"); });
"""
    head_js = 'var CONTACT = ["alain.ruffion","hotmail.fr"].join("@");\n\n'
    (ROOT / "assets" / "site.js").write_text(head_js + contact + land + tail, encoding="utf-8")

    footer = links(footer).replace(
        '<span>Paysage : le lac Majeur vu d\'Ascona, dessin original</span>',
        '<span class="lnk"><a href="mentions-legales.html">Mentions légales</a><a href="cgv.html">CGV</a><a href="confidentialite.html">Confidentialité</a></span>')
    assert "mentions-legales.html" in footer
    bar = links(bar)

    def page(fname, title, desc, body, current):
        nav = bar
        if current:
            nav = nav.replace('<a href="%s">' % PAGES[current][0], '<a href="%s" aria-current="page">' % PAGES[current][0], 1) if current != "accueil" else nav
        url = DOMAIN + "/" + ("" if fname == "index.html" else fname)
        return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ERANOS Institute">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<link rel="icon" type="image/png" href="assets/rosace-light.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
%s
<link rel="stylesheet" href="assets/site.css">
</head>
<body>

%s

<main>
<div class="view on">%s
</div>
</main>

%s

<script src="assets/site.js"></script>
</body>
</html>
""" % (title, desc, url, title, desc, url, fonts, nav, body, footer)

    made = []
    for v, (fname, title, desc) in PAGES.items():
        body = links(views[v])
        if v == "contact":
            body = body.replace('<div class="legal rv">', '<p class="rv" style="margin-bottom:34px;display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn-ghost" href="mentions-legales.html">Mentions légales</a><a class="btn btn-ghost" href="cgv.html">Conditions générales de vente</a><a class="btn btn-ghost" href="confidentialite.html">Confidentialité</a></p>\n      <div class="legal rv">')
        (ROOT / fname).write_text(page(fname, title, desc, body, GROUP.get(v, v)), encoding="utf-8")
        made.append(fname)
    for i, (fname, (title, lede, frag)) in enumerate(LEGAL.items()):
        txt = (SRC / "legal" / frag).read_text(encoding="utf-8")
        body = """
  <header class="scene phead" data-seed="%d" data-h="380"><div class="veil"></div><div class="wrap">
    <p class="lab">Informations légales</p><h1>%s</h1>
    <p>%s</p>
  </div></header>
  <section class="s"><div class="wrap"><div class="legaltxt">
%s
  </div></div></section>""" % (151 + i * 12, title, lede, txt)
        (ROOT / fname).write_text(page(fname, title + " · ERANOS Institute", lede, body, None), encoding="utf-8")
        made.append(fname)

    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        "  <url><loc>%s/%s</loc></url>\n" % (DOMAIN, "" if f == "index.html" else f) for f in made) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text("User-agent: *\nDisallow: /_src/\n\nSitemap: %s/sitemap.xml\n" % DOMAIN, encoding="utf-8")
    print("pages :", ", ".join(made))


if __name__ == "__main__":
    sys.exit(main())
