"""Build the Me. wordmark as SVG, from the brand package specification.

Spec (docs/brand/me-brand-package/assets/README.md + design-system/wordmark.md):
  Letters "Me", Inter, weight 600, letter-spacing -0.045em.
  Letters #151716 on light / #F0F0F0 on dark. Full stop ALWAYS #00C896.
  Kerning locked at the Inter default for the pair. No effects.

Text is converted to outlines so the file renders identically without Inter
installed, which is the point of shipping an SVG to a newsroom.
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
import uharfbuzz as hb

SRC = "/Users/oi17mbpmatt/Me/XCode/Me/docs/brand/me-brand-package/Inter/Inter-VariableFont_opsz,wght.ttf"
OUT = "/private/tmp/claude-501/-Users-oi17mbpmatt/2a8b1520-a10e-4d28-ada7-c1225114508e/scratchpad"
TEXT = "Me."
TRACK_EM = -0.045          # letter-spacing, applied between glyphs
GREEN = "#00C896"

# Pin weight to 600. opsz is left at its default: the spec names weight and
# tracking only, and inventing an optical size would be adding to the brand.
font = instancer.instantiateVariableFont(TTFont(SRC), {"wght": 600}, inplace=False)
upem = font["head"].unitsPerEm
glyphset = font.getGlyphSet()

with open(SRC, "rb") as fh:
    blob = hb.Blob(fh.read())
face = hb.Face(blob)
hbfont = hb.Font(face)
hbfont.scale = (upem, upem)
try:
    hbfont.set_variations({"wght": 600})
except Exception as e:
    sys.exit(f"could not set variations: {e}")

buf = hb.Buffer()
buf.add_str(TEXT)
buf.guess_segment_properties()
hb.shape(hbfont, buf)

order = font.getGlyphOrder()
track_units = TRACK_EM * upem

pen_paths, x = [], 0.0
for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
    name = order[info.codepoint]
    pen = SVGPathPen(glyphset)
    glyphset[name].draw(pen)
    d = pen.getCommands()
    pen_paths.append((name, d, x + pos.x_offset))
    x += pos.x_advance + track_units      # HarfBuzz advance carries the kerning

# The full stop is the last glyph and is coloured separately, always green.
letters = [p for p in pen_paths[:-1] if p[1]]
stop = pen_paths[-1]

asc, desc = font["hhea"].ascent, font["hhea"].descent
# Tight box around the drawn wordmark rather than the full font box.
xmin = 0
xmax = x - track_units
pad = upem * 0.06
vb_w = xmax + pad * 2
vb_h = (asc - desc)

def build(letter_colour, name):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w:.0f} {vb_h:.0f}" role="img" aria-label="Me.">']
    parts.append('  <title>Me.</title>')
    parts.append(f'  <g transform="translate({pad:.0f}, {asc:.0f}) scale(1, -1)">')
    for gname, d, gx in letters:
        parts.append(f'    <path fill="{letter_colour}" transform="translate({gx:.0f}, 0)" d="{d}"/>')
    parts.append(f'    <path fill="{GREEN}" transform="translate({stop[2]:.0f}, 0)" d="{stop[1]}"/>')
    parts.append('  </g>')
    parts.append('</svg>')
    open(f"{OUT}/{name}", "w").write("\n".join(parts) + "\n")
    print(f"wrote {name}  viewBox 0 0 {vb_w:.0f} {vb_h:.0f}")

build("#151716", "wordmark-light.svg")
build("#F0F0F0", "wordmark-dark.svg")
print("glyphs:", [p[0] for p in pen_paths], "| upem", upem, "| tracking units", round(track_units,1))
