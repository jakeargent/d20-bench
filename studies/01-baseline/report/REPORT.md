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
