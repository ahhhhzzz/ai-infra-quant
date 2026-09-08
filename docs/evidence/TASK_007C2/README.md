# TASK-007C2 synthetic browser evidence

All PNGs are unedited real Chromium screenshots of the actual local Uvicorn workbench.
Market facts, model description stress text, Chinese errors, credential operations and history
are synthetic intercepted fixtures. No private key, real provider response, user data or database
is included. Password fields are empty in screenshots. Browser viewport sizes below differ from
PNG height because captures use `full_page=True`; the native dialog remains centered in the viewport.

| Scenario | Images | Checks |
|---|---|---|
| 1440 x 900, dark/light, open dialog | [dark](modal-1440x900-dark.png), [light](modal-1440x900-light.png) | Long unbroken service description and Chinese failure text, single column, full-width input, non-overlap and reachable actions |
| 900 x 900, dark/light, open dialog | [dark](modal-900x900-dark.png), [light](modal-900x900-light.png) | Tablet-width global three-column form rule cannot alter the dialog |
| 390 x 844, dark/light, open dialog | [dark](modal-390x844-dark.png), [light](modal-390x844-light.png) | Viewport containment and real internal vertical scrolling |
| Narrow dialog scrolled to actions | [dark actions](modal-390x844-dark-actions.png), [light actions](modal-390x844-light-actions.png) | Save, Delete and Close remain reachable without horizontal overflow |
| Equivalent 200% text enlargement, desktop | [enlarged text](modal-1440x900-text-200-percent.png) | Root font size changed from 16px to 32px; modal computed font size verified 16px -> 32px. This is text enlargement, not a claim of browser page zoom or pinch zoom |
| Complete cleaned workbench after watchlist/market/history operations | [1440 dark](workbench-1440-dark.png), [900 light](workbench-900-light.png), [390 dark](workbench-390-dark.png) | Current market, main watchlist, explicit controls, Narrative and Legacy history, frozen W1 chart; no old financial/admin section |

`tests/browser/test_paqs_e_ui_cleanup.py` runs 11 business cases: six viewport/theme cases,
one enlarged-text case, one credential save/update/delete/failed-confirmation case and three
full-workbench interaction cases. DOM geometry assertions measure containment, centering, child
order, full-width input, action order/distinct primary style and button reachability. Narrow
screens require actual scroll height greater than available height. Keyboard checks cover initial
password focus, Tab, Escape, Enter reopening, Close, cleared secret and restored configuration focus.

The failed-confirmation scenario returns syntactically invalid JSON from the configuration GET
after an intercepted credential mutation. It exercises the actual existing safe failure handler,
without a real secret-store mutation or an expected HTTP-resource console error. Existing C1
credential tests additionally retain shared-slot status, removal and no browser-secret persistence.

All C2 cases assert zero page errors, zero console errors, zero Analyze POSTs, zero external
requests and no retired endpoint reads. Full-workbench cases add/select/delete (including empty
watchlist recovery), refresh current price/provenance, read both histories and a known legacy Run,
and retain the selected frozen evidence. The inherited hostile-looking prose is a harmless synthetic
renderer fixture shown as inert text; it is not an actual model answer or a new provider call.

Reproduce with declared dependencies, installed Chromium and `TASK007C_BROWSER_CHANNEL=chromium`.
Set `TASK007C2_SCREENSHOT_DIR=docs/evidence/TASK_007C2` and run
`python -m pytest tests/browser/test_paqs_e_ui_cleanup.py -ra`. The final complete validation and
exact implementation handoff are in [the implementation report](../../reports/TASK_007C2_IMPLEMENTATION_REPORT.md).
