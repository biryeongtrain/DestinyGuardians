# W59 per-weapon firing recovery

W58 connected base Handling to outgoing stow + incoming ready, but WeaponRuntime
still reused one WeaponCycle.readyAt across every ranged item owned by a player.
A fired Bad Omens (48-tick base cadence) therefore delayed a newly readied
Austringer even after its own actual Handling transition completed.

W59 separates the **actual stack's firing deadline** from the shared owner input
session. Only a numeric fractional deadline survives a rebind. Reload, burst,
charge, held-input and ammunition are never cached or restored by the bank.
Returning to the original actual stack restores its unexpired firing deadline;
a distinct ranged stack uses its own deadline plus the independent W58 Handling
transition. Same family/id/equal component values are not ownership keys.

The firing/Handling numeric inputs are unchanged:

- [W46 sources and units](../w46/README.md): official selected item RPM, fixed
  Oracle frame-specific cadence/charge/burst recovery, 20 Hz fractional scheduling.
- [W58 Handling sources](../w58/README.md): official Handling plus pinned historical
  ready/stow curves. No new current-sandbox formula was fetched or measured.
- [W58 previous implementation boundary](../../../docs/design/73_W58_무기_교체_Handling.md)
  explicitly retained the old shared ranged cadence. This limitation is superseded
  for distinct ranged stacks by W59, not retrospectively rewritten in old evidence.

**Policies, not verified exact D2 interrupt internals:** first observation remains
already equipped, same-stack deadlines remain live across a skill/paid dodge,
existing sword actor recovery remains owner-shared to prevent cross-sword melee
animation/lunge resets, and W58 stow/draw interruption rules stay unchanged.
This change models independently recovering weapons but is not a frame-measured
reconstruction of all original quickswap/animation-cancel techniques.

Each owner State has at most128 identity clocks. Writes prune expired entries.
A pathological full bank retains every live clock and uses a conservative overflow
maximum until expiry instead of evicting a deadline and enabling a bypass. This
is a documented server-safety limit, not normal D2 behavior. All clocks are
transient and released by existing owner cleanup; no player NBT timers or item
copies/UUID tags are introduced. Sword actor/overflow clocks are numeric only.
