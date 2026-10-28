---
name: traduction-regles-jeu
description: Traduit en français (et en anglais si demandé) un livret de règles de jeu de société en PDF, depuis n'importe quelle langue, en conservant la mise en page — polices, images, icônes, tableaux, positions — et produit un `*_FR.pdf` ; gère aussi les livrets scannés. À utiliser dès que l'utilisateur demande de traduire des règles, un livret, un rulebook ou un PDF de jeu (même « traduis-moi ce PDF » ou un nom comme `xxx_rulebook.pdf`, `Spielregel.pdf`), ou de corriger une traduction déjà faite ainsi. Fait aussi, à la demande, l'aide-mémoire d'une page d'un jeu (mise en place, tour de jeu, score) à poser sur la table.
---

# Traduction de livrets de règles (toutes langues → FR, mise en page conservée)

L'utilisateur parle français, joue à des jeux de plis et ne touche pas aux scripts : il veut un PDF français
qui ressemble trait pour trait à l'original. Réponds-lui en français, sans jargon technique inutile.

## Préférences de l'utilisateur
- Ne jamais traduire le titre du jeu ni les noms de variantes.
- Noms de cartes / personnages : dans la langue d'origine, français entre parenthèses dans les titres
  (« The Bride (La Fiancée) ») ; nom d'origine aussi dans le texte. Alphabet non latin : nom imprimé en lettres
  latines s'il existe, sinon nom anglais officiel, sinon romanisation.
- Vocabulaire cohérent entre jeux : `references/glossaire.md` (pli, entamer, fournir, atout, couleur demandée…).
- Typographie française : « », espaces insécables avant ; : ! ? (posées par le moteur), décimales à virgule.
- Signaler les compromis : police réduite, phrases condensées, texte des illustrations non traduit.

## Environnement
Python 3 avec pymupdf et fonttools (`-X utf8` toujours) ; winrt pour la lecture des scans. Dossiers, noms et
index : `references/dossiers.md` (à lire au premier jeu d'une session) — dépôt `A traduire/`, outils
`_outils/<Jeu>/`, livrets livrés dans `<Jeu>/`, index `_outils/LISEZMOI.md` (à chercher avec `grep`), détail d'un
jeu dans `_outils/<Jeu>/NOTES.md`. Scripts : `scripts/` ; `preparer.py` copie ceux qu'il faut.

## Quel livret traduire
Chemin donné : l'utiliser ; sinon le dossier de dépôt. **Plusieurs PDF** : les lister (regrouper ceux d'un même
jeu), coût estimé ~150-200 k jetons par livret, demander : tout un par un, ou un livret précis ? Rien avant la
réponse. Tout : un livret à la fois, sans parallélisme (index commun), court bilan après chacun, puis enchaîner ;
un livret à problème est mis de côté et signalé.

## Méthode
0. **Règle venue d'une page web** (PDF fait par recherche-regles-jeu depuis une page web ou Notion, d'après
   `_outils/<Jeu>/NOTES.md`, ou lien donné par l'utilisateur) : ne pas suivre les étapes ci-dessous ;
   traduire la page elle-même et la remettre en PDF — `references/page-web.md`.
1. **Préparer** : `python -X utf8 <skill>/scripts/preparer.py "<livret.pdf>" "<Nom du jeu>"` (nom, dossier
   d'outils, texte ou scan, scripts et modèle de spec, planche, `blocks.txt`, polices, langue —
   `references/langues.md` —, OCR des scans → `zones.py`, jeux traduits aux mêmes polices). Regarder la planche,
   annoncer langue, pages, type. Nom en écriture non latine : `--nom-fichier` (`references/dossiers.md`).
   - `NOTES.md` déjà présente (recherche-regles-jeu) : réutiliser ses liens.
   - **Jeu japonais** : fiche Tokyo Game Market et manuel de l'auteur avant le spec ; règle traduite ou de fan :
     comparer à l'original — `references/source.md`.
   - **Scan** : demander le rendu (recouvrir / côte à côte / recomposer) → `references/scan.md`.
   - **Version anglaise aussi** : une seule spec, textes `X("français", "english")` (en-tête des modèles) ;
     `LANGUE=en` construit et relit l'anglais, `livrer.py` livre `<nom>_EN.pdf`.
   La suite concerne les livrets à texte.
