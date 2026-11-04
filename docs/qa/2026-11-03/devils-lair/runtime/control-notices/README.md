# GCB notices no longer interrupt strike presentation

Observed defect: `../route-clearance-live/framebuffer.png` shows the GCB installation
recommendation over Zavala's briefing subtitle. The matching client log records
that recommendation at22:49:13. The earlier ledger called it a tutorial notice;
that attribution was incorrect. The upper-right unsigned-chat toast is Minecraft's
own warning and is not removed by this change.

`ClientControls` now continues handshake/capability detection immediately, while
queueing optional GCB recommendations and installation announcements per recipient.
It drains only after client loading, outside a Devils' Lair session and outside the
existing CombatHud cinematic predicate. Deferral covers admission/world loading as
well as running strike sessions, avoiding the original5-second recommendation race.

A newly detected GCB client cancels its queued install recommendation. Installation
announcements deduplicate by subject UUID, with a32-subject bound per recipient;
older optional announcements are discarded on overflow. The personal recommendation
is kept separately. Normal connection teardown clears the owning Session and its queue;
death/respawn retains the current connection's pending notices. Other recipients can
receive their notices immediately. Existing chat history/user messages are untouched,
so this is not a claim to prevent every possible chat/subtitle overlap.

Validation: targeted14JUnit tests passed and real Gradle jar passed. Three relevant
compiled classes match the JAR byte-for-byte. Full regression result recorded separately.
Actual post-change framebuffer remains unverified: Computer Use still reports a locked
Mac. No QA client was started, no production deployment, no visual-acceptance commit.

Next native scenario: join without GCB and start strike before5seconds; confirm no
recommendation over briefing, leave and confirm one recommendation. Repeat with a
late GCB handshake and a second recipient in a cinematic; verify independent delivery
and disconnect cleanup. The native upper-right warning must be reported separately.
