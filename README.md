# Team AER - FPL'26 Agentic FPGA Backend Optimization Competition

## Introduction — one-slide summary and contest information

![Team AER one-slide summary](_assets/AER_slide.png)

This repository is the submission of Team AER to the [**Agentic FPGA Backend
Optimization Competition at FPL'26**](https://xilinx.github.io/fpl26_optimization_contest/), Sponsored by AMD. 

The competition asks for an automated, agentic flow that takes a placed-and-routed Vivado design checkpoint (DCP) and returns a functionally equivalent DCP with a higher maximum clock
frequency (Fmax), within a budget of one hour of runtime and one dollar of LLM cost
per design. Submissions were scored on hidden benchmarks by the organizers.

## Results

### Final round (official, seven hidden benchmarks)

**[1st place (mean per-benchmark rank 4.286)](https://xilinx.github.io/fpl26_optimization_contest/results.html)**. Scored by the organizers on their evaluation instance. Score = α·(1 − 0.1β − 0.1γ), where α is
the Fmax improvement in MHz, β the OpenRouter cost in USD and γ the runtime in
hours ([see the contest's scoring criteria page](https://xilinx.github.io/fpl26_optimization_contest/score.html)).

| Benchmark | α (MHz) | Runtime | Score | Rank |
|---|---:|---:|---:|---:|
| amd_mini-isp_v2 (**new**) | +121.48 | 23.0 min (γ 0.384 h) | 116.773 | 7 |
| finn_radioml | +66.72 | 38.1 min (γ 0.635 h) | 62.454 | 1 |
| fir_symmetric_systolic (**new**) | +57.71 | 48.6 min (γ 0.810 h) | 53.014 | 2 |
| fir_systolic_transposed | +22.01 | 13.8 min (γ 0.230 h) | 21.494 | 4 |
| rosetta_3d-rendering_v2 (**new**) | +56.23 | 30.2 min (γ 0.503 h) | 53.379 | 4 |
| rosetta_digit-recognition | +54.44 | 40.7 min (γ 0.679 h) | 50.718 | 9 |
| vtr_mcml_v2 | +4.40 | 43.2 min (γ 0.719 h) | 4.083 | 3 |
| **Total** | | | **361.915** | **mean 4.286 → 1st** |

### Public and beta-round benchmarks (our own measurements, not final-round scores)

Both tables below were produced with the final build. The first set was scored by the
organizers' beta-round grader, which stayed available during the final round for
preview runs on the five beta benchmarks. The second set was run once per design
on the contest-provided development instance. Runtime is wall-clock from launcher start to
process exit.

**Beta-round benchmark set (scored by the beta grader)**

| Benchmark | α (MHz) | Runtime | Score |
|---|---:|---:|---:|
| amd_mini-isp | +102.04 | 20.0 min (γ 0.333 h) | 98.604 |
| boom_soc_v2 | +16.84 | 32.9 min (γ 0.548 h) | 15.916 |
| fir_systolic_transposed | +22.01 | 13.3 min (γ 0.222 h) | 21.511 |
| rosetta_optical-flow | +34.18 | 25.6 min (γ 0.426 h) | 32.712 |
| vtr_mcml_v2 | +4.40 | 42.5 min (γ 0.708 h) | 4.089 |

**Public development benchmarks (run on the contest development instance)**

| Benchmark | α (MHz) | Runtime | Score |
|---|---:|---:|---:|
| logicnets_jscl | +118.64 | 31.4 min (γ 0.523 h) | 112.43 |
| vexriscv_re-place | +179.54 | 33.8 min (γ 0.563 h) | 169.43 |
| vexriscv_re-place_v2 | +41.72 | 35.1 min (γ 0.585 h) | 39.28 |
| rosetta_spam-filter | +29.19 | 34.7 min (γ 0.578 h) | 27.50 |
| rosetta_3d-rendering | +29.46 | 27.7 min (γ 0.462 h) | 28.10 |
| rosetta_digit-recognition | +54.44 | 44.0 min (γ 0.733 h) | 50.45 |
| finn_radioml | +66.72 | 36.6 min (γ 0.610 h) | 62.65 |
| corescore_500_mod | +97.66 | 35.4 min (γ 0.590 h) | 91.90 |
| vtr_mcml | +16.64 | 45.1 min (γ 0.752 h) | 15.39 |
| ispd16_example2 | +107.97 | 46.6 min (γ 0.777 h) | 99.58 |
| boom_soc | +27.91 | 33.6 min (γ 0.560 h) | 26.35 |

## Development process and key findings

**Phase 1 — autoresearch meta-harness** 

<!-- TODO. Sookwan -->

**Phase 2 — phase 1 research-informed reconfiguration** 

Starting from that harness, the rest of the work was hands-on: many small experiments on the public benchmarks, our beta submission, an analysis of the official beta results, and a final rewrite of the decision logic based on what we had measured. The final optimizer in this repository is the product of Phase 2.

**Key findings — changes and observations across both phases.** 

The following changes and observations, made over the course of the two phases,
determined the final design:

- **From an LLM agent to a rule-based framework.** The template's LLM conversation
  loop was replaced by a deterministic framework; the LLM is consulted once, to
  choose the first action. This made runtime and behaviour predictable and, as a
  side effect, cut LLM cost.
- **Stop when improvement stops.** Once an action has improved the design and the
  next one does not, no further action is tried (in our measurements the third
  action never helped, 0 of 11). This is where most of the runtime (γ) was saved.
- **Window compaction does not work everywhere.** Packing the design into a small
  pblock window brings little on some designs and fails outright on others (e.g.
  fir_systolic_transposed), so the rule engine chooses between window compaction and
  global re-placement from measured features rather than always trying the window
  first.
- **Which unplace command matters.** Vivado offers `place_design -unplace`
  (unplaces every instance not locked by constraints) and `unplace_cell` (unplaces
  the listed cells). In our measurements the two do not leave the design in the same
  state, and which one works better depends on the design, so the command is chosen
  per design.

## Usage

Prerequisites are those of the template: Python 3.8+, Java 11+, AMD Vivado 2025.1
on `PATH` (or `VIVADO_EXEC`), and an OpenRouter API key. See
`_docs/README_FROM_CONTEST.md` for details.

```bash
git clone --recursive https://github.com/haeun-josue/fpl26contest-AER-optimizer.git
cd fpl26contest-AER-optimizer
make setup                      # installs Python deps, builds RapidWright, downloads the public benchmarks
                                # (fetches the RapidWright submodule itself if the clone was not --recursive)

export OPENROUTER_API_KEY=...   # required at startup even if the LLM call is disabled
make run_optimizer DCP=fpl26_contest_benchmarks/logicnets_jscl_2025.1.dcp   # run_optimizer
```

Command-line options, run modes and every `FPL_*` environment variable our code
reads, with defaults, are documented in [_docs/CONFIGURATION.md](_docs/CONFIGURATION.md).

The run directory (`dcp_optimizer_run-<timestamp>/`) holds the Vivado and MCP logs.

## Team AER

| Name | Affiliation |
|---|---|
| Sookwan Han (**Team leader**) | Seoul National University |
| Haeun Ji (**Main contributor**) | Kyung Hee University |
| Jun Sung | Seoul National University |
| Sihun Lim | Seoul National University |

Advisor: Jinho Lee, Seoul National University ([AISys Lab.](https://aisys.snu.ac.kr/))

## Note

The code in this repository is exactly what we submitted and what the organizers
scored in the final round; nothing was modified afterwards. Everything except
`_assets/`, `_docs/`, `README.md`, `LICENSE-APACHE-2.0.txt` and `NOTICE` is the
submitted code itself. The only thing not included is RapidWright, which is linked
as a git submodule instead of being copied in. A few things worth knowing before reading the code (stale labels, an
unused prompt file, leftover tables) are described in
[_docs/NOTES_ON_THE_CODE.md](_docs/NOTES_ON_THE_CODE.md).

The one-slide summary above does not show the whole structure of the optimizer;
for lack of space it shows only the parts that were active in the final round.
The full structure is described in [_docs/ARCHITECTURE.md](_docs/ARCHITECTURE.md).

## License

Copyright 2026 Team AER (Sookwan Han, Haeun Ji, Jun Sung, Sihun Lim).
Licensed under the Apache License, Version 2.0 — see `LICENSE-APACHE-2.0.txt`.

This repository is derived from AMD's `fpl26_optimization_contest` template
(Apache License 2.0). Files written and modified by Team AER are listed in `NOTICE`.

## Acknowledgments

Thanks to the contest organizers at AMD, including Chris Lavin, and to Prof. Jinho Lee
of the AISys Lab at Seoul National University for advising the team.
