# Which local model can keep a live interaction moving?

*Baseline study of English SRD 5.2.1 rules questions, by Erol Can Akbaba.*

With the source passages supplied, **only three configurations met the 5-second median bar and got more than half the answers fully correct. All three were Gemma 4.**

## The product question sets the speed target

This study looks at one job in interactive narrative systems such as game master agents and tabletop role-playing assistants: applying precise rules knowledge live, inside a conversation. I use the openly licensed rules of Dungeons & Dragons (SRD 5.2.1) as the test domain; the name d20 refers to the twenty-sided die the game rolls. For these systems, correct rulings and fast responses both matter: a wrong ruling misleads the players, and a slow one stalls the conversation.

A player describes an action. The game master (GM) agent takes 30 seconds just to say “roll Persuasion.” That delay is unusable in a live session, where play involves many such steps. My target is about 5 seconds per step on average, but quicker is better. Usability research puts the limit for keeping a user's attention on a dialogue at about 10 seconds [1](#references). I set the 30-second hard cutoff deliberately. In my judgment, a model that takes 30 seconds to settle a simple rules question even 1% of the time invites players to switch off, and one that routinely takes 30 seconds loses them for good.

For this reason, I picked Gemma 4. Every model answered each question twice: once on its own, and once with the *oracle passages*, the rules passages the task authors used to write that question. With oracle passages, Gemma 4 26B-A4B with thinking off had a 2.13-second median completion time. Thinking on reached the study's highest count of fully correct answers, 113/120, at a 6.08-second median, just beyond the intended live-use target. Across every tested configuration, oracle passages raised mean claim scores and reduced median time and mean output tokens. This makes the study a useful foundation for a retrieval series: it establishes what these configurations achieved with the oracle passages, and what a retrieval system must match or improve.

Quality and completion time therefore have to be read together. So do median and the 95th percentile (p95): the median describes a typical request, while p95 shows the slower end of the observed distribution. A low median cannot excuse a tail that repeatedly interrupts play.

## What was tested

The baseline contains 25 configurations and 6,000 answer records, from the same 120 cases answered with and without oracle passages.

All models ran locally on a single NVIDIA RTX 3090 (24 GB VRAM) in October 2026. I ran each one the way a typical user would, in LM Studio with its defaults and each provider's recommended settings, and with no tuning of the inference setup. VRAM usage was not tracked.

All aggregate results below cover the full 120-case suite per study configuration. The repository exposes 18 human-reviewed public cases and their 900 answer records. The other 102 cases remain private and contribute only aggregates.

The lead measure is **fully correct answers**: every required claim satisfied and no material error. A few answers couldn't be graded as clearly right or wrong; those are left out, so some counts are out of fewer than 120. Mean claim score is secondary. It sums the points earned for required claims, out of 100, with no deduction for errors. An answer can earn every claim point and still add a wrong rule, in which case it isn't fully correct.

