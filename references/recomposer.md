# Recomposer un livret à neuf (sans l'image d'origine)

Troisième rendu pour un **scan** (à proposer avec « recouvrir » et « côte à côte », voir `scan.md`), et seul
rendu possible quand l'original n'est pas réutilisable. À recommander pour un **scan papier de mauvaise qualité**
(livret plié, froissé, photographié de travers) : recouvrir y laisse des aplats et des plis visibles, et
l'utilisateur a préféré une page propre (CMYK : « je veux bien un fond noir, mais pas l'image scannée »).

## Principe
On réécrit tout le livret : même format, même découpage (volets d'un dépliant, colonnes), mêmes couleurs de fond
et de texte, titres, encadrés et numéros de volet redessinés ; **aucune image du scan**. Logo, pictogrammes et
illustrations sont remplacés par du texte (le dire à l'utilisateur), ou découpés proprement dans l'original
s'il les veut (`icone.py`).

## Outils
`exemples/recomposer/` de la skill : `noir.py` (moteur) et `textes.py` (le texte, français et anglais côte à
côte : `T("fr", "en")`) — l'exemple de CMYK (dépliant de 12 volets, 2 pages, fond noir). Les copier dans
`_outils/<Jeu>/`, puis adapter :
- `W, H` (format des pages, en points), `COLS`, `ROWS` (grille des volets), `M` (marge), `BG`, `FG` ;
- polices (`CSS`, fichiers dans `ff/`) ;
- blocs : `("h", titre)` section, `("rule", titre)` petit titre entre filets, `("sub", html)` sous-titre,
  `("p", html)` paragraphe, `("li", html)` puce, `("box", titre, html)` encadré à titre sur le cadre,
  `("sp", n)` espace, `("logo",)` / `("fin",)` page de titre et crédits (à réécrire pour chaque jeu).
Une seule taille de texte pour tout le livret : la plus grande qui tient dans chaque volet (le journal la donne).
Construire : `python -X utf8 noir.py fr sortie.pdf` puis `noir.py en sortie_en.pdf`. Version économe en encre
à imprimer (fond blanc), si l'utilisateur la demande : `noir.py fr sortie_encre.pdf --clair` (`encre.md`).

## Relire et livrer
- Relecture : le relecteur texte compare `textes.py` (FR et EN) au texte d'origine — relu à la main sur les
  agrandissements de `grille.py` et mis dans `zones.py` (l'OCR d'un scan froissé est très fautif) ; le relecteur
  visuel compare la recomposition à l'original volet par volet (contenu, ordre, rien d'oublié).
- Livrer : `livrer.py "<outils>" --original "<livret>" --pdf sortie.pdf [--pdf-en sortie_en.pdf]
  --type "recomposé"` (pas de spec.py). Noter dans NOTES.md comment reconstruire.
