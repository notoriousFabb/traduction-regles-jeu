# -*- coding: utf-8 -*-
"""Aide-mémoire d'une page A4 à poser sur la table : mise en place, tour de jeu, fin de partie et score…

    python -X utf8 aide_memoire.py "<Ludothèque>/_outils/<Jeu>/aide-memoire.json" "<sortie.pdf>"
        [--livret "<livret.pdf>"]   vignette de la couverture (page 1) en tête de page
        [--apercu "<image.png>"]    image de la page construite, pour la regarder

aide-memoire.json (rédigé par Claude d'après le livret, voir references/aide-memoire.md) :
    {
      "titre": "CMYK",
      "infos": "Jeu de plis · 1 à 5 joueurs · 20-30 min",          facultatif
      "but": "Remporter les plis de la couleur de son objectif.",   une phrase
      "sections": [
        {"titre": "Mise en place", "etapes": ["…", "…"]},           liste numérotée
        {"titre": "Tour de jeu", "etapes": ["…"]},
        {"titre": "Fin de manche et score", "points": ["…"]},       liste à puces
        {"titre": "Cartes spéciales", "tableau": [["Joker", "…"]]}, une ligne « nom : effet » par carte
        {"titre": "À ne pas oublier", "points": ["…"], "accent": true}   encadré
      ],
      "source": "Livret CMYK_Rules_FR.pdf, p. 2-5"
    }
Dans les textes, **gras** met en gras. Les sections se suivent dans l'ordre, sur deux colonnes ; le texte est
réduit pas à pas jusqu'à tenir sur une page (« TROP LONG » en dessous de 7 pt : raccourcir le JSON).
"""
import html, io, json, os, re, sys

import pymupdf

A4 = pymupdf.paper_rect("a4")
MARGE, ENTRE_COLONNES, HAUT_TETE = 34, 22, 92
TAILLE_MIN = 7.0
POLICES = {  # polices de Windows ; à défaut, celles intégrées à pymupdf
    "corps": ("segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf"),
    "titre": ("georgia.ttf", "georgiab.ttf", None),
}
ENCRE, GRIS, FILET, FOND = "#1d1d1f", "#5b5b63", "#c9c9cf", "#f1f1f3"


def _polices():
    dossier = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    css, archive = [], pymupdf.Archive()
    ok = all(os.path.isfile(os.path.join(dossier, f)) for fams in POLICES.values() for f in fams if f)
    if not ok:
        return "", None, "sans-serif", "serif"
    archive.add(pymupdf.Archive(dossier))
    for nom, (normal, gras, ital) in POLICES.items():
        css.append(f"@font-face {{ font-family: am-{nom}; src: url({normal}); }}")
        css.append(f"@font-face {{ font-family: am-{nom}; font-weight: bold; src: url({gras}); }}")
        if ital:
            css.append(f"@font-face {{ font-family: am-{nom}; font-style: italic; src: url({ital}); }}")
    return "\n".join(css), archive, "am-corps", "am-titre"


def _texte(t):
    """Échappe le texte, **gras** → <b>, typographie française (espace insécable avant ; : ! ? et dans « »)."""
    t = re.sub(r"\s*([;:!?])(?=\s|$|\*)", "\u00a0\\1", str(t).strip())  # avant l'échappement (« &gt; » finit par ;)
    t = re.sub(r"\s*»", "\u00a0»", re.sub(r"«\s*", "«\u00a0", t))
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t, quote=False))


def _section(s):
    h = f'<h2>{_texte(s["titre"])}</h2>'
    if s.get("etapes"):
        h += "<ol>" + "".join(f"<li>{_texte(x)}</li>" for x in s["etapes"]) + "</ol>"
    if s.get("points"):
        h += "<ul>" + "".join(f"<li>{_texte(x)}</li>" for x in s["points"]) + "</ul>"
    if s.get("tableau"):  # une ligne « Nom : effet » par entrée (les <table> de MuPDF font chevaucher les colonnes)
        h += "".join(f'<p class="def"><b>{_texte(a)}</b> : {_texte(b)}</p>' for a, b in s["tableau"])
    if s.get("texte"):
        h += f"<p>{_texte(s['texte'])}</p>"
    return f'<div class="sec{" accent" if s.get("accent") else ""}">{h}</div>'


