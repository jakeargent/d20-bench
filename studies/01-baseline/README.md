# Study 1: baseline

Study 1 is the baseline of the d20 Bench series. I tested 25 local model configurations on 120 English questions about the D&D SRD 5.2.1 rules. For every answer I measured quality, tokens generated and completion time. The results are exploratory.

Each configuration answered the same 120 questions twice: without oracle passages and with them. Oracle passages are the SRD passages the task authors used to write each question. That gives 6,000 answer records and 50 combinations of configuration and passage condition, grouped by total-parameter size class.

I am publishing 18 of the 120 cases, with their 900 detailed answer records. A human reviewed those 18 cases. The other 102 cases stay private, and they count only in the aggregate numbers.

## Start here

- [The report](report/REPORT.md): what I found, and why I use a 5-second target.
- [Explore the data](web/explore.html): the comparison table for all 50 combinations, and the 18 public cases with their answers.
- [Methods](docs/METHODS.md): how I ran and graded the study.
- [Limitations](docs/LIMITATIONS.md): what limits how far the comparisons go.
- [Results guide](docs/RESULTS.md): how to read the comparisons.
- [Data dictionary](docs/DATA_DICTIONARY.md): every public file and field.
- [Provenance](docs/PROVENANCE.md): where the data comes from, and what I left out.
- [Disclosure boundary](../../SECURITY.md) and [SRD attribution](../../THIRD_PARTY_NOTICES.md).

## About this repository

This repository holds the 18 public cases, the aggregate results, the site build and the documentation. The private task set, raw private answers, credentials and model weights are not included.

## Rebuild the site

Run these commands from the repository root. They need Python 3.13.9 and `uv`. There are no third-party Python dependencies, and a normal build runs offline.

```bash
uv run python scripts/publication.py validate
uv run python -m unittest discover -s tests -v
uv run python scripts/publication.py build
uv run python scripts/publication.py package
```

To view the site locally, run the loopback-only preview and open `http://127.0.0.1:8000/`:

```bash
make preview
```

The explorer loads its data over HTTP, so open the site through the preview server. The full JSON files are also available for download.

The build produces the report page and the data explorer, CSV and Markdown tables, a standalone latency SVG, the public JSON downloads, SHA-256 build manifests and a local release archive. The generated `site/` and `dist/` directories are ignored by Git.
