# Methods

How I ran Study 1: the questions, the configurations and prompts, the hardware, the grading, and how I counted time and tokens.

## The questions

I used 120 English SRD 5.2.1 questions in 12 topics. I asked each one twice: without oracle passages, and with them. Oracle passages are the SRD passages the task authors marked as the ones they used to write the task.

Each question has required claims. Every claim has a reviewed weight and explicit partial-credit rules, and the weights total 100. An answer's score is the sum of the points awarded across its claims. Material errors, meaning wrong rules an answer adds, are recorded separately and carry no deduction.

Eighteen task versions got a human quality review: twelve random picks by topic and six picked on purpose. Seven of the 18 needed repair first. All 18 passed in the versions now published, and those 18 are the public set. An AI reviewed the quality of the other 102 tasks, and they stay private.

All 120 were development cases I used while exploring.

## The configurations and prompts

I published 25 configurations and 6,000 answer records. A configuration is one model checkpoint with one thinking setting, sampler, context budget and output ceiling. All 25 used Q4_K_M GGUF files. The 6,000 records are one answer for each question, configuration and passage condition (25 × 2 × 120), so each of the 50 combinations of configuration and passage condition has 120 answers. This release shows 18 of them in detail, which makes 900 public answer records. The model-based IDs, parameter sources and sampling settings are in `../data/results.json`.

I group comparisons by total parameters: small (approximately 4B), medium (approximately 9B) and large (approximately 30B). The classes cover totals of 2.7–5.1B, 8.0–9.7B and 24–31B. Embeddings count toward the total. The data dictionary lists the totals, and the active counts where vendors publish them.

The published Qwen3.5 4B results come from a standard-prompt rerun. An earlier run used a mixed prompt setup with smaller output budgets and is excluded.

I ran Gemma 4, Granite 4.2, Qwen3.5 4B and 9B, Qwen3.8 27B and GLM-4.7 Flash with thinking off and with thinking on. Qwen3.8 27B ran its thinking-on configuration at low reasoning effort. LFM2.5, K2 Horizon and Muse Glimmer cannot turn thinking off. LFM2.5 ran with thinking on, which is its only mode. K2 Horizon ran with the creator's low-effort prefix and Muse Glimmer with its low reasoning-effort setting. The configuration metadata and the public request text record each setting. Each provider's recommended sampler also differs.

Gemma 4 E4B and LFM2.5 2.6B use a 32,768-token context and an 8,192-token output ceiling. The other 22 configurations use a 65,536-token context and a 32,768-token ceiling, which covers thinking and the final answer together.

## Hardware and runtime

I ran the models in October 2026 on one NVIDIA RTX 3090 (24 GB), an AMD Ryzen 9 5950X and 64 GB RAM, under Windows 11. The GPU also drove the desktop display. I used LM Studio 0.4.x with llama.cpp CUDA 12 backends. Exact backend builds and VRAM use were not recorded.

When my test harness loaded a model, it gave LM Studio only the model key and the context length. Every other load setting was LM Studio's default. The provider-recommended samplers are recorded in the configuration metadata. LM Studio's echoed load settings showed four parallel slots and GPU-resident KV caches (the memory a model uses to keep track of the text so far). Flash attention was on, except for K2 Horizon 3.7B and Qwen3.5 4B, where it was off. Speculative decoding was off, except for Qwen3.8 27B, where LM Studio turned on MTP (multi-token prediction) by default. Logs show I requested full GPU offload for Granite 4.2 30B and Qwen3.8 27B. Actual GPU placement was not measured.

Local generations ran one at a time, even though four slots were configured. The cloud grading calls eventually overlapped with generation and reached up to 32 concurrent calls.

## Grading

Each new answer got one GPT 6.1 Sol review at requested Medium effort, with complete access to the authoritative SRD. I added targeted human review for some cases, and the 72 public Gemma 4 E4B answers keep the expert and human review they already had. I did not measure grader accuracy. With thinking on, I graded the final answer. With thinking off, any self-talk the model returned counts as part of the answer. Repairs to records and citations kept the original judgments.

