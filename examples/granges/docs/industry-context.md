# Gränges industry context and peer candidates

Historical source inspection on 3 November 2026. Generic loader behavior is documented in [the shared guide](../../../docs/industry-context.md).

## Inspected Global workbooks, 3 November 2026

The real snapshot `data/benchmarks/damodaran/20261103T120604422959Z/` selected the exact `Metals & Mining` row in each workbook. Each reports 1,874 firms; that does not establish the same usable sample for every metric. All raw hashes and the context's manifest reference were verified after acquisition.

| Workbook | Internal `Date updated:` | Header / selected Excel row | HTTP Last-Modified |
|---|---|---|---|
| `marginGlobal.xls` | 5 January 2026 | 9 / 61 | 8 January 2026 |
| `wcdataGlobal.xls` | 5 January 2026 | 8 / 60 | 8 January 2026 |
| `EVAGlobal.xls` | **5 January 2025** | 19 / 71 | 8 January 2026 |
| `capexGlobal.xls` | 5 January 2026 | 8 / 60 | 8 January 2026 |

**The EVA/ROC date discrepancy is unresolved.** Its internal label may be stale, or the underlying figures may be older; these files alone do not establish which. The loader preserves the label and flags the different modification year in dataset caveats. It does not silently replace 2025 with the catalogue's 2026 update year. Do not describe this ROC figure as a verified January 2026 or current peer benchmark.

All four contain a `Variables & FAQ` sheet. This source distinguishes aggregate ratios, effective-tax ROC, capitalized R&D and cash-only acquisitions. Its capital expenditure/acquisition measures do not establish maintenance capex or include all share-funded acquisitions. The preserved source rows include other original columns, including WACC/beta and EBITDA variants; retention provides source fidelity and does not adopt those columns as valuation inputs. The optional EV/EBIT file was not fetched for this first snapshot.

## Gränges candidate comparisons

[Candidate peers](../peers.json) records a short human-reviewed candidate list with official sources beside each observation. It contains no peer financial values or derived multiples.

- **Constellium SE (NYSE: CSTM):** rolled products and recycling with packaging and automotive overlap; aerospace and structural extrusions require product/segment matching. [Business units](https://www.constellium.com/our-business-units), [current issuer identification](https://www.constellium.com/news/constellium-reports-strong-third-quarter-2026-results-raises-full-year-2026-guidance).
- **UACJ Corporation (Tokyo: 5741):** rolling includes automotive heat exchanger and fin materials, with broader foil, extrusion and other businesses. Match metal-price lag, profit adjustments and ROIC basis before comparing margins/returns. [Business](https://www.uacj.co.jp/english/company/business/), [listing](https://www.uacj.co.jp/english/ir/stockinfo/stock.html), [profit/ROIC definitions](https://www.uacj.co.jp/english/sustainability/message.html).
- **Kaiser Aluminum (Nasdaq: KALU):** fabrication and rolling serve packaging, automotive, aerospace and engineering; conversion revenue excludes hedged metal cost and cannot be compared directly with reported sales. [Business](https://investors.kaiseraluminum.com/), [listing](https://investors.kaiseraluminum.com/resources/faq), [Metal Pricing Policies](https://investors.kaiseraluminum.com/sec-filings/all-sec-filings/content/0001193125-26-059575/kalu-20251231.htm).
- **Novelis:** rolling/recycling operating reference only. It is a wholly owned Hindalco subsidiary; a parent equity multiple does not provide a standalone Novelis multiple. [Business](https://novelis.com/about-us/), [ownership](https://www.hindalco.com/businesses/novelis).

The reasons for review are product/customer overlap, conversion pricing and metal pass-through, rolling/recycling capital intensity and reinvestment. These are candidate comparisons, not demonstrated equivalence. Harmonized peer financial history, cash flow, maintenance investment and market multiples remain future evidence work; no EDGAR integration or full peer acquisition was added.
