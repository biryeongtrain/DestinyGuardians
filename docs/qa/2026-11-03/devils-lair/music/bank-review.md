# Original Wwise arrangement recovery

The delivered `strike_devils_lair_music` bank is Wwise v150. A checksum-matching
copy was parsed using bnnm/wwiser commit `08e937b649bc7007c234bbd59e34a41d5eef3b38`.
Original Downloads files were not modified. XML and diagnostic TXTP are preserved
here; these outputs are not installed game audio.

Recovered structure: 133 HIRC objects, 68 tracks, 49 segments, 10 random/sequence
containers, 2 switch containers, 2 actions, 2 events; 40 media IDs. The main switch
has 10 routes. Track clips retain play offset, begin/end trim, source duration,
automation; segments retain entry/exit markers; nested playlists retain order/loops.

Important: source filename order and numeric state order do not identify encounters.
23 media IDs have one matching delivered duration; 17 have multiple candidates.
Even the unique matches are duration evidence, not an authenticated ID mapping.
The source package does not provide named switch states here. A byte search of the
delivered mission_raw found none of the main switch/group IDs; that search does not
prove another mapping is unavailable elsewhere.

Examples of actual authored composition:
- State 1156398949: one source, introductory region followed by a distinct repeated
  region. Replaying its entire OGG would repeat the introduction too.
- State 1156398958: four sequential regions, then repeat; generated boundaries are
  approximately 163.636 / 24.545 / 138.182 / 24.545 seconds.
- State 1156398959: ordered opening followed by randomized recurring regions and
  layered clips. A sorted list of whole OGGs does not reproduce this composition.
- State 1156398955: explicit silent loop. Silence is part of the bank structure,
  not necessarily a missing or corrupt music asset.

wwiser reports a missing Wwise bus and multitracks, so its automatic gain and TXTP
cannot be accepted as the final mix. No native audio capture or listening was done.
No new combat music has been assigned or shipped based on guesses.

## Reproduction

1. Clone the pinned wwiser revision outside the project and copy the verified bank
   into an isolated directory.
2. Run `python3 wwiser.py COPY/80D52522.bnk -d xml -dn COPY/bank -g -go COPY/txtp`.
3. Run `python3 scripts/strikes/audit_devils_music_bank.py --source SOURCE --xml
   COPY/bank.xml --output REPORT.json` (arguments on one shell line).

The audit verifies the bank, validation manifest, all 41 music OGG/WEM checksums,
and expected structure. It explicitly leaves media IDs and encounter labels
unconfirmed. Next: recover or independently corroborate the media-ID table and
encounter mapping, render source-defined arrangements, then check actual seams,
mix and lifecycle before runtime adoption.
