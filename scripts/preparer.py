"""Démarre la traduction d'un livret : un seul appel au lieu d'une dizaine d'étapes.
Usage : python -X utf8 preparer.py "<chemin du livret.pdf>" "<Nom du jeu>" [--langue-ocr de-DE]
                                   [--nom-fichier "<nom en lettres latines>"]
(scan sans --langue-ocr : lu en japonais si Windows le sait et que le texte en est, sinon en anglais, ou à défaut
dans une autre langue à alphabet latin installée)

- livret nommé en écriture non latine (japonais, chinois…) : refusé sans --nom-fichier, qui le renomme sur place ;
- nettoie le nom du jeu pour Windows (virgules, ! et caractères interdits retirés) ;
- crée <Ludothèque>/_outils/<Jeu>/ (Ludothèque = dossier parent de « A traduire » ou du
  dossier de jeu <Ludothèque>/<Jeu>/ s'il contient déjà _outils, sinon dossier du PDF) ;
- détecte un livret scanné (pas de texte visible : pages-images, avec ou sans couche OCR invisible, ou lettres en
  tracés vectoriels → VECTEUR = True) et copie les bons scripts + le modèle de spec (SRC déjà rempli ;
  version anglaise possible dans la même spec : textes X("fr", "en"), voir l'en-tête du modèle) ;
- livret à texte : planche d'aperçu, inventaire blocks.txt, extraction et contrôle des polices, devine la langue ;
- livret scanné : planche d'aperçu et lecture automatique du texte (ocr.py -> zones.py) si la langue est installée ;
- cherche dans l'index et les NOTES.md des jeux déjà traduits ceux qui utilisent les mêmes polices.
Affiche un résumé à lire avant d'écrire le spec."""
import json, os, re, shutil, subprocess, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_SCRIPTS = ["build.py", "commun.py", "controle.py", "dump.py", "polices.py", "side.py", "ranger.py",
                "livrer.py", "relecture.py"]
SCAN_SCRIPTS = ["scan.py", "controle.py", "grille.py", "bandes.py", "icone.py", "side.py", "ranger.py", "livrer.py",
                "ocr.py", "relecture.py"]
SYMBOLS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "seguisym.ttf")  # ①❶◆★ des scans
NON_LATIN = re.compile(r"[Ͱ-῿　-鿿가-힯＀-￯]")  # grec, cyrillique, CJK…
RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
STOP = {"anglais": "the and of to is you your player card cards each with".split(),
        "allemand": "der die das und ist den mit karten spieler eine".split(),
        "espagnol": "el la los las de que y cartas jugador una".split(),
        "italien": "il la le di che e carte giocatore una gli".split(),
        "français": "le la les des et est carte cartes joueur une".split()}


def clean_name(name):
    n = re.sub(r'[\\/:*?"<>|,!]', " ", name)
    n = re.sub(r"\s+", " ", n).strip().rstrip(". ")
    return n + " (jeu)" if n.upper() in RESERVED else n


def guess_lang(text):
    if len(re.findall(r"[぀-ヿ]", text)) > 20:
        return "japonais"
    if len(re.findall(r"[一-鿿]", text)) > 50:
        return "chinois"
    if len(re.findall(r"[가-힯]", text)) > 20:
        return "coréen"
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", text.lower())
    score = {k: sum(words.count(w) for w in v) for k, v in STOP.items()}
    best = max(score, key=score.get)
    return best if score[best] else "inconnue"


def mostly_japanese(zones):
    """Lu en japonais, un livret anglais donne aussi quelques kana parasites : il faut qu'ils dominent."""
    text = "".join(re.findall(r'^Z\(\d+, \([^)]*\), "(.*)"\)', zones, flags=re.M))
    kana = len(re.findall(r"[぀-ヿ]", text))
    return kana > 20 and kana > len(re.findall(r"[A-Za-z]", text))


