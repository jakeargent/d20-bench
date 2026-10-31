# Which local AI answers rules questions correctly in 5 seconds?

*Baseline study of English SRD 5.2.1 rules questions, by Erol Can Akbaba.*

I gave 25 AI setups 120 questions about a game's rulebook, with and without the passage behind each question. The best setup went from 16/120 answers fully correct to 113/120 with the passage, almost three times faster. Two setups scored almost the same, 99.08 and 98.86 out of 100, yet one added a wrong rule in 2 answers and the other in 24. Three of the 25 gave a typical answer within 5 seconds and got more than half fully correct, and all three were Gemma 4, a model family from Google.

A rulebook works like a policy manual: clear rules, plenty of tricky cases, and answers you can check. If you are choosing an AI for that kind of work, this report shows which numbers reveal the risk, what the right documents add, and how much quality a faster answer costs. Look for four things.

- **Fully correct counts before average scores.** A *fully correct* answer meets every required claim and contains no *material error*, a wrong or invented rule the answer adds, which many people call a hallucination. The *claim score* sums the points earned for required claims, out of 100, with no deduction for errors, so a perfect score can still hide a wrong rule.
- **The median beside the p95.** The *median* is the middle completion time. The *p95* is the slower end of the distribution, where 1 request in 20 is slower. A low median cannot excuse a slow tail.
- **The gap with and without the passage.** *Oracle passages* are the rules passages the task authors used to write that question. The gap shows what feeding an AI the right text is worth.
- **The price of thinking.** With *thinking on*, a model works through the problem before it answers; with *thinking off*, it answers straight away. Thinking spends *tokens*, the word fragments a model reads and writes, and each one adds to the wait.

## The product question sets the speed target

This study looks at one job in interactive narrative systems such as game master agents and tabletop role-playing assistants: applying precise rules knowledge live, inside a conversation. I use the openly licensed rules of Dungeons & Dragons (SRD 5.2.1) as the test domain; the name d20 refers to the twenty-sided die the game rolls.

A player describes an action. The game master (GM) agent takes 30 seconds just to say “roll Persuasion,” and a live session has many such steps. My target is about 5 seconds per step. Usability research puts the limit for keeping a user's attention on a dialogue at about 10 seconds [1](#references). I set a 30-second hard cutoff because, in my judgment, a model that takes that long on a simple rules question even 1% of the time invites players to switch off.

## What was tested

I tested 15 models in 25 *configurations*, where a configuration is one model with one thinking setting and its run settings. Each answered the same 120 cases with and without oracle passages, for 6,000 answer records.

All models ran locally, on my own machine, on a single NVIDIA RTX 3090 graphics card (GPU) in October 2026. The card has 24 GB of *VRAM*, its own memory, which a model has to fit into. I ran each model in LM Studio with its defaults and each provider's recommended settings. VRAM usage was not tracked.

All results below cover the full 120 cases per configuration. The repository exposes 18 human-reviewed public cases and their 900 answer records. The other 102 cases remain private and contribute only aggregates. A few answers couldn't be graded as clearly right or wrong; those are left out, so some counts are out of fewer than 120.

Comparisons are grouped by *parameters*, the learned numbers that measure a model's size, into three *size classes* by total count: *small*, roughly 2.7–5.1B (billion); *medium*, 8.0–9.7B; *large*, 24–31B. *Dense* models use all their parameters for each token. *Mixture-of-experts* models use only the active experts alongside shared weights: Gemma 4 26B-A4B has about 25.8B total and 3.8B active parameters. The active count is what matters for speed [2](#references), [3](#references), provided the model fits in VRAM. Runtime and configuration differences remain confounds.

Completion time covers every recorded attempt and outcome, including retries, failures and capped outputs, and leaves out model loading and grading.

## Oracle passages improved every configuration

