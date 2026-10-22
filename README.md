# d20 Bench

Exploratory English SRD 5.2.1 studies, published incrementally.

- [Study 1: baseline](studies/01-baseline/README.md) — completed; 25 configurations, 50 combinations of configuration and passage condition, 6,000 answer records, 18 public cases and 900 public answer records.
- Study 2: BM25 context injection with Gemma 4 — in progress.

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
