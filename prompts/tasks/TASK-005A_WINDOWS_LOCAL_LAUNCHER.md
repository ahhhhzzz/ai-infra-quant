# TASK-005A_WINDOWS_LOCAL_LAUNCHER

**Task ID:** TASK-005A_WINDOWS_LOCAL_LAUNCHER  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Baseline commit:** `1791007e6a9c959d7db8da2b84795f0e834d8276`  
**Target base branch:** `roadmap/no-live-trading`  
**Task branch:** `task/TASK-005A_WINDOWS_LOCAL_LAUNCHER`

## 1. Goal

Add a small Windows one-click launcher for the already accepted local Dashboard.

The intended user flow is:

```text
double-click launcher
  -> verify/start Futu OpenD locally
  -> wait for 127.0.0.1:11111
  -> start AI Infra Quant with MARKET_DATA_PROVIDER=futu
  -> wait for http://127.0.0.1:8000/health
  -> open http://127.0.0.1:8000 in the default browser
```

This is a convenience/operations task only. It must not change market-data semantics, Dashboard behavior, API contracts, persistence, strategy logic, or product scope.

## 2. Primary artifact

Add a repository-root Windows batch launcher named:

```text
start_dashboard.bat
```

A root-level file is preferred so the user can launch the application by double-clicking it without navigating into a scripts directory.

Small supporting documentation/tests are allowed where necessary.

## 3. OpenD startup behavior

The launcher must first determine whether Futu OpenD is already reachable at:

```text
127.0.0.1:11111
```

If the port is already reachable:

- do not start another OpenD process;
- continue to application startup.

If the port is not reachable:

1. resolve the OpenD executable path;
2. start OpenD locally;
3. wait for port `11111` for a bounded timeout;
4. if OpenD still is not reachable, show a clear actionable message and stop without pretending the Dashboard has live data.

The launcher may leave OpenD running after the FastAPI process is stopped. It must not attempt to automate OpenD credentials, password entry, account selection, or login bypass.

## 4. OpenD executable resolution

Do not commit a machine-specific absolute path.

Resolution order should be simple and robust:

1. use environment variable `FUTU_OPEND_EXE` if it is set and points to an existing file;
2. optionally try a small bounded list of legitimate common Windows installation locations if known from the installed product structure;
3. otherwise print a clear message explaining how to set `FUTU_OPEND_EXE` and exit.

Example user configuration guidance may be:

```bat
setx FUTU_OPEND_EXE "C:\path\to\FutuOpenD.exe"
```

Do not write the user's local OpenD path into any tracked repository file automatically.

## 5. Repository and Python runtime

The launcher must resolve the repository root from the location of the batch file itself rather than relying on the user's current working directory.

Prefer the repository-local Python executable:

```text
.venv\Scripts\python.exe
```

If the required local Python environment is absent, fail safely with a concise setup message rather than silently installing packages or creating an environment.

Do not:

- run `git pull`;
- mutate branches;
- install/update dependencies automatically;
- change global environment configuration;
- require Administrator privileges.

## 6. FastAPI startup

The launcher must start the existing application with the equivalent of:

```text
MARKET_DATA_PROVIDER=futu
python -m uvicorn ai_infra_quant.backend.main:app --host 127.0.0.1 --port 8000
```

Use the existing local-only host/port contract.

Prefer starting FastAPI in a separate visible console window so application logs remain inspectable and the launcher can continue health checking/opening the browser.

Do not create a new backend service, daemon, Windows service, scheduler, background worker, or system tray application.

## 7. Existing-server behavior

Before spawning a new FastAPI process, check whether:

```text
http://127.0.0.1:8000/health
```

already reports the accepted application as healthy.

If it is already healthy:

- do not start a duplicate server;
- open/reuse the Dashboard URL.

If port `8000` is occupied but the AI Infra Quant health endpoint is not healthy, fail with a clear port-conflict message instead of killing an unrelated process.

## 8. Readiness checks

Use bounded local readiness checks for:

```text
OpenD TCP: 127.0.0.1:11111
FastAPI HTTP: http://127.0.0.1:8000/health
```

Do not rely only on arbitrary fixed sleeps.

PowerShell may be invoked from the batch script for reliable TCP/HTTP readiness probes, but no external module may be required.

Timeouts must be finite and error messages must state which component failed to become ready.

## 9. Browser behavior

Only after FastAPI is healthy, open:

```text
http://127.0.0.1:8000
```

