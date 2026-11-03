# SIXRX ten-year benchmark for the saved Gränges analysis

Researched 3 November 2026. Analysis date: **1 November 2026**.

## Verdict

**A transparent public benchmark is available: approximately 11.61% a year.** This is calculated from the exact SIX Return Index series, with gross dividends reinvested, using public SIX-sourced levels rounded to two decimals. It is historical market return, not a forecast. This research does not change a valuation or adopt a hurdle automatically.

## Exact series and sources

SIX identifies **SIX Return Index (SIXRX)** as a SEK gross index that reinvests the full dividend. It represents Nasdaq Stockholm companies weighted by total market capitalization; it is distinct from the capped SIXPRX and the price-only SIXGX. The downloaded current methodology is **version 1.60, 8 October 2026, section 5.4, pages 12–13**. [Official SIX Nordic methodology](https://www.six-group.com/dam/download/market-data/indices/nordics/rules-regulations/methodology-rulebook-governing-nordic-equity-indices.pdf).

The official benchmark statement gives **ISIN SE0002211029**, currency SEK and dividend-reinvested return type in Appendix I, page 7. [SIXRX benchmark statement](https://www.six-group.com/dam/download/market-data/indices/nordics/benchmark/benchmark-statement-sixrx.pdf).

The level publisher is **Fondbolagens förening**, rather than SIX's own downloadable history service. Its official market-index page states that data comes from SIX Financial Information, using weekday prices set at 17:30 CET. Its normal public date form accepts `startDate` and `endDate`. [Publisher's source/convention statement](https://fondbolagen.se/en/Facts_Indices/indices/).

## Window and calculation

Use the saved analysis date as the calendar anchor. Subtract ten calendar years for the start anchor; use the last trading close on or before each anchor. **1 November 2026 was Sunday**, so the end observation is Friday **30 October 2026**. The start anchor, **1 November 2016**, has a published observation. Do not first shift the end anchor to Friday and then subtract ten years: that would select a different starting window.

| Observation | SIXRX level |
|---|---:|
| 1 November 2016 | 946.95 |
| 30 October 2026 | 2,839.70 |

The public date table also reports a period return of **199.88%**. These are index levels from the same publisher and scale, not a fund proxy or an adjusted share-price series. [Exact selected period](https://fondbolagen.se/fakta_index/marknadsindex/six-index/sixrx/?startDate=2016-11-01&endDate=2026-10-30).

The effective observations are **3,650 days** apart. Using ACT/365 annualization gives exactly ten years for these particular endpoints:

```text
Total return = 2839.70 / 946.95 - 1
             = 199.8785575%

Annualized return = (2839.70 / 946.95)^(365 / 3650) - 1
                  = 11.6077984% per year
Display: 11.61% per year
```

This annualization is our explicit calculation convention; the publisher supplies period return, not an annualized ten-year figure. Python `Decimal` with 40-digit precision produced the result. The arithmetic precision does not increase the precision of the two-decimal source levels. Do not add dividend yield again to this total-return benchmark.

## Preserved evidence and limits

Final snapshot: `data/benchmarks/sixrx/20261103T121617260724Z/`. It contains five exact raw public responses, `manifest.json`, `context.json` with the inputs/conventions and manifest hash, and a small `calculation.py` that reproduces the result. All referenced hashes were checked. The snapshot is ignored local data; the normal research archive must carry it between workstations.

The packet input is that snapshot's `context.json`. Schema version 1 includes the benchmark identity, `analysis_date`, `start_anchor_date`, dated `start_observation`/`end_observation` with Decimal-string levels, a `calculation` object with elapsed days/years, ACT/365 convention, exact formula and Decimal-string returns, `rounded_source: true`, source sections and caveats. Its manifest is a relative path with `manifest_sha256`. Manifest `sources` have `id`, `url`, relative `file`, `sha256`, byte count, HTTP status, retrieval time and available document/HTTP/observation dates. The diagnostic history redirect is labeled separately from the level source.

The chosen levels precede the analysis date, but the source was retrieved on 3 November. This retrospective snapshot does not prove precisely what file was publicly available on 1 November. It does preserve the evidence used now.

The former official SIX history PDF URL returned **HTTP 301 to Index Data Center**, rather than historical PDF bytes, during this investigation. Cached search excerpts from that old PDF were not used for an endpoint. [Former history URL](https://www.six-group.com/dam/download/financial-information/indices/times-series/sixrx-timeseries.pdf). More precise administrator levels or a licensed feed were not obtained; neither is necessary to reproduce the rounded result above.

The saved Börsdata `instruments` catalogue (`data/borsdata/context/426/20261101T173056Z/instruments.json`, 1,706 instruments) contains Nasdaq index entries but no SIXRX/SIX Return name or ticker match. This bounded search does not prove that every Börsdata product lacks SIXRX. No authenticated request or substitute benchmark was needed.

**Recommendation:** use **11.61%** as the displayed historical SIXRX comparator for this saved analysis, retaining its exact window, gross-dividend convention, rounded-source status and raw provenance. Investor B, OMXS30 GI and fund proxies were not substituted. A separate decision must determine how a historical market comparator informs required future investment return.
