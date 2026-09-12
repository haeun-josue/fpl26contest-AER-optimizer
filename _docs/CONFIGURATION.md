# Configuration

How the optimizer is invoked, and every environment variable our code reads.

## Invocation

```bash
python3 dcp_optimizer.py <input.dcp> [--output <out.dcp>] [--api-key KEY] [--model ID] [--debug]
make run_optimizer DCP=<input.dcp>        # same, via the organizers' Makefile
```

| Option | Default | Meaning |
|---|---|---|
| `input_dcp` | required | Placed-and-routed input checkpoint |
| `--output`, `-o` | `<input>_optimized-<timestamp>.dcp` next to the input | Where the best routed design is written |
| `--api-key` | `$OPENROUTER_API_KEY` | OpenRouter key. Startup refuses to run without one, even when the LLM call is disabled with `FPL_LLM=0` |
| `--model` | `x-ai/grok-4.3` | Template option; our one-shot call uses `FPL_LLM_MODEL` instead (see below) |
| `--debug` | off | Verbose logging |
| `--test`, `--max-nets` | | Template test mode (the organizers' example optimizations). Not our optimizer |

The organizers' evaluation harness runs `make setup` once and then
`make run_optimizer DCP=<benchmark>.dcp` once per benchmark. That Makefile target
executes `python3 dcp_optimizer.py <benchmark>.dcp` with no other options, so the
output lands at the default location next to the input
(`<benchmark>_optimized-<timestamp>.dcp`, which is where the harness looks for it).
`OPENROUTER_API_KEY` is provided by the organizers; no `FPL_*` variable is set, so the
scored runs used every default below.

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `OPENROUTER_API_KEY` | required | Key for the single LLM call (OpenRouter, base URL `https://openrouter.ai/api/v1`) |
| `VIVADO_EXEC` | `vivado` | Vivado executable, used for the auxiliary Vivado session (the main session is started by the template's VivadoMCP server, which has its own lookup) |
| `FPL_BUDGET_S` | `3540` | Total time budget in seconds from process start. An independent watchdog thread calls `os._exit(0)` when it is reached, after the best routed design has been saved |
| `FPL_DEADLINE` | `0` | Absolute Unix-time deadline. When non-zero it replaces the budget above |
| `FPL_LLM` | `1` | `0` skips the one LLM call; the rule engine's second choice fills the auxiliary session instead |
| `FPL_LLM_MODEL` | `x-ai/grok-4.3` | Model id for that call |
| `FPL_PARALLEL` | `1` | `0` disables the auxiliary Vivado session for the first action (single session only). The auxiliary session is also skipped automatically for designs with ≥105K LUTs or when less than 18 GB of memory is available |
| `FPL_GIANT_MAX_ROUNDS` | `40` | Upper bound on route-directive rounds |
| `FPL_DECISION_LOG` | `1` | Writes `decision_log.jsonl`, `llm_g1_prompt.txt` and `llm_g1_response.txt` into the run's temporary directory. `0` disables |
| `FPL_HOLD_REPAIR` | `0` | Experimental hold-repair pass; off in the submission |
| `FPL_HARVEST` | `0` | Diagnostic: copy intermediate designs into `FPL_HARVEST_DIR` (default `<temp>/harvest`); off in the submission |
| `FPL_FORCE_G1` | unset | Test override: force the main session's first action (`C-D`, `C-N`, `C-E`, `F-D`, `F-N`, `F-E`) |
| `FPL_REPLACE_DIR` | unset | Test override: placement directive for the giant-tier re-placement (default `Explore`) |

Action names: `C` = window compaction into a pblock, `F` = global re-placement;
`D` = `ExtraTimingOpt`, `N` = `ExtraNetDelay_high`, `E` = `Explore`.

## Run directory

Each run creates `dcp_optimizer_run-<timestamp>/` next to `dcp_optimizer.py`, holding
the Vivado log and journal, the three MCP server logs, the token-usage report and,
with `FPL_DECISION_LOG=1`, the decision log and the LLM prompt and response.
