# Changelog

All notable changes to this actor will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

### Added
- BNM XML reference-rate fetcher.
- MAIB, MICB, Victoriabank HTML cash/card scrapers.
- Pydantic `Rate` model enforcing CONTEXT.md §4 invariants.
- Per-bank error isolation in the orchestrator.
- Apify input, output, and dataset schemas.
- Default input scrapes all four banks × five pairs × two rate types → ~27 records/run.
