# Guardian UI Sans Medium

The shared screen UI uses a derived, subsetted TrueType font instead of enlarging the objective HUD's 20px bitmaps. Its cubic outlines come from the supplied, preserved Noto Sans KR Medium OTF. `manifest.json` records the original and derived hashes. The derivative is renamed **Guardian UI Sans** and remains under SIL OFL 1.1; the runtime font folder includes the original license and notices.

Rebuild using FontTools 4.62.1:

```sh
rtk proxy uv run --with fonttools==4.62.1 python scripts/art/build_ui_font.py
rtk proxy uv run --with fonttools==4.62.1 python scripts/art/build_ui_font.py --verify
```

The generator reads the original OTF and the existing medium glyph metrics without modifying either. It keeps all 11,364 existing codepoints, converts cubic curves to quadratic curves with maximum error 0.5 font units (0.01 logical pixel at 20px), and gives the new font the same advances as the old bitmaps. A minimal TrueType program disables grid fitting and prevents FreeType's auto-hinter from shifting 14 Latin/punctuation advances by half a pixel at 2x sampling. `UiOutlineFontTest` loads the actual Minecraft 26.3/FreeType provider and compares every glyph's advance with those server-side metrics.

The provider uses size 20 and oversample 2, retaining logical glyph size while rasterizing outlines at twice the resolution. `HudPainter` retains its existing scale, positions, wrapping and clipping metrics. The original bitmap font remains available to the objective/tutorial HUD and other existing callers.

`UiFontPack` composes a small shader change with the final ShaderFX text shaders. Grayscale screen-fixed HUD glyphs receive bilinear coverage sampling and retain low-opacity edge coverage; world text, normal GUI text, colored bitmap glyphs, RGBMap decoding, ShaderFX effects and animated glyphs keep their existing paths. No client mod or global sampler change is needed. New outline glyphs are baked through the normal client font cache.
