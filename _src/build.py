#!/usr/bin/env python3
"""Fabrique les pages du site à partir de _src/site.html (source en une page) et de _src/legal/.

Usage : python3 _src/build.py   (depuis la racine du dépôt ; nécessite playwright et Chrome)
Sortie : *.html à la racine, assets/site.css, assets/site.js, sitemap.xml, robots.txt
"""
import functools, html, http.server, json, pathlib, re, socketserver, sys, threading

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
    "reglement-interieur.html": ("Règlement intérieur", "Les règles applicables à tous les stagiaires pendant leur formation.", "reglement-interieur.html"),
    "livret-accueil.html": ("Livret d'accueil du stagiaire", "Ce qu'il faut savoir avant, pendant et après une formation.", "livret-accueil.html"),
    "mentions-legales.html": ("Mentions légales", "Éditeur, hébergement, propriété intellectuelle, données personnelles.", "mentions-legales.html"),
    "cgv.html": ("Conditions générales de vente", "Les conditions applicables aux formations et prestations d'ERANOS Institute.", "cgv.html"),
    "confidentialite.html": ("Politique de confidentialité", "Données personnelles et cookies.", "confidentialite.html"),
}
GROUP = {"fondateur": "eranos", "equipe": "eranos", "chaire": "eranos"}
DYNAMIC = ["home-shelf", "pub-list", "home-presta", "presta-list", "arts"]
MAJ = "14 novembre 2026"  # date de mise à jour affichée sur les fiches

CATS = {  # catalogue -> (titre, présentation, public)
    "fondamentaux": ("Connaissances et outils sur les fondamentaux des métiers du travail social et socio-éducatif",
                     "Ces métiers se renouvellent sans cesse, mais des fondamentaux en sciences humaines ont fait la qualité d'intervention des professionnels expérimentés. Ils sont remis à jour et replacés dans l'actualité sociale, politique et économique.",
                     "Professionnels du travail social et socio-éducatif : éducateurs, médiateurs, animateurs, assistants de service social, encadrants, agents des collectivités et des associations."),
    "specialisees": ("Compétences spécialisées en travail social et socio-éducatif",
                     "Le contexte se complexifie pendant que les sciences humaines avancent. Ces modules aident à devancer les situations, à se protéger et à cultiver des formes de résilience individuelles et collectives.",
                     "Professionnels du travail social, de l'éducation, de la médiation, de la santé, de la justice, des collectivités et de l'entreprise."),
    "positive": ("La psychologie positive, l'éducation positive et l'éducation critique à la spiritualité",
                 "Les formations fondamentales et innovantes de l'institut, issues de ses recherches.",
                 "Professionnels de l'éducation, de l'insertion, du travail social, de la santé et de l'entreprise ; dirigeants et managers."),
}


def e(s):
    return html.escape(s, quote=False)


def heures(d):
    n = [int(x) for x in re.findall(r"\d+", d)]
    if not n:
        return d
    h = " à ".join(str(x * 7) for x in n) + " heures"
    return "%s (%s)" % (d, h)


def items(lst, cls="dots"):
    """Rend une liste de blocs [type, texte] : les titres deviennent des intertitres."""
    out, cur = [], []

    def flush():
        if cur:
            out.append('<ul class="%s">%s</ul>' % (cls, "".join("<li>%s</li>" % e(x) for x in cur)))
            cur.clear()
    for k, x in lst:
        if k == "h":
            flush()
            out.append('<p class="sub2">%s</p>' % e(x))
        else:
            cur.append(x)
    flush()
    return "\n".join(out)


def catalogue(mods):
    out = []
    for c, (titre, pres, _) in CATS.items():
        out.append('<div class="cat"><header><h2>%s</h2><p>%s</p></header>' % (e(titre), e(pres)))
        groupes = []
        for m in mods:
            if m["cat"] == c and m["groupe"] not in groupes:
                groupes.append(m["groupe"])
        for g in groupes:
            out.append("<h4>%s</h4><ul class=\"mods\">" % e(g))
            for m in mods:
                if m["cat"] == c and m["groupe"] == g:
                    out.append('<li class="lk"><a href="%s"><b>%s</b><span>%s</span><em>%s</em></a></li>' % (m["file"], m["num"], e(m["titre"]), e(m["duree"])))
            out.append("</ul>")
        out.append("</div>")
    return "\n".join(out)