2. **Polices** (`references/polices.md`) : celles d'un jeu proche, sinon des remplaçantes (`polices.py glyphes /
   planche / largeur`) dans `ff/` ; en tête de `spec.py` : `CSS`, `BODY`, `CODE`, `SIZE_K`, si besoin `COLUMNS`.
3. **Écrire `spec.py`** d'après `blocks.txt` (le lire en entier ; « [N icône(s)] » = autant de `{}`) : un flux `F`
   par zone de texte, paragraphes `P` / `C` / `L` / `T`, `maxy` = limite basse ; format dans l'en-tête du modèle.
   Colonnes, étapes sur pastille et coupures « Bleu | 19 » sont gérées seules ; `x1=`, `fix=`, `COLUMNS` pour un
   cas raté. Lire `references/pieges.md` avant. Retouches du spec avec l'outil d'édition (pas `sed`).
4. **Construire** : `python -X utf8 build.py sortie.pdf`. « ERREUR : » = spec à corriger. Journal : « police
   réduite », « DÉBORDE », icônes, **« TEXTE NON TRADUIT »** (traduire, ou `IGNORE`), **« À VÉRIFIER »**.
   - **Livret à fond sombre** : une version économe en encre à imprimer est possible **en plus**, jamais
     d'office — seulement si l'utilisateur la demande : `references/encre.md`.
5. **Relire** — deux agents lancés **en parallèle** (un message, deux appels Agent). Messages **courts** : les
   agents ont leur méthode ; donner seulement les chemins, le vocabulaire choisi en une ligne, les endroits à
   regarder et les particularités (spec bilingue, scan, rendu recomposé) :
   - `relecteur-texte` : dossier d'outils + dossier de la skill ;
   - `relecteur-visuel` : dossier d'outils, PDF d'origine, PDF construit(s), journal, endroits prioritaires.
   Agents non installés : `general-purpose`, `model: "sonnet"`, message = contenu de `agents/relecteur-….md`
   (sans l'en-tête) + chemins. Rapports = propositions : vérifier chaque point avant de corriger ; petite
   correction → regarder soi-même la seule zone modifiée, sans relancer les agents.
6. **Livrer** : écrire `NOTES.md` (langue d'origine, éditeur, type, polices, vocabulaire, choix, compromis,
   astuces ; garder « Sources »), puis `python -X utf8 livrer.py "<Ludothèque>/_outils/<Jeu>"` (`--remplacer`
   seulement avec l'accord de l'utilisateur ; `--encre` livre en plus `<nom>_FR_encre.pdf`) : original déplacé,
   `SRC` mis à jour, dossier allégé, reconstruction, `<nom>_FR.pdf` (et `_EN.pdf` si spec bilingue), index.
   Sans spec.py (page web recréée, livret recomposé) : `livrer.py "<outils>" --original "<livret>"
   --pdf <fr.pdf> [--pdf-en <en.pdf>] [--pdf-encre <encre.pdf>] --type "<type>"`.
   Termes généraux nouveaux → `references/glossaire.md`. Résumer : fichiers, vocabulaire, compromis.
   - **Livret d'au moins 10 Mo** (`livrer.py` le signale) : proposer une version allégée pour Discord, jamais
     la faire d'office — `references/alleger.md` ; le livret en pleine qualité est gardé tel quel.

## Aide-mémoire d'une page (à la demande)
« Fais l'aide-mémoire de <jeu> » : une page A4 en français (mise en place, tour de jeu, fin de partie et score,
pièges), d'après le texte du livret, rangée en `<Jeu>/<nom>_aide-memoire.pdf` — `references/aide-memoire.md`.
Jamais d'office ; après une traduction, ne pas la proposer à chaque fois.

## Économiser les jetons
- Images : une planche à 70-80 dpi pour voir, puis seulement des **zooms sur une zone** (`clip=`) pour vérifier ;
  jamais une page entière à plus de 110 dpi ; pas de nouvelle vue de toute la page après une petite correction.
- Texte : lire `blocks.txt` / `zones.py` / les journaux plutôt que des images ; filtrer les journaux (`grep`
  DÉBORDE, ERREUR, VÉRIFIER) ; index et notes : `grep`, pas de lecture intégrale.
- Spec : écrit d'un seul coup, puis retouches ciblées avec l'outil d'édition (pas de réécriture complète).
- Agents : seulement pour la relecture (étape 5) ; tout le reste ici.

## Correction d'une traduction existante
Lire `NOTES.md`, modifier `spec.py`, relancer `build.py` (ou `scan.py`), regarder la zone modifiée, puis
`livrer.py … --remplacer` (avec l'accord de l'utilisateur pour remplacer le `_FR.pdf`).