def _css(polices, corps, titre, taille):
    return polices + f"""
    * {{ margin: 0; padding: 0; }}
    body {{ font-family: {corps}; font-size: {taille}pt; line-height: 1.3; color: {ENCRE}; }}
    .sec {{ margin-bottom: {taille * 0.9}pt; }}
    .accent {{ background-color: {FOND}; padding: {taille * 0.6}pt {taille * 0.8}pt; }}
    h2 {{ font-family: {titre}; font-size: {taille * 1.3}pt; font-weight: bold; margin-bottom: {taille * 0.35}pt;
          padding-bottom: {taille * 0.15}pt; border-bottom: 0.6pt solid {FILET}; }}
    ol, ul {{ margin-left: {taille * 0.4}pt; }}
    li {{ margin-bottom: {taille * 0.25}pt; }}
    p {{ margin-bottom: {taille * 0.3}pt; }}
    p.def {{ padding-bottom: {taille * 0.25}pt; border-bottom: 0.4pt solid {FILET}; }}
    b {{ font-weight: bold; }}
    """


def _colonnes():
    largeur = (A4.width - 2 * MARGE - ENTRE_COLONNES) / 2
    haut, bas = MARGE + HAUT_TETE, A4.height - MARGE - 16
    return [pymupdf.Rect(MARGE, haut, MARGE + largeur, bas),
            pymupdf.Rect(MARGE + largeur + ENTRE_COLONNES, haut, A4.width - MARGE, bas)]


def _poser(sections, taille, css, archive, dev):
    """Pose les sections l'une sous l'autre sur deux colonnes, chacune d'un seul bloc : une section qui ne tient
    pas dans le reste d'une colonne passe en haut de la suivante (coupée seulement si elle dépasse une colonne
    entière). Rend False si tout ne tient pas sur la page."""
    cols, gap = _colonnes(), taille * 0.3  # en plus de la marge basse de .sec, comprise dans la zone remplie
    c, y = 0, cols[0].y0
    for html_sec in sections:
        story = pymupdf.Story(html=html_sec, user_css=css, archive=archive)
        while True:
            if c >= len(cols):
                return False
            col = cols[c]
            reste, rempli = story.place(pymupdf.Rect(col.x0, y, col.x1, col.y1))
            if reste and y > col.y0:  # pas la place ici : la section repart en haut de la colonne suivante
                c, y = c + 1, cols[min(c + 1, len(cols) - 1)].y0
                story = pymupdf.Story(html=html_sec, user_css=css, archive=archive)
                continue
            story.draw(dev)
            if not reste:
                y = rempli[3] + gap  # bas de la zone remplie
                break
            c, y = c + 1, cols[min(c + 1, len(cols) - 1)].y0  # plus haute qu'une colonne : la suite en face
    return True


def _taille(d, polices, archive, corps, titre):
    """Plus grande taille de texte (pas de 0,25 pt) à laquelle les sections tiennent sur la page."""
    sections = [_section(s) for s in d["sections"]]
    taille = 11.0
    while taille >= TAILLE_MIN:
        w = pymupdf.DocumentWriter(io.BytesIO())  # essai dessiné à part, jeté ensuite
        ok = _poser(sections, taille, _css(polices, corps, titre, taille), archive, w.begin_page(A4))
        w.end_page()
        w.close()
        if ok:
            return sections, taille
        taille = round(taille - 0.25, 2)
    raise SystemExit(f"TROP LONG : même en {TAILLE_MIN} pt le contenu ne tient pas sur une page — raccourcir le JSON")


