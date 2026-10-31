# d20 Bench

Same score, twelve times the mistakes. I tested 25 AI setups on 120 questions about a game's rulebook, the English SRD 5.2.1 rules of Dungeons & Dragons. Two scored almost the same, 99.08 and 98.86 out of 100, yet one invented a wrong rule in 2 answers and the other in 24.

These exploratory studies show which AI to trust with rules-heavy work, how fast it answers and where it goes wrong. A rulebook works like a policy manual: clear rules, plenty of tricky cases, and answers you can check.

- [Study 1: baseline](studies/01-baseline/README.md): completed. 25 configurations (one model with one thinking setting), 50 combinations of configuration and passage condition, 6,000 answer records, 18 public cases and 900 public answer records.
- Study 2, BM25 keyword search with Gemma 4: in progress, no results yet.

Both studies use the same 120 cases and the same 18-case public boundary.

[Disclosure boundary](SECURITY.md) · [SRD attribution](THIRD_PARTY_NOTICES.md)

## Local viewing

Run `make preview` from the repository root, then visit
`http://127.0.0.1:8000/`. Each study has a report page and an **Explore the data** page. The explorer
fetches local JSON files, so open it through the preview server.

## License

Copyright © 2026 Erol Can Akbaba. Source code in `scripts/`, `tests/`, `web/`,
study web templates and build configuration is licensed under [MIT](LICENSE).
Data, cases, documentation and reports are licensed under
[Creative Commons Attribution 4.0 International](LICENSE-CC-BY-4.0.md).
Attribute Erol Can Akbaba and link to this repository or use its
[citation metadata](CITATION.cff).

SRD 5.2.1 content retains its own CC BY 4.0 attribution; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
