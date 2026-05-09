# Changelog

All notable changes to this actor will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-09

Public release on Apify Store: <https://apify.com/blameless_rumor/moldova-bank-rates>.

### Added
- BNM XML reference-rate fetcher.
- MAIB, MICB, Victoriabank HTML cash/card scrapers.
- Pydantic `Rate` model enforcing CONTEXT.md §4 invariants.
- Per-bank error isolation in the orchestrator.
- Apify input, output, and dataset schemas.
- Default input scrapes all four banks × five pairs × two rate types → ~27 records/run.
- Pay-per-event monetization, $0.01 / 1000 results (deviation from CONTEXT.md $0.50/1000 — see `docs/operations.md`).
- 6h schedule (cron `0 */6 * * *` UTC) with email failure alerts.
- GitHub source linked to https://github.com/PixelPerfector/apify (auto-buildable).