Comparisons are grouped by total parameters: *small*, roughly 2.7–5.1B; *medium*, 8.0–9.7B; *large*, 24–31B. Mixture-of-experts models use only part of their weights for each token: Gemma 4 26B-A4B has about 25.8B total and 3.8B active parameters. The active parameter count is what matters for speed [2](#references), [3](#references), provided the model fits in VRAM. Runtime and configuration differences remain confounds.

Completion time includes recorded request attempts and retries, excluding model loading and grading. The tables use all outcomes, including failures and capped outputs. Output tokens are recorded totals per response; separate thinking-token counts are sometimes unknown. See [Methods](../docs/METHODS.md) for prompts, budgets and grading.

## Oracle passages improved every configuration

All 25 configurations had higher mean claim scores, lower median completion times and fewer mean and median output tokens with oracle passages provided to the model. The result supports context injection as a practical quality and efficiency intervention, which fits with the retrieval-augmented generation literature [4](#references).

<!-- figure: oracle-effect — paired no_source versus supplied_passage results, faceted by total-parameter size class; results.json configurations.id/size_class and cells.configuration/condition, quality.mean_claim_score, timing.median_seconds, output_tokens.mean -->

The public case [d20-en-pilot-t01-003](../../../data/cases.json) asks whether a willing character can fail a saving throw without rolling. Gemma 4 E2B with thinking off insisted on a roll without oracle passages. With the oracle passage, it correctly allowed voluntary failure. Its score rose from 0 to 100 and the answer became fully correct, while time fell from 1.76 to 0.70 seconds and output from 356 to 130 tokens.

In [d20-en-pilot-t11-006](../../../data/cases.json), Qwen3.5 4B, thinking off, fabricated restrictions for *Knock* and its interaction with *Arcane Lock*. With oracle passages, it correctly distinguished unlocking a lock from suppressing the magical lock and described the spell's loud sound; its score rose from 0 to 100, with a fully correct answer.

## Under the 5-second bar, Gemma 4 leads

With oracle passages, 10/25 configurations had a median at or below 5 seconds. Rows are sorted by fully correct answers, with lower median time breaking ties. Here, off/on mean thinking off/on; native marks models that cannot turn thinking off, and low marks reduced thinking effort.

| Size class | Configuration | Fully correct / assessed | Median s | p95 s | Mean output tokens |
|---|---|---:|---:|---:|---:|
| Large | Gemma 4 26B-A4B on | 113/120 | 6.08 | 15.68 | 892.6 |
| Large | Qwen3.8 27B on (low) | 102/119 | 11.28 | 22.27 | 709.6 |
| Medium | Qwen3.5 9B on | 99/120 | 26.66 | 77.80 | 3,577.9 |
| **Large** | **Gemma 4 26B-A4B off** | **96/120** | **2.13** | **4.56** | **255.3** |
| Large | Muse Glimmer low | 96/120 | 16.39 | 27.46 | 581.0 |
| Medium | Gemma 4 E4B on | 91/120 | 7.02 | 11.06 | 801.7 |
| Large | Qwen3.8 27B off | 90/120 | 7.71 | 14.14 | 456.8 |
| Small | Qwen3.5 4B on | 90/120 | 32.70 | 94.70 | 5,193.2 |
| Large | GLM-4.7 Flash on | 82/120 | 13.77 | 44.25 | 2,061.9 |
| **Medium** | **Gemma 4 E4B off** | **78/119** | **3.99** | **8.77** | **383.7** |
| **Small** | **Gemma 4 E2B on** | **76/120** | **3.86** | **6.57** | **837.2** |
| Small | Granite 4.2 3B on | 76/119 | 8.51 | 45.17 | 2,508.2 |
| Large | LFM2.5-24B-A2B native | 73/119 | 10.76 | 29.95 | 2,868.5 |
| Large | Granite 4.2 30B on | 69/119 | 52.04 | 97.29 | 1,493.3 |
| Medium | Granite 4.2 8B off | 63/120 | 9.41 | 46.69 | 1,685.1 |
| Medium | Granite 4.2 8B on | 63/117 | 18.47 | 97.16 | 2,971.9 |
| Large | Granite 4.2 30B off | 62/115 | 27.07 | 72.33 | 825.6 |
| **Small** | **Gemma 4 E2B off** | **58/120** | **1.76** | **4.36** | **380.0** |
| **Small** | **Qwen3.5 4B off** | **51/120** | **3.57** | **16.17** | **986.5** |
| **Medium** | **Qwen3.5 9B off** | **49/116** | **4.86** | **19.40** | **749.7** |
| Small | Granite 4.2 3B off | 49/119 | 6.87 | 37.39 | 1,832.6 |
| **Small** | **K2 Horizon 3.7B low** | **33/119** | **3.27** | **89.81** | **2,106.6** |
| **Medium** | **LFM2.5-8B-A1B native** | **32/120** | **4.07** | **14.34** | **1,729.9** |
| **Small** | **LFM2.5 2.6B native** | **32/120** | **4.99** | **21.39** | **1,734.0** |
| **Large** | **GLM-4.7 Flash off** | **30/120** | **3.11** | **6.07** | **356.2** |

Bold rows: median at or below 5 seconds.

<!-- figure: live-use-tradeoffs — oracle fully-correct counts and assessed denominators against median completion time, with p95 and mean output tokens visible; results.json configurations.id/size_class and supplied_passage cells.quality.fully_correct/profile_assessed, timing.median_seconds/p95_seconds/above_30_seconds, output_tokens.mean; my reference lines at 5 and 30 seconds -->

I picked Gemma 4 because of the combination of fully correct answers, short times and few output tokens. Among the configurations with a median at or below 5 seconds, Gemma 4 26B-A4B off had the most fully correct answers and the lowest mean output tokens. Its p95 was also below the target. That is a stronger live-use result than passing the median filter alone: on consumer-grade hardware, even its slower responses stay within the target.

Dense models read all their weights for each generated token; mixture-of-experts models read only the active experts alongside shared weights [2](#references), [3](#references). In the public answers, Gemma 4 26B-A4B, with 3.8B active parameters, generated about 130 tokens per second, compared with about 24–33 tokens per second for the dense roughly 30B models without speculative decoding on the same GPU. I see this smaller active workload as the main reason Gemma clears my 5-second bar with thinking off, alongside its short answers.

K2 shows why the tail matters: its 3.27-second median accompanies an 89.81-second p95. It exceeded the 30-second cutoff in 8/120 requests.

## Thinking can buy quality, or consume the session

For Gemma 4 26B-A4B with oracle passages, thinking on is a clear quality gain: it increased fully correct answers from 96/120 to 113/120. Median time rose from 2.13 to 6.08 seconds, p95 from 4.56 to 15.68 seconds, and mean output tokens from 255.3 to 892.6. The highest fully correct count in the study therefore misses the median target, and the gain has to be weighed against the wait.

<!-- figure: thinking-returns — paired off/on oracle results within model families, grouped by total-parameter size class; results.json configurations.id/model/mode/size_class and cells.configuration/condition, quality.fully_correct/profile_assessed/mean_claim_score, timing.median_seconds/p95_seconds, output_tokens.mean -->

Granite 4.2 30B gained much less: with oracle passages, fully correct counts went from 62/115 (thinking off) to 69/119 (thinking on), while median time rose from 27.07 to 52.04 seconds. Neither mode approaches the live-use target.

The public case [d20-en-pilot-t03-009](../../../data/cases.json), about damage after stabilization and run without oracle passages, makes the cost concrete. Thinking on reduced the score from 20 to 10, increased time from 94 to 795 seconds, and increased output from 2,256 to 11,321 tokens. The longer answer invented rules, including negative hit points; without grounding, thinking turned into excessive rumination, a pattern also reported for other reasoning models [5](#references).

Qwen3.5 4B illustrates both sides. With oracle passages, thinking increased fully correct answers from 51/120 to 90/120, but median time rose from 3.57 to 32.70 seconds, beyond the 30-second cutoff. On the public spell-slot case [d20-en-pilot-t10-008](../../../data/cases.json), the score fell from 100 with thinking off to 93 with thinking on, time rose from 15 to 123 seconds, and output from 2,080 to 15,656 tokens. Both answers had a material error. The thinking off answer met every required claim while also asserting a false blanket prohibition after Bonus Action spellcasting.

Thinking is a less reliable route to quality than supplying oracle passages, and it also changes output budgets and runtime. For knowledge-heavy questions, the right evidence reliably improves accuracy, while extra thinking brings uneven gains [6](#references), [7](#references). The advantage of oracle passages in this study fits that pattern.

## A high average can conceal wrong rules

With oracle passages, Muse Glimmer with low thinking effort averaged 98.86 claim points, close to Gemma 4 26B-A4B thinking on at 99.08. Their fully correct counts were 96/120 and 113/120 respectively. Muse had material errors in 24/120 answers; Gemma had them in 2/120. Those similar averages describe different risks for a workflow that will act on the explanation.

<!-- figure: scores-and-errors — oracle mean claim scores alongside fully-correct and material-error counts with separate assessed denominators, grouped by total-parameter size class; results.json configurations.id/size_class and supplied_passage cells.quality.mean_claim_score/fully_correct/profile_assessed/answers_with_material_errors/material_error_assessed -->

In [d20-en-pilot-t05-010](../../../data/cases.json), LFM2.5 2.6B with oracle passages correctly separated negotiating from reading body language. It earned 100 claim points. It also invented an Intelligence-versus-Willpower check for Influence and extended the restriction on simultaneous actions to the whole turn. The answer is not fully correct and has a material error.

That distinction matters in an interactive loop: the system can choose the right action while teaching or enforcing a wrong rule. Claim score measures required content; fully correct also checks whether the answer added material errors.

## Inspect the evidence

Start with the [study index](../README.md) for the offline comparison and public case explorer. The [aggregate results](../data/results.json) contain every condition; [public answer records](../data/answers.json) contain the five examples above, their scores, request timings and tokens.

Read [Methods](../docs/METHODS.md), [Limitations](../docs/LIMITATIONS.md), the [data dictionary](../docs/DATA_DICTIONARY.md) and [provenance](../docs/PROVENANCE.md) for measurement definitions and the public/private boundary. The source rules retain their [SRD attribution](../../../THIRD_PARTY_NOTICES.md).

## Next: measure the gap from retrieval to oracle

The next study is in progress: BM25 retrieval variants with Gemma 4 at several sizes.

## References

1. Nielsen, J. [Response Times: The 3 Important Limits](https://www.nngroup.com/articles/response-times-3-important-limits/). Excerpt from *Usability Engineering*, chapter 5. Academic Press, 1993.
2. Fedus, W., Zoph, B. & Shazeer, N. [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961). JMLR, 2022.
3. Jiang, A. Q. et al. [Mixtral of Experts](https://arxiv.org/abs/2401.04088). 2024.
4. Lewis, P. et al. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). NeurIPS, 2020.
5. Chen, X. et al. [Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs](https://arxiv.org/abs/2412.21187). 2024.
6. Trivedi, H., Balasubramanian, N., Khot, T. & Sabharwal, A. [Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions](https://aclanthology.org/2023.acl-long.557/). ACL, 2023.
7. Zhao, J. X., Hooi, B. & Ng, S.-K. [Test-Time Scaling in Reasoning Models Is Not Effective for Knowledge-Intensive Tasks Yet](https://arxiv.org/abs/2509.06861). COLM, 2026.

<!--
NUMERIC AUDIT
Paths are relative to studies/01-baseline/. R = data/results.json; A =
data/answers.json. Repeated numbers use the same sources below. Model names,
version strings, case IDs and study/path labels are identifiers, not additional
measurements: configuration names/IDs are R.configurations[].model/id; SRD
5.2.1 appears in A.answers[].candidate_request; case IDs are A.answers[].case_id.
No statistic here is recomputed from the public subset except its case count.
Displayed times and scores use nearest decimal rounding; integer case times
use nearest whole second; table tokens use one decimal. B means 1e9 parameters.

Author framing (not empirical observations): about 5 seconds per step is the
live-use target; 30 seconds is the generous hard cutoff and the illustrative
player wait. R.cells[].timing.above_30_seconds supplies observed exceedances.
The one-AI-review method is described in docs/METHODS.md, with historical pilot
exceptions; it is not an aggregate measurement. p95 denotes the 95th percentile;
its definition and nearest-rank convention are in docs/METHODS.md.

Scope: 25 = len(R.configurations); 50 = len(R.cells); 6,000 = R.selected_records;
120 = R.suite_questions and every cells[].records; 900 = R.public_answer_records
and len(A.answers); 18 = len(unique A.answers[].case_id); 102 = 120 minus 18.
100-point scale = sum(required-claim maximum awards), confirmed by public
100-point A.answers[].score.earned_points and documented in docs/METHODS.md.
The five public examples = five distinct case IDs in the answer audit below.
No random audit / unmeasured grader accuracy = R.random_human_audit/grader_accuracy.

Size ranges: R.configurations[].total_parameters, grouped by size_class:
small min 2697198592, max 5123178051 -> 2.7–5.1B;
medium min 7996156490, max 9653104368 -> 8.0–9.7B;
large min 23971585280, max 31221488576 -> roughly 24–31B.
gemma4-e4b/off: total_parameters 7996156490 -> 8.0B;
effective_parameters 4500000000 -> 4.5B.
gemma4-26b-a4b/off: total_parameters 25805936206 -> 25.8B;
active_parameters 3800000000 -> 3.8B.

Oracle improvements: join R.cells by configuration and compare supplied_passage
against no_source. Count strictly higher quality.mean_claim_score = 25/25;
strictly lower timing.median_seconds = 25/25; strictly lower output_tokens.mean
= 25/25; strictly lower output_tokens.median = 25/25.
10/25 = count(supplied_passage timing.median_seconds <= author threshold 5)
divided by len(R.configurations).
Headline: among those 10 cells, exactly three have quality.fully_correct > 60
(more than half of the 120-case suite): gemma4-26b-a4b/off 96/120 at 2.13 s,
gemma4-e4b/off 78/119 at 3.99 s, gemma4-e2b/on 76/120 at 3.86 s.
No other supplied_passage cell with timing.median_seconds <= 5 exceeds 60.
The table includes all 25 supplied_passage cells, sorted by fully_correct
descending, then median_seconds ascending; all six cells of each row are bold
if and only if timing.median_seconds <= 5. Size classes come from the joined
R.configurations[].size_class.
Hardware/runtime: author-supplied provenance, not aggregate measurements:
all models ran locally on one NVIDIA RTX 3090 (24 GB VRAM), using LM Studio,
in October 2026. VRAM usage was not tracked; exact runtime builds and GPU
placement remain incompletely pinned.

Oracle table and repeated narrative values: R.cells selected by configuration
below and condition=supplied_passage. Columns in this audit are
quality.fully_correct / quality.profile_assessed; timing.median_seconds;
timing.p95_seconds; output_tokens.mean. Displayed rounding:
gemma4-26b-a4b/on: 113/120; 6.08; 15.68; 892.6
qwen3.8-27b/on: 102/119; 11.28; 22.27; 709.6
qwen3.5-9b/on: 99/120; 26.66; 77.80; 3577.9
gemma4-26b-a4b/off: 96/120; 2.13; 4.56; 255.3
muse-glimmer/low: 96/120; 16.39; 27.46; 581.0
gemma4-e4b/on: 91/120; 7.02; 11.06; 801.7
qwen3.8-27b/off: 90/120; 7.71; 14.14; 456.8
qwen3.5-4b/on: 90/120; 32.70; 94.70; 5193.2
glm4.7-flash/on: 82/120; 13.77; 44.25; 2061.9
gemma4-e4b/off: 78/119; 3.99; 8.77; 383.7
gemma4-e2b/on: 76/120; 3.86; 6.57; 837.2
granite4.2-3b/on: 76/119; 8.51; 45.17; 2508.2
lfm2.5-24b-a2b/native: 73/119; 10.76; 29.95; 2868.5
granite4.2-30b/on: 69/119; 52.04; 97.29; 1493.3
granite4.2-8b/off: 63/120; 9.41; 46.69; 1685.1
granite4.2-8b/on: 63/117; 18.47; 97.16; 2971.9
granite4.2-30b/off: 62/115; 27.07; 72.33; 825.6
gemma4-e2b/off: 58/120; 1.76; 4.36; 380.0
qwen3.5-4b/off: 51/120; 3.57; 16.17; 986.5
qwen3.5-9b/off: 49/116; 4.86; 19.40; 749.7
granite4.2-3b/off: 49/119; 6.87; 37.39; 1832.6
k2-horizon-3.7b/low: 33/119; 3.27; 89.81; 2106.6
lfm2.5-8b-a1b/native: 32/120; 4.07; 14.34; 1729.9
lfm2.5-2.6b/native: 32/120; 4.99; 21.39; 1734.0
glm4.7-flash/off: 30/120; 3.11; 6.07; 356.2
All these cells have timing.recorded_cases=120 and output_tokens.count=120.
k2-horizon-3.7b/low: timing.above_30_seconds=8 / timing.recorded_cases=120.

Additional supplied_passage aggregates, same fields unless specified:
gemma4-26b-a4b/on: 113/120; 6.08; 15.68; 892.6;
quality.mean_claim_score=99.075 -> 99.08;
quality.answers_with_material_errors/material_error_assessed=2/120.
113 is max(R.cells[].quality.fully_correct) across both conditions.
granite4.2-30b/off: fully_correct/profile_assessed=62/115;
timing.median_seconds=27.07 (rounded).
granite4.2-30b/on: fully_correct/profile_assessed=69/119;
timing.median_seconds=52.04 (rounded).
qwen3.5-4b/on: fully_correct/profile_assessed=90/120;
timing.median_seconds=32.70 (rounded).
muse-glimmer/low: quality.mean_claim_score=98.85833333333333 -> 98.86;
quality.fully_correct/profile_assessed=96/120;
quality.answers_with_material_errors/material_error_assessed=24/120.

Public answer audit: select A.answers by (configuration, case_id, condition).
Fields: score.earned_points; score.complete_task_success (F); score.has_material_error
(E); request_timing.total_attempt_seconds; operations.total_output_tokens.
gemma4-e2b/off, d20-en-pilot-t01-003:
no_source: 0; F=false; E=true; 1.76267917198129 -> 1.76; 356.
supplied_passage: 100; F=true; E=false; 0.7039401099900715 -> 0.70; 130.
qwen3.5-4b/off, d20-en-pilot-t11-006:
no_source: 0; F=false; E=true.
supplied_passage: 100; F=true; E=false.
lfm2.5-2.6b/native, d20-en-pilot-t05-010, supplied_passage:
100; F=false; E=true.
granite4.2-30b/off, d20-en-pilot-t03-009, no_source:
20; F=false; E=true; 93.69579367700499 -> 94; 2256.
granite4.2-30b/on, d20-en-pilot-t03-009, no_source:
10; F=false; E=true; 794.8344104519929 -> 795; 11321.
qwen3.5-4b/off, d20-en-pilot-t10-008, supplied_passage:
100; F=false; E=true; 15.117679689006764 -> 15; 2080.
qwen3.5-4b/on, d20-en-pilot-t10-008, supplied_passage:
93; F=false; E=true; 122.68982181999309 -> 123; 15656.
granite4.2-3b/off, d20-en-pilot-t09-003, supplied_passage:
100; F=true; E=false; 2.167420300989761 -> 2.17; 351.
Public rule paraphrases are backed by these records' candidate_answer and
expert_annotation; accepted score profiles above govern the report's judgments.
Generation-speed audit: built speed.csv / speed.json, 18 public cases only,
both passage conditions pooled. Single-attempt answers with >=100 output tokens;
operations.total_output_tokens / (request_timing.selected_request_seconds minus
request_timing.first_token_seconds where recorded). Columns: configuration; n;
median tokens/second (rounded to 2 decimals).
lfm2.5-2.6b/native; 36; 242.43
granite4.2-3b/off; 36; 166.28
granite4.2-3b/on; 36; 165.49
qwen3.5-4b/off; 36; 133.57
qwen3.5-4b/on; 36; 134.45
k2-horizon-3.7b/low; 30; 89.63
gemma4-e2b/off; 36; 205.44
gemma4-e2b/on; 36; 205.71
gemma4-e4b/off; 36; 112.62
gemma4-e4b/on; 36; 133.61
lfm2.5-8b-a1b/native; 36; 307.50
granite4.2-8b/off; 36; 101.34
granite4.2-8b/on; 36; 101.02
qwen3.5-9b/off; 36; 101.01
qwen3.5-9b/on; 36; 101.72
lfm2.5-24b-a2b/native; 36; 215.72
gemma4-26b-a4b/off; 35; 128.81
gemma4-26b-a4b/on; 36; 128.53
qwen3.8-27b/off; 36; 52.17
qwen3.8-27b/on; 36; 55.99
granite4.2-30b/off; 36; 25.26
granite4.2-30b/on; 36; 24.37
muse-glimmer/low; 36; 33.36
glm4.7-flash/off; 36; 113.15
glm4.7-flash/on; 34; 115.98
-->