All 25 configurations had higher mean claim scores, lower median completion times and fewer output tokens with oracle passages. Gemma 4 26B-A4B with thinking on went from 16/120 fully correct at a 17.42-second median to 113/120 at 6.08 seconds. The lowest count with passages, 30/120, still beats the best count without them. This supports context injection, handing the model the text it needs, and fits the retrieval-augmented generation literature [4](#references).

<!-- figure: oracle-effect — paired no_source versus supplied_passage results, faceted by total-parameter size class; results.json configurations.id/size_class and cells.configuration/condition, quality.mean_claim_score, timing.median_seconds, output_tokens.mean -->

The public case [d20-en-pilot-t01-003](../../../data/cases.json) asks whether a willing character can fail a saving throw without rolling. Gemma 4 E2B with thinking off insisted on a roll without oracle passages and allowed voluntary failure with them. Its score rose from 0 to 100, while time fell from 1.76 to 0.70 seconds and output from 356 to 130 tokens.

On [d20-en-pilot-t11-006](../../../data/cases.json), Qwen3.5 4B with thinking off also rose from 0 to 100, dropping fabricated restrictions for *Knock* and *Arcane Lock*.

## Under the 5-second bar, Gemma 4 leads

With oracle passages, 10/25 configurations had a median at or below 5 seconds, but only three configurations met the 5-second median bar and got more than half the answers fully correct. All three were Gemma 4. Rows are sorted by fully correct answers, then by lower median time. Here, off/on mean thinking off/on; native marks models that cannot turn thinking off, and low marks reduced thinking effort.

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

Among the bold rows, Gemma 4 26B-A4B off had the most fully correct answers and the lowest mean output tokens, and its 4.56-second p95 also sat below the target. That combination is why I picked Gemma 4.

In the public answers, Gemma 4 26B-A4B generated about 130 tokens per second, compared with about 24–33 tokens per second for the dense roughly 30B models without speculative decoding on the same GPU. I see its smaller active workload as the main reason Gemma clears my 5-second bar with thinking off, alongside its short answers.

K2's 3.27-second median accompanies an 89.81-second p95, and it exceeded the 30-second cutoff in 8/120 requests.

## Thinking can buy quality, or consume the session

For Gemma 4 26B-A4B with oracle passages, thinking on increased fully correct answers from 96/120 to 113/120, the highest count in the study. Median time rose from 2.13 to 6.08 seconds, just past the target and p95 from 4.56 to 15.68 seconds.

<!-- figure: thinking-returns — paired off/on oracle results within model families, grouped by total-parameter size class; results.json configurations.id/model/mode/size_class and cells.configuration/condition, quality.fully_correct/profile_assessed/mean_claim_score, timing.median_seconds/p95_seconds, output_tokens.mean -->

With oracle passages, Qwen3.5 4B went from 51/120 to 90/120, but its median rose from 3.57 to 32.70 seconds, beyond the 30-second cutoff.

The public case [d20-en-pilot-t03-009](../../../data/cases.json), about damage after stabilization and run on Granite 4.2 30B without oracle passages, makes the cost concrete. Thinking on reduced the score from 20 to 10, increased time from 94 to 795 seconds, and output from 2,256 to 11,321 tokens. The longer answer invented rules; without grounding, thinking turned into excessive rumination, a pattern also reported for other reasoning models [5](#references).

On the spell-slot case [d20-en-pilot-t10-008](../../../data/cases.json), Qwen3.5 4B fell from 100 to 93 with thinking on, while time rose from 15 to 123 seconds.

For knowledge-heavy questions, the right evidence reliably improves accuracy, while extra thinking brings uneven gains [6](#references), [7](#references). The advantage of oracle passages in this study fits that pattern.

## A high average can conceal wrong rules

With oracle passages, Muse Glimmer with low thinking effort averaged 98.86 claim points, close to Gemma 4 26B-A4B thinking on at 99.08. Their fully correct counts were 96/120 and 113/120. Muse had material errors in 24/120 answers; Gemma had them in 2/120.

<!-- figure: scores-and-errors — oracle mean claim scores alongside fully-correct and material-error counts with separate assessed denominators, grouped by total-parameter size class; results.json configurations.id/size_class and supplied_passage cells.quality.mean_claim_score/fully_correct/profile_assessed/answers_with_material_errors/material_error_assessed -->

In [d20-en-pilot-t05-010](../../../data/cases.json), LFM2.5 2.6B with oracle passages correctly separated negotiating from reading body language and earned 100 claim points. It also invented an Intelligence-versus-Willpower check for Influence, so the answer has a material error and isn't fully correct.

## Inspect the evidence

The [study index](../README.md) links the offline comparison and public case explorer. The [aggregate results](../data/results.json) contain every condition; [public answer records](../data/answers.json) contain the five examples above. [Methods](../docs/METHODS.md), [Limitations](../docs/LIMITATIONS.md), the [data dictionary](../docs/DATA_DICTIONARY.md) and [provenance](../docs/PROVENANCE.md) give measurement definitions and the public/private boundary. The source rules retain their [SRD attribution](../../../THIRD_PARTY_NOTICES.md).

## Next: measure the gap from retrieval to oracle

A live system needs retrieval, software that finds the passages for the model. The next study, in progress, tests *BM25*, a standard keyword search that ranks passages by how well their words match the question, with Gemma 4 at several sizes.

[See what a study on your own AI would give you](https://erolcanakbaba.com/d20#what-you-get).

## References

1. Nielsen, J. [Response Times: The 3 Important Limits](https://www.nngroup.com/articles/response-times-3-important-limits/). Excerpt from *Usability Engineering*, chapter 5. Academic Press, 1993.
2. Fedus, W., Zoph, B. & Shazeer, N. [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961). JMLR, 2022.
3. Jiang, A. Q. et al. [Mixtral of Experts](https://arxiv.org/abs/2401.04088). 2024.
4. Lewis, P. et al. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). NeurIPS, 2020.
5. Chen, X. et al. [Do NOT Think That Much for 2+3=? On the Overthinking of o1-Like LLMs](https://arxiv.org/abs/2412.21187). 2024.
6. Trivedi, H., Balasubramanian, N., Khot, T. & Sabharwal, A. [Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions](https://aclanthology.org/2023.acl-long.557/). ACL, 2023.
7. Zhao, J. X., Hooi, B. & Ng, S.-K. [Test-Time Scaling in Reasoning Models Is Not Effective for Knowledge-Intensive Tasks Yet](https://arxiv.org/abs/2509.06861). COLM, 2026.
