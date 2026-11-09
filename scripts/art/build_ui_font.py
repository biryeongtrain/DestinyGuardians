"""Build a renamed, quadratic-outline UI font with the legacy bitmap advances.

Run with fonttools 4.62.1. Outputs include the runtime font and source manifest.
The original OTF remains read-only; the derived font remains under the OFL.
"""
import argparse
import io
import fontTools
import copy
import hashlib
import json
from pathlib import Path

from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.ttProgram import Program

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/main/resources/assets/destiny/font/ui'
ART = ROOT / 'art/hud/ui-font'
SOURCE = ROOT / 'art/hud/objective-ko/source/fonts/notosanskr-medium.otf'
METRICS = ROOT / 'src/main/resources/assets/destiny/hud/rg_objective_metrics.json'

def main(verify=False):
    original_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert original_hash == 'e7f8d77657c4df73d42c0151b7f53038a6461d94e3061fe642c98790a8dc82fd', 'Original font changed'
    advances = json.loads(METRICS.read_text())['medium']
    original = TTFont(SOURCE, recalcTimestamp=False)
    units = original['head'].unitsPerEm
    options = subset.Options()
    options.recalc_timestamp = False
    options.layout_features = []
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=[ord(c) for c in advances])
    sub.subset(original)
    glyphset = original.getGlyphSet()
    glyphs = {}
    for name in original.getGlyphOrder():
        pen = TTGlyphPen(glyphset)
        glyphset[name].draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=True))
        glyph = pen.glyph()
        # An explicit no-op marks the font as bytecode-managed. Otherwise
        # FreeType may choose its auto-hinter and ignore the prep grid-fit rule.
        glyph.program = Program()
        glyph.program.fromAssembly(['SVTCA[0]'])
        glyphs[name] = glyph
    metrics = dict(original['hmtx'].metrics)
    cmap = original.getBestCmap()
    for cp, name in cmap.items():
        metrics[name] = (round(advances[chr(cp)] * units / 20), metrics[name][1])
    builder = FontBuilder(units, isTTF=True)
    builder.setupGlyphOrder(original.getGlyphOrder())
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    hhea = original['hhea']
    builder.setupHorizontalHeader(ascent=hhea.ascent, descent=hhea.descent, lineGap=hhea.lineGap)
    builder.font['name'] = copy.deepcopy(original['name'])
    names = {1: 'Guardian UI Sans', 2: 'Medium', 3: 'GuardianUISans-Medium-' + original_hash[:12],
             4: 'Guardian UI Sans Medium', 6: 'GuardianUISans-Medium', 16: 'Guardian UI Sans', 17: 'Medium'}
    for record in builder.font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    builder.font['OS/2'] = copy.deepcopy(original['OS/2'])
    builder.setupPost()
    builder.setupMaxp()
    builder.font['maxp'].maxStackElements = 8
    # Keep FreeType's grid fitting from rounding some advances by half a logical
    # pixel at 2x oversampling. Coverage comes from the original outline instead.
    prep = newTable('prep')
    prep.program = Program()
    prep.program.fromAssembly(['PUSHB[ ]', '1', '1', 'INSTCTRL[ ]'])
    builder.font['prep'] = prep
    functions = newTable('fpgm')
    functions.program = Program()
    functions.program.fromAssembly(['PUSHB[ ]', '0', 'FDEF[ ]', 'ENDF[ ]'])
    builder.font['fpgm'] = functions
    builder.font['maxp'].maxFunctionDefs = 1
    builder.font['head'].created = original['head'].created
    builder.font['head'].modified = original['head'].modified
    builder.font.recalcTimestamp = False
    target = OUT / 'guardian_ui_medium.ttf'
    binary = io.BytesIO()
    builder.save(binary)
    font_bytes = binary.getvalue()
    result = TTFont(io.BytesIO(font_bytes), recalcTimestamp=False)
    restored = result.getBestCmap()
    assert set(restored) == set(map(ord, advances)), 'Missing legacy UI glyphs'
    assert all(result['hmtx'].metrics[restored[ord(c)]][0] * 20 / units == advance
               for c, advance in advances.items()), 'Layout advance changed'
    manifest = {'family': 'Guardian UI Sans Medium', 'source': str(SOURCE.relative_to(ROOT)),
        'sourceSha256': original_hash, 'derivedSha256': hashlib.sha256(font_bytes).hexdigest(),
        'license': 'SIL Open Font License 1.1', 'glyphs': len(advances), 'emSize': units,
        'logicalSize': 20, 'oversample': 2, 'gridFitting': 'disabled by TrueType prep INSTCTRL',
        'cubicToQuadraticMaxErrorFontUnits': 0.5,
        'layout': 'Every codepoint advance equals the shipped 20px bitmap advance; outlines retain source coordinates',
        'derivedBytes': len(font_bytes), 'fontToolsVersion': fontTools.__version__}
    outputs = {target: font_bytes, ART / 'manifest.json': (json.dumps(manifest, indent=2) + '\n').encode(),
        OUT / 'OFL.txt': SOURCE.with_name('OFL.txt').read_bytes(),
        OUT / 'NOTICES.txt': SOURCE.with_name('NOTICES.txt').read_bytes()}
    for path, raw in outputs.items():
        if verify:
            assert path.read_bytes() == raw, 'Stale font artifact: ' + str(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    main(parser.parse_args().verify)
