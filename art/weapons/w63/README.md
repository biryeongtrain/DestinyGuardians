# W63 — timed, source-cancellable reload audio

- [Audio manifest](audio-manifest.json): authorized W33 source identity, consumed hashes, actual base/Outlaw rows, filters, Ogg measurements.
- [Audio notes](audio-notes.md): reproducibility and fidelity limits.
- [Generator](../../../scripts/audio/build_reload_sounds_w63.py): `--verify` is offline/read-only; `--check` regenerates twice in private temporary storage.
- [Design](../../../docs/design/78_W63_재장전_음향_시간과_취소.md), [QA](../../../docs/qa/2026-10-24/w63/README.md), [audition](../../../docs/qa/2026-10-24/w63/audio/audition.html).

50 base whole-magazine weapons +11 Outlaw variants,61 runtime rows,53 deduplicated pitch-preserving Oggs/events.
All99 previous sound definitions and original Oggs remain unchanged. Incremental/bow/sword audio is not reinterpreted as a whole-magazine variant.
No original-model/reload-animation replacement, native framebuffer, input or acoustic-output claim.
`implementation.json` records current source/JAR pins; older stage implementation files remain historical.
