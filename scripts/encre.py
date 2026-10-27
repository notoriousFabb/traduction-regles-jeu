# -*- coding: utf-8 -*-
"""Version économe en encre d'un livret sombre : le fond part, les couleurs claires deviennent foncées.

Utilisé par build.py avec --fond-clair, page sombre par page sombre ; à copier avec lui dans _outils/<Jeu>/.
Principe : l'image ou l'aplat qui couvre la page n'est plus peint (le papier blanc reste), et toute autre
couleur voit sa clarté inversée à teinte constante — texte blanc -> texte noir, filet clair -> filet foncé,
pastille sombre -> pastille claire. Les images gardent leurs couleurs : illustrations, logos et pictogrammes
sont imprimés tels quels, seul le fond est retiré."""
import colorsys, re
import pymupdf

SEUIL = 0.45   # clarté médiane au-dessous de laquelle une page (ou un aplat) est jugée sombre
PART = 0.5     # part de la page à couvrir pour être le fond et non une illustration
PROCHE = 0.06  # écart au-dessous duquel deux couleurs sont la même (fond repéré par sa couleur)
CONTRASTE = 3.0  # contraste minimal du texte sur papier blanc (seuil des grands caractères)
IMGDO = re.compile(rb"(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) cm\s*(/[\w.]+ Do)")
PDFTOK = re.compile(rb"\((?:\.|[^\)])*\)|<<|>>|<[^>]*>|\[|\]|/[^\s/\[\]()<>]+|[^\s/\[\]()<>]+")
OPS = {b"g": 1, b"G": 1, b"rg": 3, b"RG": 3, b"k": 4, b"K": 4}
OPS_CS = (b"sc", b"scn", b"SC", b"SCN")  # couleur dans l'espace courant : seulement 3 (RVB) ou 4 (CMJN) valeurs


def _rgb(vals):
    """Opérandes d'un opérateur de couleur ramenées en RVB (1 = gris, 3 = RVB, 4 = CMJN)."""
    if len(vals) == 1:
        return (vals[0],) * 3
    if len(vals) == 3:
        return tuple(vals)
    c, m, j, n = vals
    return ((1 - c) * (1 - n), (1 - m) * (1 - n), (1 - j) * (1 - n))


def _vals(rgb, n):
    """Retour du RVB vers les opérandes de l'opérateur d'origine (même opérateur, même nombre de valeurs)."""
    if n == 1:
        return [sum(rgb) / 3]
    if n == 3:
        return list(rgb)
    k = 1 - max(rgb)
    if k >= 1:
        return [0.0, 0.0, 0.0, 1.0]
    return [(1 - rgb[0] - k) / (1 - k), (1 - rgb[1] - k) / (1 - k), (1 - rgb[2] - k) / (1 - k), k]


def clarte(rgb):
    return colorsys.rgb_to_hls(*rgb)[1]


def inverse(rgb, fonds=()):
    """Même teinte, clarté inversée ; une couleur de fond devient du blanc franc (aucune encre)."""
    if any(max(abs(a - b) for a, b in zip(rgb, f)) < PROCHE for f in fonds):
        return (1.0, 1.0, 1.0)
    h, l, s = colorsys.rgb_to_hls(*rgb)
    return colorsys.hls_to_rgb(h, 1.0 - l, s)


