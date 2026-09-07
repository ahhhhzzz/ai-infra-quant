# TASK-007C third-party use manifest

Status: implementation evidence; pending independent review.

| Source | Exact reference | Actual use | Local destination / license |
|---|---|---|---|
| `555cute/r20-quantum-trader` | `3840ef1af57c929c081fbe45087225cca1b508f1` | Design reference only: focused watchlist / chart / analysis workbench, card grouping, dark/light hierarchy. Pinned README product overview inspected. No source, image, icon, font, strategy threshold, executable integration or asset copied. | Original owned HTML/CSS/JS. No copied R20 material requiring an additional MIT notice. |
| TradingView Lightweight Charts | Existing accepted `5.2.1` vendor | Existing local chart library reused for a second, isolated frozen chart and volume pane. No vendor-byte change. | `src/ai_infra_quant/frontend/static/vendor/lightweight-charts.standalone.production.js`; Apache-2.0 license and TradingView copyright notice retained in adjacent `LIGHTWEIGHT_CHARTS_LICENSE.txt` / `LIGHTWEIGHT_CHARTS_NOTICE.txt`. Visible attribution and TradingView link retained. |
| Playwright Python | `1.55.0`, pinned dev extra only | Runs real browser acceptance against the existing Uvicorn entrypoint. No production/browser runtime dependency or source copied into the product. | `pyproject.toml` dev extra; Apache-2.0 package. Browser installation is external to the repository. |

Chart normalized-LF SHA-256 remains
`e21cc5caa0226ef30bd8549c50b9ef926615f2a4ee6b4e486353477a55f598cf`.
Its existing attribution regression also checks the served bytes and both notices. No new chart,
icon, font, media, CDN, telemetry or remote UI asset dependency is introduced. Screenshots are
generated locally from the owned application with clearly identified synthetic test responses.

No R20 account, execution, CLI/OAuth, scheduler, model-output-to-shell, arbitrary plugin, strategy
editing, synthetic production market fallback or secret backup behavior was adopted.