def fiche(m, prev, nxt):
    titre_cat, _, public = CATS[m["cat"]]
    prereq = e(m["prereq"]) if m["prereq"] else "Aucun"
    blk = []
    if m["intro"]:
        blk.append('<div class="blk"><h4>À qui s\'adresse ce module</h4>%s</div>' % "".join("<p>%s</p>" % e(x) for _, x in m["intro"]))
    if m["obj"]:
        blk.append('<div class="blk"><h4>Objectifs pédagogiques</h4><p>Ce que le participant aura acquis à l\'issue de la formation :</p>%s</div>' % items(m["obj"]))
    if m["buts"]:
        blk.append('<div class="blk"><h4>Finalités du module</h4>%s</div>' % items(m["buts"]))
    if m["contenu"]:
        blk.append('<div class="blk"><h4>Contenu</h4>%s</div>' % items(m["contenu"]))
    outils = items(m["outils"]) if m["outils"] else ""
    blk.append('<div class="blk"><h4>Méthodes mobilisées</h4><p>Méthode active : études de cas concrets, exposés interactifs, temps d\'échange et de partage d\'expériences.</p>%s</div>' % outils)
    ev = items(m["eval"]) if m["eval"] else ""
    blk.append('<div class="blk"><h4>Modalités d\'évaluation</h4>%s<ul class="dots"><li>Recueil des besoins et positionnement avant la session.</li><li>Questionnaire de satisfaction en fin de session, puis questionnaire de suivi dans les deux mois.</li><li>Attestation de fin de formation remise à chaque participant.</li></ul></div>' % ev)
    blk.append('<div class="blk"><h4>Modalités et délais d\'accès</h4><p>Inscription sur demande, par le formulaire de contact ou par téléphone. L\'institut répond sous 24 à 72 heures, puis établit un devis et une convention de formation. L\'inscription doit être confirmée au plus tard 15 jours avant le début de la session ; les dates sont fixées avec le commanditaire.</p></div>')
    blk.append('<div class="blk"><h4>Accessibilité aux personnes en situation de handicap</h4><p>Cette formation peut être adaptée. Signalez votre situation dès la prise de contact : nous étudions avec vous les aménagements possibles (rythme, supports, lieu) et vous orientons si besoin vers l\'Agefiph, le FIPHFP, Cap emploi ou la MDPH.</p></div>')
    blk.append('<div class="blk"><h4>Indicateurs de résultats</h4><p>Le nombre de stagiaires formés et le taux de satisfaction de ce module sont communiqués sur demande. Ils sont calculés à partir des questionnaires remis en fin de session.</p></div>')
    if m.get("note"):
        blk.append('<div class="blk"><p class="aside">%s</p></div>' % e(m["note"]))
    blk.append('<div class="blk" style="display:flex;gap:12px;flex-wrap:wrap"><button class="btn btn-fir" type="button" data-write="Formation : module %s, %s">Demander cette formation <i>→</i></button><a class="btn btn-ghost" href="formations.html">Retour au catalogue</a></div>' % (m["num"], e(m["titre"]).replace('"', "&quot;")))
    facts = [("Durée", heures(m["duree"])), ("Public", public), ("Prérequis", prereq),
             ("Format", "Présentiel, en intra ou en inter. Contenu et organisation adaptables à votre structure."),
             ("Tarif", "Sur devis, selon le format et le nombre de participants. Prix nets de taxe : l'association n'est pas assujettie à la TVA."),
             ("Intervenant", "Formateurs d'ERANOS Institute, sous la responsabilité pédagogique d'Alain Ruffion."),
             ("Validation", "Formation non certifiante. Attestation de fin de formation."),
             ("Contact", "Alain Ruffion, +33 6 29 76 83 90")]
    nav = '<p class="pn">%s%s</p>' % ('<a href="%s">← Module %s</a>' % (prev["file"], prev["num"]) if prev else "<span></span>", '<a href="%s">Module %s →</a>' % (nxt["file"], nxt["num"]) if nxt else "")
    return """
  <header class="scene phead" data-seed="%d" data-h="400"><div class="veil"></div><div class="wrap">
    <p class="lab">Formation · module %s</p><h1>%s</h1>
    <p>%s · %s</p>
  </div></header>
  <section class="s"><div class="wrap">
    <article class="pre fiche">
      <div><dl class="facts">%s</dl><p class="maj">Fiche mise à jour le %s.</p></div>
      <div>%s</div>
    </article>
    %s
  </div></section>""" % (200 + m["n"] * 3 + len(m["num"]), m["num"], e(m["titre"]), e(m["duree"]), e(titre_cat),
                         "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (a, e(b)) for a, b in facts), MAJ, "\n".join(blk), nav)


DIALOG = """<button class="fab" type="button" data-write="">Nous écrire</button>
<dialog id="dlg" aria-labelledby="dlg-t">
  <form id="wform" novalidate>
    <button class="x" type="button" id="dlg-x" aria-label="Fermer">×</button>
    <h2 id="dlg-t">Écrire à ERANOS Institute</h2>
    <p class="hint">Votre message arrive directement à l'institut. Réponse sous 24 à 72 heures.</p>
    <div class="two">
      <label for="f-name">Nom et prénom<input id="f-name" name="name" type="text" autocomplete="name" required></label>
      <label for="f-email">Courriel<input id="f-email" name="email" type="email" autocomplete="email" required></label>
    </div>
    <div class="two">
      <label for="f-org">Structure (facultatif)<input id="f-org" name="structure" type="text" autocomplete="organization"></label>
      <label for="f-tel">Téléphone (facultatif)<input id="f-tel" name="telephone" type="tel" autocomplete="tel"></label>
    </div>
    <label for="f-obj">Objet<input id="f-obj" name="objet" type="text" required placeholder="Formation, prestation, programme Fudōshin, autre"></label>
    <label for="f-msg">Message<textarea id="f-msg" name="message" rows="5" required></textarea></label>
    <input class="hp" type="text" name="_honey" tabindex="-1" autocomplete="off" aria-hidden="true">
    <p class="rgpd">Ces informations servent uniquement à vous répondre. Voir la <a href="confidentialite.html">politique de confidentialité</a>.</p>
    <div class="row"><button class="btn btn-fir" type="submit" id="f-send">Envoyer le message <i>→</i></button><span id="f-status" role="status" aria-live="polite"></span></div>
  </form>
</dialog>"""


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

    mods = json.loads((SRC / "formations.json").read_text(encoding="utf-8"))
    main_html, n = re.subn(r'(id="catalogue"[^>]*>)(</div>)', lambda m: m.group(1) + catalogue(mods) + m.group(2), main_html)
    assert n == 1
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
.legaltxt h3{font-size:21px;margin:26px 0 6px}
.legaltxt ul{margin-top:12px;display:grid;gap:8px}
.legaltxt li{position:relative;padding-left:22px;font-size:16.5px}
.legaltxt li::before{content:"";position:absolute;left:0;top:.8em;width:9px;height:1.5px;background:var(--alp)}
.legaltxt a{color:var(--azure);text-underline-offset:4px}
.lnk{display:flex;gap:18px;flex-wrap:wrap}
.mods li.lk{display:block;padding:0}
.mods li.lk:hover{padding:0}
.mods li.lk a{display:grid;grid-template-columns:54px minmax(0,1fr) auto;gap:14px;align-items:baseline;padding:13px 10px 13px 0;color:inherit;text-decoration:none;transition:padding .25s}
.mods li.lk a:hover{padding-left:10px}
.mods li.lk a:hover span{color:var(--azure);text-decoration:underline;text-underline-offset:4px}
.fiche{border-top:2px solid var(--ink) !important}
.fiche>div{min-width:0}
.fiche .blk,.fiche dd{overflow-wrap:anywhere}
.fiche .sub2{font:400 20px/1.3 var(--display);margin:16px 0 6px}
.fiche .blk p+ul,.fiche .blk ul+ul{margin-top:8px}
.fiche .facts div{grid-template-columns:104px minmax(0,1fr)}
.maj{margin-top:16px;font-size:14px;color:var(--ink-soft)}
.pn{display:flex;justify-content:space-between;gap:16px;margin-top:10px;padding-top:22px;border-top:1px solid var(--rule);font:500 13px/1 var(--body);letter-spacing:.18em;text-transform:uppercase}
.pn a{text-decoration:none;color:var(--azure)}
.pn a:hover{text-decoration:underline;text-underline-offset:5px}
.fab{position:fixed;right:22px;bottom:22px;z-index:60;border:0;cursor:pointer;background:var(--glacier);color:var(--abyss);font:500 13px/1 var(--body);letter-spacing:.16em;text-transform:uppercase;padding:16px 22px;border-radius:999px;box-shadow:0 16px 34px -12px rgba(8,32,47,.65);transition:transform .25s cubic-bezier(.2,.7,.2,1)}
.fab:hover{transform:translateY(-3px)}
dialog#dlg{border:0;padding:0;width:min(640px,calc(100vw - 28px));max-height:calc(100vh - 28px);background:var(--paper);color:var(--ink);box-shadow:0 40px 90px -20px rgba(8,32,47,.8);border-top:3px solid var(--azure)}
dialog#dlg::backdrop{background:rgba(8,32,47,.72);backdrop-filter:blur(4px)}
dialog#dlg[open]{animation:rise .35s cubic-bezier(.2,.7,.2,1)}
#wform{position:relative;padding:34px 34px 30px;display:grid;gap:16px}
#wform h2{font-size:32px;padding-right:40px}
#wform .hint{color:var(--ink-soft);font-size:16px;margin-top:-8px}
#wform .two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
#wform label{display:grid;gap:6px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);font-weight:500}
#wform input,#wform textarea{font:400 17px/1.4 var(--body);letter-spacing:0;text-transform:none;color:var(--ink);background:#fff;border:1px solid var(--rule);padding:12px 14px;border-radius:2px;width:100%}
#wform input:focus,#wform textarea:focus{outline:2px solid var(--azure);outline-offset:1px}
#wform textarea{resize:vertical;min-height:120px}
#wform .hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
#wform .rgpd{font-size:14px;color:var(--ink-soft)}
#wform .rgpd a{color:var(--azure)}
#wform .row{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
#wform .x{position:absolute;right:16px;top:14px;border:0;background:none;font:400 30px/1 var(--body);color:var(--ink-soft);cursor:pointer;padding:6px 10px}
#f-status{font-size:15.5px}
#f-status.ok{color:var(--fir)}
#f-status.ko{color:#a3352a}
@media (max-width:560px){#wform{padding:28px 20px 24px}#wform .two{grid-template-columns:1fr}.fab{right:14px;bottom:14px}}
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

/* ---------- boîte de dialogue : écrire à l'institut ---------- */
(function(){
  var dlg = document.getElementById("dlg"), form = document.getElementById("wform"), st = document.getElementById("f-status"), send = document.getElementById("f-send");
  if (!dlg || !form) return;
  document.addEventListener("click", function(ev){
    var b = ev.target.closest ? ev.target.closest("[data-write]") : null;
    if (!b) return;
    ev.preventDefault();
    var s = b.getAttribute("data-write");
    if (s) document.getElementById("f-obj").value = s;
    st.textContent = ""; st.className = "";
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    document.getElementById("f-name").focus();
  });
  document.getElementById("dlg-x").addEventListener("click", function(){ dlg.close(); });
  dlg.addEventListener("click", function(ev){ if (ev.target === dlg) dlg.close(); });
  form.addEventListener("submit", function(ev){
    ev.preventDefault();
    if (!form.checkValidity()){ form.reportValidity(); return; }
    var d = {}; new FormData(form).forEach(function(v, k){ d[k] = v; });
    if (d._honey){ return; }
    d._subject = "Site ERANOS Institute : " + d.objet;
    d._template = "table";
    d._replyto = d.email;
    send.disabled = true; st.className = ""; st.textContent = "Envoi en cours…";
    fetch("https://formsubmit.co/ajax/" + CONTACT, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(d) })
      .then(function(r){ return r.json().then(function(j){ return { ok: r.ok, j: j }; }); })
      .then(function(r){
        if (r.ok && String(r.j.success) === "true"){ st.className = "ok"; st.textContent = "Message envoyé. Merci, nous vous répondons sous 24 à 72 heures."; form.reset(); }
        else { throw new Error("refus"); }
      })
      .catch(function(){ st.className = "ko"; st.textContent = "L'envoi n'a pas abouti. Écrivez-nous à " + CONTACT + " ou appelez le +33 6 29 76 83 90."; })
      .then(function(){ send.disabled = false; });
  });
})();
"""
    head_js = 'var CONTACT = ["alain.ruffion","hotmail.fr"].join("@");\n\n'
    (ROOT / "assets" / "site.js").write_text(head_js + contact + land + tail, encoding="utf-8")

    footer = links(footer).replace(
        '<span>Paysage : le lac Majeur vu d\'Ascona, dessin original</span>',
        '<span class="lnk"><a href="livret-accueil.html">Livret d\'accueil</a><a href="reglement-interieur.html">Règlement intérieur</a><a href="mentions-legales.html">Mentions légales</a><a href="cgv.html">CGV</a><a href="confidentialite.html">Confidentialité</a></span>')
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

%s

<script src="assets/site.js"></script>
</body>
</html>
""" % (title, desc, url, title, desc, url, fonts, nav, body, footer, DIALOG)

    for old in ROOT.glob("formation-*.html"):
        old.unlink()
    made = []
    for v, (fname, title, desc) in PAGES.items():
        body = links(views[v])
        if v == "contact":
            body = body.replace('<a class="btn btn-glacier" id="mailbtn" href="#">Ouvrir un courriel</a>', '<button class="btn btn-glacier" type="button" data-write="">Écrire un message</button>\n          <a class="btn btn-ghost" id="mailbtn" href="#">Ouvrir un courriel</a>')
            body = body.replace("<h3>Un message en deux clics</h3>", "<h3>Un message, directement d'ici</h3>")
            body = body.replace('<div class="legal rv">', '<p class="rv" style="margin-bottom:34px;display:flex;gap:12px;flex-wrap:wrap"><a class="btn btn-ghost" href="livret-accueil.html">Livret d\'accueil</a><a class="btn btn-ghost" href="reglement-interieur.html">Règlement intérieur</a><a class="btn btn-ghost" href="mentions-legales.html">Mentions légales</a><a class="btn btn-ghost" href="cgv.html">Conditions générales de vente</a><a class="btn btn-ghost" href="confidentialite.html">Confidentialité</a></p>\n      <div class="legal rv">')
        (ROOT / fname).write_text(page(fname, title, desc, body, GROUP.get(v, v)), encoding="utf-8")
        made.append(fname)
    for i, m in enumerate(mods):
        body = fiche(m, mods[i - 1] if i else None, mods[i + 1] if i + 1 < len(mods) else None)
        desc = "Formation ERANOS Institute, module %s : %s. Durée : %s. Objectifs, contenu, méthodes, évaluation, accès et tarif." % (m["num"], m["titre"], m["duree"])
        (ROOT / m["file"]).write_text(page(m["file"], "%s · formation ERANOS Institute" % m["titre"], desc.replace('"', "'"), body, "formations"), encoding="utf-8")
        made.append(m["file"])
    for i, (fname, (title, lede, frag)) in enumerate(LEGAL.items()):
        txt = (SRC / "legal" / frag).read_text(encoding="utf-8")
        body = """
  <header class="scene phead" data-seed="%d" data-h="380"><div class="veil"></div><div class="wrap">
    <p class="lab">Informations pratiques et légales</p><h1>%s</h1>
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
