# How to read the results

The comparison table has 50 rows: every configuration, with and without oracle passages. Each row covers all 120 cases. The case explorer shows the 18 public cases.

Read three measures separately: fully correct answers, claim score and material errors. A high claim score can sit next to an extra wrong rule. Read each count with its denominator: a few answers couldn't be graded as clearly right or wrong; those are left out, so some counts are out of fewer than 120. For time, compare the median with the quartiles, the p95, the maximum and the number of requests over 30 seconds. The p95 is the slower end of the distribution, where 1 request in 20 is slower, and a fast mean can hide it.

The table supports three comparisons: thinking off against thinking on within one model family, the effect of oracle passages, and smaller against larger checkpoints where both exist. Provider settings, output budgets and version changes differ between configurations, which limits what the comparisons say about cause. The tables and the latency figure group configurations by total-parameter size class.

The 18 public cases got a human quality review. The detailed examples let you read individual answers and see how they were graded.
