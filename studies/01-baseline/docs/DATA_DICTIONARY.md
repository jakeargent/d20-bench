# Data dictionary

The public data files and what their fields mean. All files are UTF-8 JSON with `schema_version: 1`.

## Files

| File | Contents | Disclosure |
|---|---|---|
| `../../../data/visibility.json` | The 18 public case IDs, exactly, and the basis for choosing them | No private case IDs |
| `../../../data/cases.json` | Questions, reference answers, reviewed claim rubrics and oracle passages | Public cases only |
| `../data/answers.json` | 900 final answers, the exact request text sent to the model, final scores and claim awards, historical expert annotations, operations and request timing | Public cases only |
| `../data/results.json` | 25 configurations, 50 full-120 cells (one per configuration and passage condition) | Aggregates include the private cases; no private per-case rows |

`../config.json` holds model metadata and data-integrity checks.

## Identifiers

Configuration IDs have the form `model/mode`.

The mode in a configuration ID is `off`, `on`, `native` or `low`. `native` marks the LFM2.5 models, which cannot turn thinking off and ran with thinking on. `low` marks K2 Horizon and Muse Glimmer, which cannot turn thinking off and ran at a low reasoning-effort setting. Qwen3.8 27B `on` also ran at low reasoning effort.

To match an answer record to its configuration and case, use the three fields `configuration`, `case_id` and `condition` together. `condition` is `no_source` (without oracle passages) or `supplied_passage` (with oracle passages).

## Scores and reviews

- `score.earned_points` is the sum of the final claim awards, out of 100.
- `claim_awards` holds the per-claim points, including human judgments. It is empty for the 72 public Gemma 4 E4B answers (36 thinking off, 36 thinking on). For these answers the data holds final scores and fully correct and material-error results but no per-claim awards, and `historical_review` labels this.
- For the 36 thinking-on answers among them, `historical_expert_annotations` holds annotations from two graders, labeled `grader_1` and `grader_2`.
- `expert_annotation` holds grader claim judgments and source findings. `original_expert_score` is the grader score where available; `final_review` describes the human judgment. Final scores and correctness judgments are in `score`.
- `score.complete_task_success` and `score.has_material_error` hold the final fully correct and material-error judgments. Each is true, false or null (unknown), and null answers are left out of the counts.
- `profile_assessed` and `material_error_assessed` in the quality summary give the number of answers that could be graded. They are the denominators of the fully correct and material-error counts. A few answers couldn't be graded as clearly right or wrong; those are left out, so some counts are out of fewer than 120.

`unknown_judgments` counts answers flagged for grading uncertainty in the aggregate summaries, including individual assertions that could not be graded. An answer can have a final score and correctness judgment while another assertion remains unknown. Use `profile_assessed` and `material_error_assessed` for the final correctness denominators.

## Timing and tokens

- `request_timing.total_attempt_seconds` adds up all recorded attempts for the answer.
- `request_timing.has_final` means the answer has a non-empty final section.
- `operations` and the token distributions describe the response. Raw thinking traces are not exported, and reasoning-token counts may be missing.
- Aggregate timing includes the mean, the median, nearest-rank quartiles and tails, coverage, retries and conditional-final statistics.

## Request text

`candidate_request` holds prompt text only: either the rendered raw-completion `prompt`, or a native `system_prompt` and `input`. Text paths and private addresses are redacted where they appeared.

## Runtime metadata

`runtime_version`, `exact_gpu_placement`, `selected_variant` and `reasoning_effort` are null when not recorded. `generation_seed` is null when no seed was recorded; `generation_seed_status` is `not set` when no seed was set.

## Parameter counts and size classes

I checked the counts in October 2026 against vendor model cards and the safetensors metadata of each official repository.

`total_parameters` is the integer `safetensors.total` that Hugging Face reports for the pinned official artifact. It includes embeddings and any modality components counted in that artifact. It is one consistent convention for totals and can differ from the rounded number in a model's name. The table below rounds to three decimals of a billion; each configuration stores the exact integer.

`active_parameters` is an active count the vendor explicitly published. Null means I found no separate active count, as for dense models. For Gemma 4 E2B and E4B, the effective counts are stored separately as `effective_parameters` (2.3B and 4.5B). Active counts follow each vendor's convention, so they may not be comparable with full-artifact totals.

`parameter_source_url` pins the official artifact metadata. `parameter_card_url` and `parameter_card_sha256` identify the model card I checked. `parameter_notes` records differences in scope.

