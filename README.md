# Site ERANOS Institute

Site statique, sans compilation côté hébergeur : il suffit de servir la racine du dépôt.

- `*.html` à la racine : les quinze pages du site.
- `assets/` : feuille de style, script, logo, couvertures, portrait.
- `sitemap.xml`, `robots.txt` : pour les moteurs de recherche (domaine visé : www.eranosinstitute.com).
- `_src/` : la source. `site.html` contient toutes les rubriques en une page, `legal/` les textes légaux, `build.py` fabrique les pages.

Pour modifier le site : éditer `_src/site.html` ou `_src/legal/*.html`, puis lancer `python3 _src/build.py`.