def run(args, cwd):
    r = subprocess.run([sys.executable, "-X", "utf8"] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf8")
    return (r.stdout + r.stderr).strip()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    pdf = os.path.abspath(sys.argv[1])
    if not os.path.isfile(pdf):
        sys.exit(f"ERREUR : livret introuvable : {pdf}")
    jeu = clean_name(sys.argv[2])
    lang_ocr = sys.argv[sys.argv.index("--langue-ocr") + 1] if "--langue-ocr" in sys.argv else None
    folder = os.path.dirname(pdf)
    parent = os.path.dirname(folder)
    if os.path.basename(folder).lower() in ("a traduire", "à traduire"):
        ludo = parent
    elif os.path.isdir(os.path.join(parent, "_outils")):  # livret déjà rangé dans <Ludothèque>/<Jeu>/
        ludo = parent
    else:
        ludo = folder
    tools = os.path.join(ludo, "_outils", jeu)
    if os.path.isfile(os.path.join(tools, "spec.py")):
        sys.exit(f"ERREUR : {tools} contient déjà un spec.py (jeu déjà commencé ?) — rien n'a été modifié")
    stem = os.path.splitext(os.path.basename(pdf))[0]
    if "--nom-fichier" in sys.argv:  # nom en lettres latines pour un livret nommé en japonais, chinois…
        new = clean_name(sys.argv[sys.argv.index("--nom-fichier") + 1]).removesuffix(".pdf")
        dest = os.path.join(folder, new + ".pdf")
        if os.path.exists(dest):
            sys.exit(f"ERREUR : {dest} existe déjà — rien n'a été modifié")
        os.rename(pdf, dest)
        print(f"Livret renommé : {stem}.pdf → {new}.pdf")
        pdf = dest
    elif NON_LATIN.search(stem):
        sys.exit(f"ERREUR : nom de fichier en écriture non latine ({stem}.pdf) — relancer avec "
                 f'--nom-fichier "<nom en lettres latines>" — rien n\'a été modifié')
    os.makedirs(os.path.join(tools, "ff"), exist_ok=True)

    doc = pymupdf.open(pdf)
    # texte visible seulement : une couche OCR invisible (mode de rendu 3, police « HiddenHorzOCR »…) sur une
    # page-image ne se remplace pas, c'est un scan
    text = "".join(chr(ch[0]) for p in doc for c in p.get_texttrace() if c["type"] != 3 for ch in c["chars"])
    covered = sum(1 for p in doc for i in p.get_image_info()
                  if (i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]) > 0.8 * p.rect.width * p.rect.height)
    # lettres en tracés vectoriels (texte vectorisé) : pas de texte, des centaines de petits tracés par page
    small = sum(1 for p in doc for d in p.get_drawings() if d["rect"].width <= 12 and d["rect"].height <= 12)
    vecteur = len(text.strip()) < 30 * len(doc) and covered < len(doc) and small > 300 * len(doc)
    scan = len(text.strip()) < 30 * len(doc) and (covered >= len(doc) or vecteur)
    rel = os.path.relpath(pdf, tools).replace("\\", "/").split("/")
    src_line = "SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), " + \
               ", ".join(json.dumps(x, ensure_ascii=False) for x in rel) + ")"  # pas repr : apostrophe (Buccaneers' Code)

    for f in (SCAN_SCRIPTS if scan else TEXT_SCRIPTS):
        shutil.copy(os.path.join(HERE, f), tools)
    if scan and os.path.isfile(SYMBOLS):
        shutil.copy(SYMBOLS, os.path.join(tools, "ff"))
    model = open(os.path.join(HERE, "spec_scan_modele.py" if scan else "spec_modele.py"), encoding="utf8").read()
    imp = "" if re.search(r"^import os$", model, re.M) else "import os\n"
    model = re.sub(r'^SRC = r"CHEMIN/VERS/[^"]*"  # A ADAPTER$', lambda m: imp + src_line, model,
                   flags=re.M)
    model = model.replace("de <JEU>", "de " + jeu)
    if vecteur:
        model = model.replace('MODE = "recouvrir"  # ou "cote"',
                              'MODE = "recouvrir"  # ou "cote"\nVECTEUR = True  # lettres en tracés vectoriels', 1)
    open(os.path.join(tools, "spec.py"), "w", encoding="utf8").write(model)

    print(f"Jeu : {jeu}\nOutils : {tools}\nLivret : {len(doc)} page(s), {doc[0].rect.width:.0f} × "
          f"{doc[0].rect.height:.0f} pt — " + ("texte en tracés vectoriels, traité comme un scan (VECTEUR = True)"
                                               if vecteur else "SCANNÉ (pages-images)" if scan else "texte"))
    print(run([os.path.join(HERE, "sheet.py"), pdf, "planche", "80"], tools) or "planche*.png : aperçu créé")

    fonts_found = []
    if scan:
        print("\n--- lecture automatique (OCR) ---")
        zf = os.path.join(tools, "zones.py")
        if lang_ocr:
            print(run(["ocr.py", pdf, lang_ocr, "zones.py"], tools))
        else:  # langue inconnue : japonais si Windows sait le lire et qu'il en sort du japonais, sinon anglais
            out = run(["ocr.py", pdf, "ja", "zones.py"], tools) if "'ja" in run(["ocr.py", "--langues"], tools) else ""
            if not (os.path.isfile(zf) and mostly_japanese(open(zf, encoding="utf8").read())):
                out = run(["ocr.py", pdf, "en-US", "zones.py"], tools)
            print(out)
        if os.path.isfile(zf):
            print(f"Langue devinée : {guess_lang(open(zf, encoding='utf8').read())}")
    else:
        print(f"Langue devinée : {guess_lang(text)}")
        print(run(["dump.py", pdf, "blocks.txt"], tools))
        print("\n--- polices du livret ---")
        print(run(["polices.py", "extraire", pdf, "fonts"], tools))
        fdir = os.path.join(tools, "fonts")
        files = [os.path.join("fonts", f) for f in sorted(os.listdir(fdir))
                 if not f.endswith(".txt")] if os.path.isdir(fdir) else []
        if files:
            out = run(["polices.py", "glyphes"] + files, tools)
            # regroupé par liste de caractères manquants : souvent la même pour toutes les polices (sous-ensembles)
            groupes, nom = {}, None
            for l in out.splitlines():
                if l.startswith("=="):
                    nom = l.strip("= ").strip()
                elif "français manquants" in l and nom:
                    groupes.setdefault(l.split(":", 1)[1].strip(), []).append(nom)
            for manque, noms in groupes.items():
                print(f"français manquants : {manque} — {', '.join(noms)}")
        fonts_found = [os.path.splitext(os.path.basename(f))[0] for f in files]

    # jeux déjà traduits qui utilisent les mêmes polices
    notes = []
    base = os.path.join(ludo, "_outils")
    for d in sorted(os.listdir(base)):
        nf = os.path.join(base, d, "NOTES.md")
        if d != jeu and os.path.isfile(nf):
            t = open(nf, encoding="utf8").read().lower()
            hits = [f for f in fonts_found if re.sub(r"[-_ ]?(regular|bold|medium|light|std|pro).*$", "",
                                                     f.lower().replace(" ", "")) in t.replace(" ", "")]
            if hits:
                notes.append(f"  {d} : {', '.join(hits)}")
    if notes:
        print("\nJeux déjà traduits avec les mêmes polices (lire leur NOTES.md, recopier leurs polices ff/) :")
        print("\n".join(notes))
    print("\nÀ faire : regarder planche*.png, " + ("compléter zones.py → spec.py (traduire chaque Z)"
                                                   if scan else "lire blocks.txt, choisir les polices, écrire spec.py")
          + ", puis build/scan, relire, et livrer avec livrer.py.")


if __name__ == "__main__":
    main()
