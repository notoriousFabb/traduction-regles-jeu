# -*- coding: utf-8 -*-
"""Livret CMYK recomposé à neuf (fond noir, texte blanc, 12 volets comme le dépliant d'origine, aucune image
du scan) d'après textes.py.
Usage : python -X utf8 noir.py fr|en sortie.pdf [--clair]
--clair : version économe en encre à imprimer (fond blanc, texte foncé) — à construire en plus du livret
normal, dans un autre fichier, et seulement si l'utilisateur le demande.
Une seule taille de texte (≤ BASE), la plus grande qui tient dans tous les volets ; le journal la donne.

EXEMPLE de la skill (references/recomposer.md) : à copier dans _outils/<Jeu>/ avec textes.py, puis adapter le
format (W, H), la grille des volets (COLS, ROWS), les couleurs (BG, FG), les polices (CSS, fichiers dans ff/ :
segoeui*.ttf, seguisym.ttf, bahnschrift.ttf de C:/Windows/Fonts ici) et les blocs spéciaux (« logo », « fin »)."""
import os, re, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
import textes

CLAIR = "--clair" in sys.argv  # version économe en encre : fond blanc, texte foncé
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
LANG, OUT = ARGS[0], ARGS[1]
W, H = 456, 1000                      # format du dépliant scanné (points)
COLS = [(0, 228), (228, 456)]
ROWS = [(0, 333), (333, 667), (667, 1000)]
M = 11                                # marge intérieure d'un volet
BASE = 9.6                            # taille de départ du texte courant
BG, FG, GREY = (0.05, 0.05, 0.05), (0.95, 0.95, 0.95), (0.3, 0.3, 0.3)
if CLAIR:  # fond blanc : couleurs permutées ; le gris est assombri plutôt qu'inversé, pour rester lisible
    BG, FG, GREY = (1, 1, 1), (0.05, 0.05, 0.05), (0.45, 0.45, 0.45)
HEX = "#%02x%02x%02x" % tuple(round(c * 255) for c in FG)  # couleur du texte, pour le CSS de box()
ARCH = pymupdf.Archive("ff")
CSS = """
@font-face{font-family:Sg;src:url(segoeui.ttf);}
@font-face{font-family:Sg;font-weight:bold;src:url(segoeuib.ttf);}
@font-face{font-family:Sg;font-style:italic;src:url(segoeuii.ttf);}
@font-face{font-family:Sg;font-weight:bold;font-style:italic;src:url(segoeuiz.ttf);}
@font-face{font-family:Sym;src:url(seguisym.ttf);}
@font-face{font-family:Bahn;src:url(bahnschrift.ttf);}
* {margin:0; padding:0;}
"""
BOLD = pymupdf.Font(fontfile="ff/segoeuib.ttf")
log = []


def tr(v):
    s = v[LANG] if isinstance(v, dict) else v
    if LANG == "fr":  # espaces insécables de la typographie française
        s = re.sub(r" ([:;!?»])", " \\1", s).replace("« ", "« ")
        s = re.sub(r"(?<=[A-Za-zÀ-ÿ])'", "’", s)
    return s


def box(page, rect, html, size, bold=False, align="left", lead=1.28, fam="Sg", ital=False):
    """Pose html dans rect (haut fixé) ; rend la hauteur utilisée, ou None si ça ne tient pas."""
    st = (f"font-family:{fam};font-size:{size}pt;line-height:{lead};color:{HEX};text-align:{align};"
          f"font-weight:{'bold' if bold else 'normal'};font-style:{'italic' if ital else 'normal'};")
    spare, _ = page.insert_htmlbox(rect, f'<div style="{st}">{html}</div>', css=CSS, archive=ARCH, scale_low=1)
    return None if spare < 0 else rect.height - spare


def line(page, a, b, w=0.6, color=FG):
    page.draw_line(a, b, color=color, width=w)


def label(page, x, y, text, size):
    """Titre posé sur un filet : aplat noir derrière, puis texte."""
    w = BOLD.text_length(text, size)
    page.draw_rect(pymupdf.Rect(x - 2, y - size * 0.7, x + w + 3, y + size * 0.7), color=None, fill=BG)
    box(page, pymupdf.Rect(x, y - size * 0.75, x + w + 20, y + size * 0.9), text, size, bold=True, lead=1.0)
    return w