| Model | Total B | Active B | Size class | Sources |
|---|---:|---:|---|---|
| LFM2.5 2.6B | 2.697 | unknown | small | [artifact](https://huggingface.co/api/models/LiquidAI/LFM2.5-2.6B/revision/654f9463ce32b05d0429d76fe1f580b27d4c1ac0), [card](https://huggingface.co/LiquidAI/LFM2.5-2.6B/blob/654f9463ce32b05d0429d76fe1f580b27d4c1ac0/README.md) |
| Granite 4.2 3B | 3.660 | unknown | small | [artifact](https://huggingface.co/api/models/ibm-granite/granite-4.2-3b/revision/4e9c275e232f10211ec88644d106a1f6a1b60e06), [card](https://huggingface.co/ibm-granite/granite-4.2-3b/blob/4e9c275e232f10211ec88644d106a1f6a1b60e06/README.md) |
| Qwen3.5 4B | 4.660 | unknown | small | [artifact](https://huggingface.co/api/models/Qwen/Qwen3.5-4B/revision/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a), [card](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md) |
| K2 Horizon 3.7B | 5.058 | 3.7 | small | [artifact](https://huggingface.co/api/models/IFM/K2-Horizon-3.7B/revision/9d280ff742235796925c9fe3cf243dc1beea5c08), [card](https://huggingface.co/IFM/K2-Horizon-3.7B/blob/9d280ff742235796925c9fe3cf243dc1beea5c08/README.md) |
| Gemma 4 E2B | 5.123 | unknown | small | [artifact](https://huggingface.co/api/models/google/gemma-4-E2B-it/revision/3e22461f65e89153144f8adb70e3b8c2cc9845a7), [card](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md) |
| Gemma 4 E4B | 7.996 | unknown | medium | [artifact](https://huggingface.co/api/models/google/gemma-4-E4B-it/revision/ee0ef6023621cff504d758262d4e04895a5af4a2), [card](https://huggingface.co/google/gemma-4-E4B-it/blob/ee0ef6023621cff504d758262d4e04895a5af4a2/README.md) |
| LFM2.5-8B-A1B | 8.468 | 1.5 | medium | [artifact](https://huggingface.co/api/models/LiquidAI/LFM2.5-8B-A1B/revision/5dd22602c2e9f6a097b1de4c4efe0658b605015c), [card](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B/blob/5dd22602c2e9f6a097b1de4c4efe0658b605015c/README.md) |
| Granite 4.2 8B | 8.792 | unknown | medium | [artifact](https://huggingface.co/api/models/ibm-granite/granite-4.2-8b/revision/a7042144125ce5ae64f89610e8289647fc000b9a), [card](https://huggingface.co/ibm-granite/granite-4.2-8b/blob/a7042144125ce5ae64f89610e8289647fc000b9a/README.md) |
| Qwen3.5 9B | 9.653 | unknown | medium | [artifact](https://huggingface.co/api/models/Qwen/Qwen3.5-9B/revision/c202236235762e1c871ad0ccb60c8ee5ba337b9a), [card](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/README.md) |
| LFM2.5-24B-A2B | 23.972 | 2.45 | large | [artifact](https://huggingface.co/api/models/LiquidAI/LFM2.5-24B-A2B/revision/3fcfdbfa1a1b6d8166846a6323e69f1e1254440d), [card](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B/blob/3fcfdbfa1a1b6d8166846a6323e69f1e1254440d/README.md) |
| Gemma 4 26B-A4B | 25.806 | 3.8 | large | [artifact](https://huggingface.co/api/models/google/gemma-4-26B-A4B-it/revision/4d7ae4984b7db7de8f8457170b3f1a419ee76d52), [card](https://huggingface.co/google/gemma-4-26B-A4B-it/blob/4d7ae4984b7db7de8f8457170b3f1a419ee76d52/README.md) |
| Qwen3.8 27B | 27.781 | unknown | large | [artifact](https://huggingface.co/api/models/Qwen/Qwen3.8-27B/revision/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0), [card](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md) |
| Granite 4.2 30B | 29.277 | unknown | large | [artifact](https://huggingface.co/api/models/ibm-granite/granite-4.2-30b/revision/9e668ce1c538387ef24d3644e9b0606647762636), [card](https://huggingface.co/ibm-granite/granite-4.2-30b/blob/9e668ce1c538387ef24d3644e9b0606647762636/README.md) |
| Muse Glimmer | 29.777 | unknown | large | [artifact](https://huggingface.co/api/models/meta-models/Muse-Glimmer-30B/revision/7af58019cf472021aae5480731c9ae8e141b56c7), [card](https://huggingface.co/meta-models/Muse-Glimmer-30B/blob/7af58019cf472021aae5480731c9ae8e141b56c7/README.md) |
| GLM-4.7 Flash | 31.221 | 3 | large | [artifact](https://huggingface.co/api/models/zai-org/GLM-4.7-Flash/revision/7dd20894a642a0aa287e9827cb1a1f7f91386b67), [card](https://huggingface.co/zai-org/GLM-4.7-Flash/blob/7dd20894a642a0aa287e9827cb1a1f7f91386b67/README.md) |

The observed clusters are 2.697–5.123B (small), 7.996–9.653B (medium) and 23.972–31.221B (large).

- Gemma 4 E2B (5.123B) and K2 Horizon 3.7B (5.058B) sit at the upper edge of the small class.
- Gemma 4 E4B counts as medium because its total is 7.996B.
- LFM2.5-8B-A1B stays medium despite its 1.5B active count.
- LFM2.5-24B-A2B is at the low end of large.

No total falls in the gaps between the clusters. The classes describe this selection of models.

Model names and cards often differ from the artifact totals:

- Gemma 4 26B-A4B: the card gives 25.2B for the language model and about 0.55B for the vision encoder. The artifact total is 25.806B.
- Qwen: the cards label the language models 4B, 9B and 27B. The artifact totals are 4.660B, 9.653B and 27.781B.
- LFM2.5: the cards give 2.69B, 8.3B and 24.0B totals. The artifact totals are 2.697B, 8.468B and 23.972B.
- K2 Horizon 3.7B: the 3.7B core/activated count excludes part of its 5.058B total.
- Granite: the cards identify dense 3B, 8B and 30B models. The artifact totals are 3.660B, 8.792B and 29.277B.
- GLM: the nominal 30B-A3B corresponds to a 31.221B artifact.
- Muse Glimmer: the card rounds its dense model, including vision, to about 29.6B. The artifact metadata gives 29.777B.

