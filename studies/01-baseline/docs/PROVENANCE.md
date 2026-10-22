# Provenance

Where the data comes from and what I left out.

The Study 1 data includes human judgments through October 2026. The `sources` array in the data identifies the exact observation, metrics and timing snapshots by SHA-256.

## Which cases are public

The public cases are the 18 task versions that got a human quality review. Seven needed repair first, and all 18 passed in the versions now published. They are pinned in `../../../data/visibility.json`, and all three source reports agree on those case versions.

## What the release contains

The release holds allowlisted copies of the answer records for the public cases and aggregate numbers for all 120 cases per configuration. Private case text and per-case records are left out. The public request text keeps the rendered adapter prompts that were sent to each model.

The full-120 aggregates come from my private research workspace, which is the evidence archive, so they cannot be recomputed from the public subset. Builds, tests and packaging need only this repository.

## The SRD source

The wording comes from the English SRD 5.2.1. Physical page numbers refer to the full main English PDF. The public oracle passages are included. See the [attribution notice](../../../THIRD_PARTY_NOTICES.md) for the authoritative source and license.

## Judgments and history

For the 72 public Gemma 4 E4B answers (36 thinking off, 36 thinking on), the data holds final scores and fully correct and material-error results but no per-claim awards. The `claim_awards` field is empty and `historical_review` labels this. Annotations from two experts exist for the 36 thinking-on answers and stay as history.

The public final claim awards and judgments include human decisions, and the original expert annotations are stored separately. One example is the public Counterspell case, d20-en-pilot-t10-008. For Granite 4.2 8B's two answers with oracle passages, the original expert records left the Counterspell claim (25 points) unresolved. A human reviewer awarded all 25 points, which gives 100 points with thinking on and 60 with thinking off. Qwen3.5 9B's thinking-on answer with oracle passages has no material error after review and keeps 93 points.

## Published selection

I left out the superseded `tiny/qwen-off` and `tiny/qwen-on` configurations. That removes 2 configurations, 4 combinations of configuration and passage condition, 480 records and 72 public answer records. They used a mixed prompt setup with smaller output budgets, and the standard-prompt Qwen3.5 4B rerun is published. What remains is 25 configurations, 50 combinations, 6,000 records and 900 public answers.

The `sources` hashes cover the original reports, which include the excluded configurations. The three sources publish 1,920, 1,680 and 2,400 records, and their sum, 6,000, is also the sum of the 50 combination counts.

## Configuration IDs

IDs have the form `model/mode`, where the mode is `off`, `on`, `native` or `low`. Case IDs are unchanged. Each configuration stores its original ID as `source_id` and its original research batch as `batch`. `suite_id` remains the old name for the batch, in configurations, answers and source entries. Answer and combination matching uses the published configuration ID.

| Source ID | Published ID |
|---|---|
| `tiny/gemma-off` | `gemma4-e4b/off` |
| `tiny/gemma-on` | `gemma4-e4b/on` |
| `tiny/lfm-on` | `lfm2.5-2.6b/native` |
| `tiny/gemmae2-off` | `gemma4-e2b/off` |
| `tiny/gemmae2-on` | `gemma4-e2b/on` |
| `tiny/k2-low` | `k2-horizon-3.7b/low` |
| `tiny/granite-off` | `granite4.2-3b/off` |
| `tiny/granite-on` | `granite4.2-3b/on` |
| `medium/qwen4-off` | `qwen3.5-4b/off` |
| `medium/qwen4-on` | `qwen3.5-4b/on` |
| `medium/granite-on` | `granite4.2-8b/on` |
| `medium/granite-off` | `granite4.2-8b/off` |
| `medium/lfm8-on` | `lfm2.5-8b-a1b/native` |
| `medium/qwen9-off` | `qwen3.5-9b/off` |
| `medium/qwen9-on` | `qwen3.5-9b/on` |
| `large/granite-on` | `granite4.2-30b/on` |
| `large/granite-off` | `granite4.2-30b/off` |
| `large/lfm24-on` | `lfm2.5-24b-a2b/native` |
| `large/qwen27-off` | `qwen3.8-27b/off` |
| `large/qwen27-on` | `qwen3.8-27b/on` |
| `large/gemma26-off` | `gemma4-26b-a4b/off` |
| `large/gemma26-on` | `gemma4-26b-a4b/on` |
| `large/glm30-off` | `glm4.7-flash/off` |
| `large/glm30-on` | `glm4.7-flash/on` |
| `large/muse-low` | `muse-glimmer/low` |
