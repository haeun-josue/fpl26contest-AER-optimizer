# Architecture of the final optimizer

The one-slide summary shows the parts of the optimizer that were active in the final
round. This page describes the same structure in words, end to end, and lists at the
bottom what exists in the code but was not used.

## Overview

A run takes one placed-and-routed DCP and returns a faster one inside a fixed time
budget. The whole run is controlled by a rule-based framework inside `optimize()` in
`dcp_optimizer.py`. Vivado does all the work on the design; RapidWright is used for one
measurement; the LLM is asked exactly one question. The framework never lets an
unverified design reach the output file.

```
input.dcp
   │
   ▼
Analysis ──► Decision ──► Execution (main Vivado ‖ auxiliary Vivado)
                │                      │
                │                      ▼
                │              Validation gate ──► Update output.dcp
                │                      │
                └──── loop policy ◄────┘
                                            watchdog ends the run at the budget
```

## 1. Analysis

Vivado opens the input and the framework measures it: WNS of the contest clock, LUT
count, the share of routing delay on the worst path, high-fanout nets, how far apart
the cells of the critical paths are (spread, measured with RapidWright), and how many
clock regions those paths cross. Nothing is decided here; these numbers feed every later
step. The input is also saved to the output path immediately, so a valid output exists
from the first minute.

## 2. Decision

The design is sorted into one of two tiers by size.

**Giant designs** (about 105K LUTs and more) get one fixed recipe: clear the placement,
re-place the whole design with the `Explore` directive, route, and stop as soon as an
improvement is saved. No LLM call and no second session.

**All other designs** choose from a pool of six actions. An action combines *how* to
re-place — window compaction (C) or global re-placement (F), both described below —
with *which* placer directive to use — `ExtraTimingOpt` (D), `ExtraNetDelay_high` (N)
or `Explore` (E) — giving C-D, C-N, C-E, F-D, F-N and F-E. The rule engine ranks the
six from the analysis numbers, mainly from how many clock regions the critical paths
cross (few → window compaction, many → global re-placement) and from the routing share.
The LLM (Grok 4.3 via OpenRouter) is then asked once to pick a first action, with the
same analysis numbers and a catalog of measured results on the public benchmarks as
evidence. Its answer is accepted only if it is one of the six actions.

**The action pool, in a little more detail.**

**Window compaction (the C actions).** The framework counts the resources the design
actually uses (slices, block RAMs, DSPs, URAMs) and looks for the smallest rectangle of
clock regions, nearest to the centroid of the current placement, that can hold them at
about 60 % fill. That rectangle becomes a pblock; all fabric logic is constrained into
it (IO and clock primitives stay where they are), the old placement is cleared, and the
design is re-placed inside the window with the chosen directive and routed. Pulling a
spread-out design into a small window shortens its wires. It brings little on designs
that are already compact and fails on designs whose structure cannot be packed (for
example fir_systolic_transposed).

**Global re-placement (the F actions).** No pblock. The old placement is cleared across
the whole device and the placer starts again from scratch with the chosen directive,
then the design is routed. This is the choice when the critical paths already span many
clock regions, when the window fails, and always for giant designs, where it is run once
with the `Explore` directive.

**Routing-only rounds (rd).** Not one of the six actions; this is the closing technique of
section 6, described here with the others. Placement is kept and only `route_design` is re-run with
a different directive: `AggressiveExplore`, then `MoreGlobalIterations`, and
`NoTimingRelaxation` for designs whose critical paths were widely spread. Neither logic
nor placement changes, so the rounds are safe and cheaper than a re-placement; each
result is kept only if it is fully routed and better than the saved design. The rounds
end after two rounds without gain or when time runs low, and one `phys_opt_design`
pass follows if enough time is left.

## 3. Execution

The first action runs in two Vivado sessions at once: the main session runs the rule
engine's top choice, an auxiliary session runs the LLM's choice (or the rule engine's
second choice when the two agree). Both start from the input. Each action clears the old
placement, either fully with `place_design -unplace` or cell by cell with `unplace_cell`
(the framework picks one per design), re-places with the chosen directive, and routes.

## 4. Validation

Every candidate design passes a gate before it can count: fully routed, no unplaced
cell, no hold violation, no pulse-width violation, no DRC error, and a measured WNS
better than the design already saved. The gate is the only way into the output file. A
candidate that fails is discarded and the session is reverted to the saved best.

## 5. Update

When the main and auxiliary results are both in, the better one that passed the gate
becomes the saved output. From then on the run continues from that design.

## 6. Loop policy

After the first action, up to two more actions are chosen by rules from what has been
observed: which action family improved or failed, and how much time is left. Each
candidate is started only if its estimated runtime fits the remaining budget. If an
action improved the design and the next one did not, no further action is tried. When
time remains, the run finishes with routing-only rounds (`route_design` with different
directives, which change no logic) and, if there is still time, one more `phys_opt_design`
pass.

## 7. Time budget

The budget is 3,540 seconds from the start of the run. A separate watchdog thread ends
the process cleanly at that point no matter what Vivado is doing, kills the auxiliary
session, and leaves the best saved design as the output.

## Notes: present in the code, not used in the final round

- A middle size tier between 105K and 160K LUTs; both thresholds were set to 105K, so
  the branch cannot be reached.
- The template's LLM conversation loop and `SYSTEM_PROMPT.TXT`; the framework does not
  call them.
- Two rule-engine functions (`g2_decision`, `value_ok`) and the fingerprint tables in
  `_fpl_knowledge.py` (`FINGERPRINTS`, `ANSWER_SHEET`); nothing calls them.
- Optional switches that were off in the submission: hold repair, harvesting of
  intermediate designs, and test overrides (see `CONFIGURATION.md`).
- A last-resort save for giant designs in the final two minutes; it did not fire in any
  official run.
- The CustomToolMCP server, which starts but registers no tool.
