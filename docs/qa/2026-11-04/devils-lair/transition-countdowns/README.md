# Transition and return countdowns

The plan requires advance notice before moving stragglers and a completion return timer. Both deadlines existed in DevilsSession, but neither was projected into the objective HUD.

- Existing 300-tick gathering window now displays remaining seconds in the objective text, rounded up. Moving away from the exit resets it through the existing path; no living participants now also clear the pending gathering time.
- Existing 600-tick completion window displays remaining return seconds. If the final voice is still running at zero, the HUD explicitly says return follows the report instead of showing an endless zero-second promise.
- Failed safe placement displays preparation status instead of negative seconds.
- Display projection preserves the existing hidden state, progress and interaction fields; original tracker font, layout, four-tick update cadence and ownership remain in use. These are authored Korean UX strings, not extracted original dialogue.

Validation: scoped strike JUnit and Gradle jar succeeded (counts/hashes in receipt.json). No additional UI-only test suite was added. The previous full regression run had 16 unresolved failures; this scoped run does not clear them. Native HUD rendering and countdown readability remain unverified: Computer Use again reported the Mac locked. No completion commit or commercial-quality acceptance is claimed.
