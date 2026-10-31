# Limitations

Study 1 is an exploratory comparison of 25 configurations, with no preregistration.

## Comparing models

- Models differ in architecture, total and active parameters, sampling, templates and output budgets. Qwen is version 3.5 at the smaller sizes and 3.8 at the larger size, so version and size change together.
- Parameter totals come from the official checkpoint files. Active counts follow each vendor's convention, and where a vendor publishes none, the count is unknown.

## The questions

- Eighteen task versions got a human quality review. An AI reviewed the rest and I checked them, without a full source-backed review. All 120 tasks are development material, and the 18 public cases are a small subset.
- The 72 public Gemma 4 E4B answers (36 thinking off, 36 thinking on) have final scores and fully correct and material-error results but no per-claim awards. The expert annotations that exist for them stay separate.

## Grading

- One model, GPT 6.1 Sol at medium effort, graded each new answer. I did not measure its accuracy, and a human reviewed only some cases.
- Each question was answered once per configuration and passage condition, so the data shows no run-to-run variation.
- A few answers couldn't be graded as clearly right or wrong; those are left out, so some counts are out of fewer than 120.
- Mean claim scores sum the points awarded per claim. An answer can earn every claim point and still add a wrong rule.

## Timing and runtime

- Context and token ceilings, request deadlines and retries shape the completion times, which come from one run on one machine. Grading and model loading are separate costs outside the times.
- I did not record the exact llama.cpp CUDA 12 backend version I used with LM Studio 0.4.x. The GPU also drove my desktop display. LM Studio's echoed load settings show the configuration I requested; GPU placement and peak VRAM were not measured.
- Generation-speed medians pool both passage conditions from the 18 public cases. They exclude retries and answers shorter than 100 output tokens. Some configurations lack first-token timing, which leaves prompt and client overhead in the rate's denominator.

## The data

- The private task set and raw private answers are excluded, so the full-120 aggregates cannot be recomputed from this public release.

## VRAM estimates

I did not measure VRAM use. I calculated these estimates after the runs. Each one adds three things:

- the file size of a public Q4_K_M GGUF file, as a stand-in for the weights;
- the KV or recurrent state (the memory a model keeps for the text so far) at the configured context;
- **1 GiB of assumed runtime overhead**.

GiB means bytes divided by 2³⁰. Each row combines the thinking modes. Model names link to the weight files I used as proxies, and the cache figures link to the architecture configs. The linked files are public stand-ins for the files I evaluated.

