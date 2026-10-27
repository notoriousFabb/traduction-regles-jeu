# Version économe en encre (fond sombre retiré)

Un livret à fond noir ou très sombre vide une cartouche à l'impression. Cette option construit **en plus** du
livret normal un second PDF, même mise en page, prêt à imprimer : fond blanc, texte foncé.

**Elle n'est jamais faite d'office** : seulement si l'utilisateur la demande (« imprimable », « économe en
encre », « ink friendly », « ça va me vider la cartouche »). Le livret normal reste le livret de référence ;
la version encre vient à côté, avec `_encre` dans son nom.

## Construire
Livret à texte, après la construction normale :
```
python -X utf8 build.py sortie_encre.pdf --fond-clair
```
Livret recomposé à neuf (`references/recomposer.md`) :
```
python -X utf8 noir.py fr sortie_encre.pdf --clair
```

## Livrer
```
python -X utf8 livrer.py "<Ludothèque>/_outils/<Jeu>" --encre
```
livre `<nom>_FR.pdf` **et** `<nom>_FR_encre.pdf`, et note « + encre » dans la colonne Type de l'index.
Sans spec.py (livret recomposé, page web) : `livrer.py … --pdf sortie.pdf --pdf-encre sortie_encre.pdf`.

## Ce que fait le traitement (`encre.py`)
Page par page, et **seulement sur les pages jugées sombres** (clarté médiane basse ; une page déjà claire est
laissée telle quelle, le journal le dit) :
- l'**image** qui couvre la page n'est plus peinte : le papier blanc reste ;
- les grands **aplats** sombres qui couvrent la page deviennent du blanc franc (aucune encre) ;
- toute autre couleur voit sa **clarté inversée à teinte constante** : filet clair → filet foncé, pastille
  sombre → pastille claire, titre jaune clair → jaune foncé ;
- les couleurs de **texte** sont en plus assombries tant que le contraste avec le blanc est insuffisant, sinon
  un titre clair resterait pâle et illisible une fois le fond blanc ;
- les **images gardent leurs couleurs** : illustrations, logos et pictogrammes sont imprimés tels quels. Seul
  le fond est retiré. Une illustration sombre reste sombre : c'est voulu, l'économie vient du fond.

Le texte français est posé dans la couleur inversée de l'original, donc un texte blanc sur fond noir devient
noir sur blanc sans rien changer au spec.

## Vérifier
Dans le journal, une ligne par page : `page N : fond clair — … image(s) de fond retirée(s), … aplat(s) de fond
blanchi(s), … couleur(s) inversée(s)`. Regarder ensuite **une** page au zoom (`side.py`), pas tout le livret.

Deux mentions à lire :
- `À VÉRIFIER : … image(s) de fond NON retirée(s)` : le fond est posé avec une matrice tournée ou inclinée et
  n'a pas été reconnu — la page restera sombre, le dire à l'utilisateur.
- `… couleur(s) d'un espace particulier laissée(s) telle(s) quelle(s)` : couleurs d'un ton direct (Pantone) ou
  d'un espace à une composante, laissées intactes faute de pouvoir les interpréter sans risque. Quelques-unes
  ne gênent pas ; beaucoup, et la page gardera des zones sombres.

## Limites
- **Livrets scannés** (`scan.py`) : non couvert. Le fond EST l'image scannée ; l'éclaircir demanderait de
  retoucher le scan lui-même. `livrer.py --encre` refuse et le dit.
- Un fond fait de **nombreux petits pavés** sombres (et non d'un seul aplat) est éclairci mais pas blanchi : il
  restera un gris très clair, qui consomme un peu d'encre.
- Un crochet `AVANT_TEXTE` du spec est traité comme le reste de la page : ce qu'il dessine est éclairci avec
  elle, sans rien changer au spec.