using the Windows default browser.

Do not open the browser before readiness has been confirmed.

## 10. User-visible behavior

The launcher should be concise and understandable. Typical messages may include:

```text
[1/4] Checking Futu OpenD...
[2/4] Waiting for OpenD...
[3/4] Starting AI Infra Quant...
[4/4] Opening Dashboard...
```

On failures, keep the console visible long enough for the user to read the error (for example with `pause` on an error path).

Do not print secrets or sensitive environment values.

## 11. Safety and product boundaries

This task remains strictly read-only.

Do not add or invoke:

```text
OpenSecTradeContext
OpenFutureTradeContext
place_order
cancel_order
modify_order
unlock_trade
broker account access
real positions/cash/orders/trades
```

The launcher starts only the existing quote-only OpenD market-data path and FastAPI Dashboard.

No credential, account ID, trade password, token, or private broker export may be added to the repository or passed through the launcher.

## 12. No scope expansion

Do not implement:

- TASK-006;
- Composite Quant Score;
- indicators;
- new API routes;
- market-data persistence;
- database migration;
- public/cloud deployment;
- auto-update or auto-pull;
- Windows installer/package;
- service installation;
- automatic OpenD login.

## 13. Documentation

Update `README.md` minimally with a Windows one-click start section covering:

- double-click `start_dashboard.bat`;
- `FUTU_OPEND_EXE` one-time configuration if auto-resolution cannot find OpenD;
- OpenD login/entitlement remains external and manual;
- FastAPI logs appear in a separate console;
- browser opens at `http://127.0.0.1:8000` once ready;
- how to stop FastAPI (close the server console / Ctrl+C).

Do not rewrite unrelated documentation.

## 14. Testing

Normal repository tests must remain independent of live OpenD.

Add focused automated coverage for the launcher contract where practical, for example source-level assertions verifying:

- repository-relative path resolution;
- `FUTU_OPEND_EXE` support;
- no hard-coded user-specific absolute path;
- checks port 11111 before starting OpenD;
- uses `MARKET_DATA_PROVIDER=futu`;
- uses `.venv\Scripts\python.exe`;
- targets `127.0.0.1:8000`;
- health-checks before opening browser;
- does not contain `git pull`, package installation, trading methods, credentials, or broker-account behavior.

Do not add a heavyweight Windows testing framework solely for this batch file.

## 15. Live Windows smoke

If the executor is running on Windows with local OpenD available, perform a real smoke:

1. launch from the batch file or an equivalent non-interactive invocation;
2. confirm already-running OpenD is reused, or OpenD starts successfully;
3. confirm port `11111` becomes reachable;
4. confirm FastAPI becomes healthy on port `8000`;
5. confirm Dashboard URL is reachable;
6. confirm the app is running with Futu market-data mode;
7. avoid spawning duplicate OpenD/FastAPI instances on a repeated invocation.

If OpenD executable path cannot be resolved in the executor environment, report `LIVE_LAUNCHER_SMOKE_BLOCKED` truthfully rather than weakening the launcher.

## 16. Validation

Run at minimum:

```text
pytest -ra
ruff check .
ruff format --check .
mypy src tests
git diff --check
git diff --stat
```

Also verify the existing application still returns:

```text
GET /health -> 200
GET / -> 200
GET /openapi.json -> 200
```

Existing API surface must remain unchanged.

## 17. Expected change scope

Likely files:

```text
start_dashboard.bat
README.md
tests/... focused launcher test
```

No backend/domain/integration implementation file should need modification.

Do not modify historical Phase 1 evidence or migrations.

Preserve `phase1_remediation_commit.txt` untouched and untracked if present.

## 18. Git rules

Work only on:

```text
task/TASK-005A_WINDOWS_LOCAL_LAUNCHER
```

Create one implementation commit after this Task Contract.

Do not modify `master`.
Do not modify `roadmap/no-live-trading`.
Do not force-push.
Do not merge.
Do not start TASK-006.

## 19. Final report

Report:

```text
branch
commit SHA
parent SHA
tree SHA
changed files
launcher path
OpenD path resolution behavior
OpenD readiness behavior
FastAPI readiness behavior
existing-server/port-conflict behavior
browser-open behavior
tests/lint/type/diff results
live Windows launcher smoke result
confirmation: no credentials, no trading/account access, no API/migration/persistence changes, roadmap unchanged, no force-push
```

Then STOP.