| Model | Context tokens | Weights GiB | KV/state GiB | Estimated total GiB |
|---|---:|---:|---:|---:|
| [Gemma 4 E4B](https://huggingface.co/lmstudio-community/gemma-4-E4B-it-GGUF/blob/main/gemma-4-E4B-it-Q4_K_M.gguf) | 32,768 | 4.97 | [0.539](https://huggingface.co/google/gemma-4-E4B-it/blob/ee0ef6023621cff504d758262d4e04895a5af4a2/config.json) | 6.51 |
| [LFM2.5 2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF/blob/main/LFM2.5-2.6B-Q4_K_M.gguf) | 32,768 | 1.56 | [0.500](https://huggingface.co/LiquidAI/LFM2.5-2.6B/blob/654f9463ce32b05d0429d76fe1f580b27d4c1ac0/config.json) | 3.06 |
| [Gemma 4 E2B](https://huggingface.co/lmstudio-community/gemma-4-E2B-it-GGUF/blob/main/gemma-4-E2B-it-Q4_K_M.gguf) | 65,536 | 3.19 | [0.387](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/config.json) | 4.58 |
| [K2 Horizon 3.7B](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/blob/main/K2-Horizon-4B-Q4_K_M.gguf) | 65,536 | 2.94 | [9.000](https://huggingface.co/IFM/K2-Horizon-3.7B/blob/9d280ff742235796925c9fe3cf243dc1beea5c08/config.json) | 12.94 |
| [Granite 4.2 3B](https://huggingface.co/ibm-granite/granite-4.2-3b-GGUF/blob/main/granite-4.2-3b-Q4_K_M.gguf) | 65,536 | 2.09 | [5.000](https://huggingface.co/ibm-granite/granite-4.2-3b/blob/4e9c275e232f10211ec88644d106a1f6a1b60e06/config.json) | 8.09 |
| [Qwen3.5 4B](https://huggingface.co/lmstudio-community/Qwen3.5-4B-GGUF/blob/main/Qwen3.5-4B-Q4_K_M.gguf) | 65,536 | 2.52 | [2.049](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/config.json) | 5.57 |
| [Granite 4.2 8B](https://huggingface.co/ibm-granite/granite-4.2-8b-GGUF/blob/main/granite-4.2-8b-Q4_K_M.gguf) | 65,536 | 4.98 | [10.000](https://huggingface.co/ibm-granite/granite-4.2-8b/blob/a7042144125ce5ae64f89610e8289647fc000b9a/config.json) | 15.98 |
| [LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF/blob/main/LFM2.5-8B-A1B-Q4_K_M.gguf) | 65,536 | 4.80 | [0.750](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B/blob/5dd22602c2e9f6a097b1de4c4efe0658b605015c/config.json) | 6.55 |
| [Qwen3.5 9B](https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/blob/main/Qwen3.5-9B-Q4_K_M.gguf) | 65,536 | 5.24 | [2.049](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/config.json) | 8.29 |
| [Granite 4.2 30B](https://huggingface.co/ibm-granite/granite-4.2-30b-GGUF/blob/main/granite-4.2-30b-Q4_K_M.gguf) | 65,536 | 16.50 | [16.000](https://huggingface.co/ibm-granite/granite-4.2-30b/blob/9e668ce1c538387ef24d3644e9b0606647762636/config.json) | 33.50 |
| [LFM2.5-24B-A2B](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B-GGUF/blob/main/LFM2.5-24B-A2B-Q4_K_M.gguf) | 65,536 | 13.53 | [1.250](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B/blob/3fcfdbfa1a1b6d8166846a6323e69f1e1254440d/config.json) | 15.78 |
| [Qwen3.8 27B](https://huggingface.co/lmstudio-community/Qwen3.8-27B-GGUF/blob/main/Qwen3.8-27B-Q4_K_M.gguf) | 65,536 | 15.66 | [4.146](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/config.json) | 20.80 |
| [Gemma 4 26B-A4B](https://huggingface.co/lmstudio-community/gemma-4-26B-A4B-it-GGUF/blob/main/gemma-4-26B-A4B-it-Q4_K_M.gguf) | 65,536 | 15.64 | [1.543](https://huggingface.co/google/gemma-4-26B-A4B-it/blob/4d7ae4984b7db7de8f8457170b3f1a419ee76d52/config.json) | 18.19 |
| [GLM-4.7 Flash](https://huggingface.co/lmstudio-community/GLM-4.7-Flash-GGUF/blob/main/GLM-4.7-Flash-Q4_K_M.gguf) | 65,536 | 16.89 | [3.305](https://huggingface.co/zai-org/GLM-4.7-Flash/blob/7dd20894a642a0aa287e9827cb1a1f7f91386b67/config.json) | 21.19 |
| [Muse Glimmer](https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF/blob/main/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf) | 65,536 | 15.61 | [0.908](https://huggingface.co/meta-models/Muse-Glimmer-30B/blob/7af58019cf472021aae5480731c9ae8e141b56c7/config.json) | 17.51 |

The estimate of 33.50 GiB for Granite 4.2 30B exceeds the card's 24 GB, so part of the model may have run off the GPU, which would slow its times. Every other row is at or below 21.19 GiB.

The calculation assumes one loaded model and one generation sequence, FP16 K/V, FP32 hybrid recurrent/convolution states, and full configured capacity for full-attention caches. Sliding-window caches use compact allocation with `round_up(window + 512, 256)` slots, assuming a 512-token microbatch. Gemma's cross-layer cache sharing and GLM's compressed MLA cache are included. These assumptions follow [llama.cpp cache defaults](https://github.com/ggml-org/llama.cpp/blob/master/common/common.h), [sliding-window allocation](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-kv-cache-iswa.cpp), [hybrid state allocation and cache sharing](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-model.cpp) and [MLA cache storage](https://github.com/ggml-org/llama.cpp/blob/master/src/llama-kv-cache.cpp).

Cache precision, allocation mode, per-slot state replication and runtime buffers were not measured, and LM Studio reported four parallel slots. The estimates leave out separate vision/audio projectors and extra speculative or rollback states. The Qwen3.8 MTP allocation is unknown.

Gemma 4 26B-A4B's estimate rises from 18.19 to 30.39 GiB if sliding-window layers get full-context caches. The same alternative gives 7.72 GiB for Gemma 4 E4B, 5.32 for Gemma 4 E2B and 19.86 for Muse Glimmer. Such assumptions can move an estimate across the GPU's 24 GB capacity.
