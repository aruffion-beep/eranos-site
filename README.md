# Site ERANOS Institute

Site statique, mis en ligne automatiquement par GitHub Pages à chaque envoi sur `main`.

- `*.html` à la racine : les pages du site, dont une fiche par module de formation (`formation-NN-….html`).
- `assets/` : feuille de style, script, logo, couvertures, portrait.
- `sitemap.xml`, `robots.txt` : pour les moteurs de recherche (domaine visé : www.eranosinstitute.com).
- `_src/` : la source.
  - `site.html` : toutes les rubriques en une page.
  - `formations.json` : les fiches de formation (catalogue 2025).
  - `legal/` : textes légaux, règlement intérieur, livret d'accueil.
  - `build.py` : fabrique les pages.

Pour modifier le site : éditer les fichiers de `_src/`, puis lancer `python3 _src/build.py`.
Le formulaire de contact passe par FormSubmit (aucun serveur à maintenir).
