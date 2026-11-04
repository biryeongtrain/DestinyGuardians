# W151 Bad Omens / Code Duello ADS

Opened both cached default Bungie photos from `/tmp/destiny-weapons-w31/references/`. Bad Omens has a right-offset recessed optic/rubber bellows, teal tube, silver collars and brown wood grips; Code Duello has a right-offset copper optic and gold/teal fluted tube. Existing W130/W132 semantic body and all canonical HIP/third/reload assets are unchanged.

The canonical optics had opaque glass/rear plugs. The ADS-only copies remove those named pieces, preserve their surrounding tube walls and original face UV, add a thin octagonal open rear rim for Bad Omens, and add a tiny physical luminous post/shoulder inside each aperture. This is a clear no-refraction sight proxy, not restoration of the original game lens shader.

- bad_omens: 123 emitted cubes; removed optic_bellows_core, optic_bellows_bevel_a, optic_rear_socket, right_recessed_glass; ray [9.72, 12.18, 8.225] along -Z.
- code_duello: 217 emitted cubes; removed Optic_recessed_lens, Optic_rear_termination; ray [9.55, 12.0, 6.85] along -Z.

Targeted rotation-aware ray check initially found `right_recessed_glass` still obstructing Bad Omens; corrected the explicit removal list rather than claiming the empty aperture was already valid. Both final center/upper aperture rays clear. Actual gameplay/PNG review pending integrated QA.