def _tete_html(d, polices, corps, titre):
    tete = (f'<p class="eti">Aide-mémoire</p><h1>{_texte(d["titre"])}</h1>'
            + (f'<p class="infos">{_texte(d["infos"])}</p>' if d.get("infos") else "")
            + (f'<p class="but"><b>But du jeu.</b> {_texte(d["but"])}</p>' if d.get("but") else ""))
    css = polices + f"""
      * {{ margin: 0; padding: 0; }}
      body {{ font-family: {corps}; color: {ENCRE}; }}
      .eti {{ font-size: 7.5pt; font-weight: bold; color: {GRIS}; letter-spacing: 1pt; text-transform: uppercase; }}
      h1 {{ font-family: {titre}; font-size: 24pt; line-height: 1.1; margin: 1pt 0 2pt; }}
      .infos {{ font-size: 9pt; color: {GRIS}; margin-bottom: 4pt; }}
      .but {{ font-size: 10pt; line-height: 1.3; }}"""
    return tete, css


def _vignette(livret):
    """Taille de la vignette de couverture (largeur, hauteur) pour la hauteur de l'en-tête."""
    with pymupdf.open(livret) as src:
        r = src[0].rect
    h = HAUT_TETE - 14
    return h * r.width / r.height, h


def construire(json_path, sortie, livret=None, apercu=None):
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    polices, archive, corps, titre = _polices()
    sections, taille = _taille(d, polices, archive, corps, titre)
    livret = livret if livret and os.path.isfile(livret) else None
    vw, vh = _vignette(livret) if livret else (0, 0)
    x_tete = MARGE + (vw + 14 if livret else 0)

    # texte : en-tête puis sections sur deux colonnes, dessinés dans une seule page
    tampon = io.BytesIO()
    w = pymupdf.DocumentWriter(tampon)
    dev = w.begin_page(A4)
    tete, css_tete = _tete_html(d, polices, corps, titre)
    st = pymupdf.Story(html=tete, user_css=css_tete, archive=archive)
    st.place(pymupdf.Rect(x_tete, MARGE, A4.width - MARGE, MARGE + HAUT_TETE - 8))
    st.draw(dev)
    _poser(sections, taille, _css(polices, corps, titre, taille), archive, dev)
    w.end_page()
    w.close()

    # dessins : vignette, filet sous l'en-tête, pied de page
    doc = pymupdf.open("pdf", tampon.getvalue())
    page = doc[0]
    if livret:
        r = pymupdf.Rect(MARGE, MARGE, MARGE + vw, MARGE + vh)
        with pymupdf.open(livret) as src:
            page.show_pdf_page(r, src, 0)
        page.draw_rect(r, color=(0.8, 0.8, 0.82), width=0.5)
    y = MARGE + HAUT_TETE - 4
    page.draw_line((MARGE, y), (A4.width - MARGE, y), color=(0.25, 0.25, 0.28), width=1.2)
    pied = " · ".join(x for x in (d.get("source") and f"D'après le livret : {d['source']}",
                                  "aide-mémoire : les règles complètes font foi") if x)
    page.insert_text((MARGE, A4.height - MARGE + 6), pied, fontsize=6.5, color=(0.45, 0.45, 0.5))
    doc.set_metadata({"title": f"{d['titre']} — aide-mémoire", "creator": "regles-jeu"})
    os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True)
    doc.save(sortie, garbage=3, deflate=True)
    if apercu:
        page.get_pixmap(dpi=80).save(apercu)
    doc.close()
    print(f"OK : {sortie} (texte en {taille} pt{' — petit : envisager de raccourcir' if taille < 8.5 else ''})")


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda n: a[a.index(n) + 1] if n in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    if len(pos) != 2:
        raise SystemExit(__doc__)
    construire(pos[0], pos[1], opt("--livret"), opt("--apercu"))