def panel(page, n, s):
    """Pose le volet n à la taille s ; rend False si le texte dépasse."""
    i = (n - 1) % 6
    x0, x1 = COLS[i % 2]
    y0, y1 = ROWS[i // 2]
    x0, x1, top, bottom = x0 + M, x1 - M, y0 + M + 2, y1 - 24
    y = top
    for b in textes.VOLETS[n]:
        kind = b[0]
        first = y == top
        if kind == "logo":
            box(page, pymupdf.Rect(x0, y + 2, x1, y + 56), "CMYK", 42, fam="Bahn", align="center", lead=1.0)
            box(page, pymupdf.Rect(x0, y + 54, x1, y + 70), tr(textes.SOUS_TITRE), 10.5, bold=True, align="center")
            cw, ch, cx = 46, 20, (x0 + x1) / 2 - 69
            for k, info in enumerate(textes.INFO):
                r = pymupdf.Rect(cx + k * cw, y + 74, cx + (k + 1) * cw, y + 74 + ch)
                page.draw_rect(r, color=FG, width=0.6)
                box(page, r + (1, 5.5, -1, 0), tr(info), 7, bold=True, align="center", lead=1.0)
            y += 100
        elif kind == "fin":
            yy = y0 + 105
            box(page, pymupdf.Rect(x0, yy, x1, yy + 30), "Anyway have fun!", 17, bold=True, ital=True,
                align="center", lead=1.0)
            yy += 42
            yy += box(page, pymupdf.Rect(x0, yy, x1, yy + 60), tr(textes.CREDITS), 7, align="center", lead=1.3)
            yy += 12
            box(page, pymupdf.Rect(x0, yy, x1, yy + 20), "Nakagawa Hands", 11.5, bold=True, align="center",
                lead=1.0)
            box(page, pymupdf.Rect(x0, yy + 17, x1, yy + 50), tr(textes.ADRESSE), 6.5, align="center", lead=1.3)
        elif kind == "h":
            if not first:
                y += s * 0.9
            sz = s * 1.3
            h = box(page, pymupdf.Rect(x0, y, x1, bottom),
                    '<span style="font-family:Sym;font-weight:normal">⌖</span> ' + tr(b[1]), sz, bold=True,
                    lead=1.15)
            if h is None:
                return False
            y += h + s * 0.35
        elif kind == "rule":
            y += s * 0.6
            sz = s * 1.1
            line(page, (x0, y + sz * 0.6), (x0 + 6, y + sz * 0.6))
            w = BOLD.text_length(tr(b[1]), sz)
            box(page, pymupdf.Rect(x0 + 9, y, x1, y + sz * 2), tr(b[1]), sz, bold=True, lead=1.0)
            line(page, (x0 + 13 + w, y + sz * 0.6), (x1, y + sz * 0.6))
            y += sz * 1.35
        elif kind == "sub":
            if not first:
                y += s * 0.55
            h = box(page, pymupdf.Rect(x0, y, x1, bottom), tr(b[1]), s * 1.08, bold=True, lead=1.2)
            if h is None:
                return False
            y += h + s * 0.2
        elif kind == "p":
            h = box(page, pymupdf.Rect(x0, y, x1, bottom), tr(b[1]), s)
            if h is None:
                return False
            y += h + s * 0.4
        elif kind == "li":
            box(page, pymupdf.Rect(x0 + 2, y, x0 + 12, y + s * 2), "◦", s, lead=1.28)
            h = box(page, pymupdf.Rect(x0 + 11, y, x1, bottom), tr(b[1]), s)
            if h is None:
                return False
            y += h + s * 0.25
        elif kind == "sp":
            y += s * b[1]
        elif kind == "box":
            y += s * (0.3 if first else 0.7)
            pad, sz = 6, s * 0.95
            h = box(page, pymupdf.Rect(x0 + pad, y + pad + 3, x1 - pad, bottom), tr(b[2]), sz)
            if h is None:
                return False
            r = pymupdf.Rect(x0, y, x1, y + h + 2 * pad + 3)
            page.draw_rect(r, color=FG, width=0.6)
            label(page, x0 + 9, y, tr(b[1]), s * 1.0)
            y = r.y1 + s * 0.45
        if y > bottom:
            return False
    # numéro du volet, dans un petit carré en bas à droite
    r = pymupdf.Rect(x1 - 11, y1 - 22, x1, y1 - 11)
    page.draw_rect(r, color=FG, width=0.6)
    box(page, r + (0, 1.6, 0, 2), str(n), 6.5, align="center", lead=1.0)
    return True


def fond(page):
    page.draw_rect(page.rect, color=None, fill=BG)
    line(page, (228, 0), (228, H), 0.4, GREY)          # plis du dépliant
    for y in (333, 667):
        line(page, (0, y), (W, y), 0.4, GREY)


def fits(n, s):
    essai = pymupdf.open()
    return panel(essai.new_page(width=W, height=H), n, s)


# une seule taille de texte pour tout le livret : la plus grande qui tient dans chaque volet
s = BASE
while not all(fits(n, s) for n in textes.VOLETS):
    s = round(s - 0.1, 2)
    if s < 6.5:
        sys.exit(f"ERREUR : le texte ({LANG}) ne tient pas même à 6,5 pt")
log.append(f"texte courant à {s:.1f} pt")
doc = pymupdf.open()
for p in range(2):
    page = doc.new_page(width=W, height=H)
    fond(page)
    for n in range(p * 6 + 1, p * 6 + 7):
        panel(page, n, s)
doc.set_metadata({"title": "CMYK — " + ("Règles du jeu" if LANG == "fr" else "Rules"),
                  "author": "Kohta Nakagawa (Nakagawa Hands)"})
doc.subset_fonts()
doc.save(OUT, garbage=4, deflate=True)
print("\n".join(log))
print(f"{OUT} : {len(doc)} pages")