def _lum(rgb):
    """Luminance relative (WCAG), pour juger du contraste sur papier blanc."""
    r, g, b = ((c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def texte(rgb):
    """Couleur d'un texte sur papier blanc : clarté inversée, puis assombrie tant que le contraste avec le
    blanc reste insuffisant — un titre jaune clair deviendrait un jaune pâle illisible une fois le fond blanc."""
    h, l, s = colorsys.rgb_to_hls(*inverse(rgb))
    while l > 0.02 and 1.05 / (_lum(colorsys.hls_to_rgb(h, l, s)) + 0.05) < CONTRASTE:
        l -= 0.02
    return colorsys.hls_to_rgb(h, l, s)


def sombre(page):
    """Page à fond sombre : la clarté médiane de ses pixels est basse (vue à 10 dpi, le fond l'emporte)."""
    vals = sorted(page.get_pixmap(dpi=10, colorspace=pymupdf.csGRAY).samples)
    return bool(vals) and vals[len(vals) // 2] < 255 * SEUIL


def fonds(page):
    """Couleurs des grands aplats sombres qui couvrent la page : à blanchir plutôt qu'à éclaircir."""
    aire = page.rect.get_area()
    return [tuple(d["fill"]) for d in page.get_drawings()
            if d.get("fill") and d["rect"].get_area() > PART * aire and clarte(d["fill"]) < SEUIL]


def retirer_image_de_fond(doc, page):
    """L'image qui couvre la page n'est plus peinte (son « Do » est retiré), le papier reste blanc.
    Rend (images de fond trouvées, images effectivement retirées)."""
    aire = page.rect.get_area()
    cibles = [pymupdf.Rect(im["bbox"]) for im in page.get_image_info()
              if pymupdf.Rect(im["bbox"]).get_area() > PART * aire]
    if not cibles:
        return 0, 0
    H, n = page.rect.height, 0

    def rimg(m):
        nonlocal n
        a, b, c, d, e, f = (float(v) for v in m.groups()[:6])
        if abs(b) > 1e-3 or abs(c) > 1e-3:
            return m.group(0)
        r = pymupdf.Rect(e, H - (f + d), e + a, H - f)
        if any(abs(r.x0 - t.x0) < 1 and abs(r.y0 - t.y0) < 1
               and abs(r.x1 - t.x1) < 1 and abs(r.y1 - t.y1) < 1 for t in cibles):
            n += 1
            return m.group(0)[:-len(m.group(7))]
        return m.group(0)

    for xref in page.get_contents():
        data = doc.xref_stream(xref)
        new = IMGDO.sub(rimg, data)
        if new != data:
            doc.update_stream(xref, new)
    return len(cibles), n


def inverser_couleurs(doc, page, bg):
    """Clarté inversée pour chaque couleur posée dans le flux de la page (les images ne sont pas concernées).
    Rend (couleurs changées, couleurs d'un espace particulier laissées telles quelles)."""
    chg = skip = 0
    for xref in page.get_contents():
        data = doc.xref_stream(xref)
        out, nums = [], []
        for t in PDFTOK.findall(data):
            n = OPS.get(t)
            if t in OPS_CS:
                n = len(nums) if len(nums) in (3, 4) else 0
                skip += 0 if n else 1
            if n and len(nums) >= n and out[-n:] == nums[-n:]:
                vals = [float(v) for v in nums[-n:]]
                if all(0 <= v <= 1 for v in vals):
                    out[-n:] = [b"%g" % v for v in _vals(inverse(_rgb(vals), bg), n)]
                    chg += 1
            out.append(t)
            try:
                float(t)
                nums.append(t)
            except ValueError:
                if t not in (b"[", b"]"):
                    nums = []
        new = b" ".join(out)
        if new != data:
            doc.update_stream(xref, new)
    return chg, skip


def eclaircir(doc, page, log):
    """Rend la page économe en encre. À appeler une fois le texte d'origine effacé et le crochet AVANT_TEXTE
    passé, avant de dessiner le français (dont build.py choisit lui-même la couleur, avec inverse())."""
    bg = fonds(page)
    trouvees, retirees = retirer_image_de_fond(doc, page)
    chg, skip = inverser_couleurs(doc, page, bg)
    log.append(f"page {page.number} : fond clair — {retirees} image(s) de fond retirée(s), {len(bg)} aplat(s) "
               f"de fond blanchi(s), {chg} couleur(s) inversée(s)"
               + (f" ; {skip} couleur(s) d'un espace particulier laissée(s) telle(s) quelle(s)" if skip else "")
               + (f"  À VÉRIFIER : {trouvees - retirees} image(s) de fond NON retirée(s) (posée(s) autrement "
                  f"qu'avec une matrice droite)" if trouvees > retirees else ""))