Where a human reviewer changed a claim award or an answer's fully correct or material-error result, the final `claim_awards` hold the human result. The original expert annotations stay in the data as history, and they can differ.

A fully correct answer satisfies every required claim and has no material error. A few answers couldn't be graded as clearly right or wrong. I treat those as unknown and leave them out of the counts. So some counts are out of fewer than 120, and percentages use the number of answers that could be graded.

Where two SRD passages conflicted over land-vehicle pace, I followed the more specific one. This changed the fully correct and material-error results of three answers from large-class models, and no claim score.

## Time and tokens

I time a single model response against a target of about 5 seconds, with 30 seconds as the hard cutoff.

Request time is the client-side elapsed time summed over every recorded attempt for the answer, retries included. It leaves out model loading and grading. Two GLM thinking-on requests needed retries because the first outputs lacked a closed thinking section and a final answer. Both retries succeeded.

The tables report the mean, the median, p25 and p75 (the quartiles), p95, the maximum, and the number of requests above 30 seconds. The p95 is the slower end of the distribution, where 1 request in 20 is slower. Quartiles and tail percentiles use the nearest-rank method. The median averages the two middle values when the count is even. The all-outcome times include failed and capped outcomes. A second population keeps the answers with a non-empty final answer, which can still be truncated or wrong. Answers with missing timing are left out and the coverage is shown. Token statistics describe the responses, and missing thinking-token counts are shown as unknown.

The build also exports generation-speed medians for each configuration, with sample counts, as `speed.csv` and `speed.json` in the generated study site directory. They use the 18 public cases, pool both passage conditions, and have at most 36 answers per configuration. An answer counts if it has exactly one recorded attempt, at least 100 output tokens and a positive finite duration. Its rate is
`operations.total_output_tokens / (request_timing.selected_request_seconds − request_timing.first_token_seconds)`.
When first-token timing is missing, the denominator is the whole request time, and `n_first_token_timing` shows how many eligible answers have that measurement. The median averages the two middle rates when needed, and an empty group has a null median. The rates are computed on the client side and include any overhead beyond decoding, so they can differ from LM Studio's own `operations.tokens_per_second`.

On one RTX 3090, [neoX's Q4_K_M inference tests](https://ahelpme.com/ai/llm-inference-using-riser-extender-cable-and-oculink-cable/2/) report 32.60–34.37 tokens per second for Qwen2.5 32B, 35.94–38.14 for Gemma 3 27B and 114.77–125.18 for DeepSeek-R1-Distill-Llama 8B, across generation lengths of 128–2,048 tokens with no prompt tokens. [No-Statement-0001's Qwen2.5-Coder 32B tests](https://www.reddit.com/r/LocalLLaMA/comments/1gp376v/qwen25coder_32b_benchmarks_with_3xp40_and_3090/) separately report 28.38 tokens per second on one RTX 3090 at 275 W and 32.83 at 350 W, using Q4_K_M, a configured 32K context and Q8_0 KV caches. Those tests use different software, contexts and settings. Granite 4.2 30B generated about 25 tokens per second, below those dense-model results, and Muse Glimmer about 33, within their 28.38–38.14 range. Granite 4.2 8B and Qwen3.5 9B generated about 101, roughly 20% below neoX's 125.18 tokens per second for the 8B model at 128 generated tokens. Qwen3.8 27B generated about 52–56 tokens per second with LM Studio's default MTP on.

## What you can rebuild

Every table, figure and public-case view in the report rebuilds offline from the data in this repository. I computed the full-120 aggregate statistics in my private workspace and stored them with source hashes. The 18 public cases cover part of those totals. The 102 private tasks are not included, and rerunning the models gives different generations because sampling is nondeterministic.
