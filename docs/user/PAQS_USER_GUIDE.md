# PAQS User Guide — TASK-006A

PAQS is intended to become a read-only way to explain market structure and support investment
decisions. TASK-006A does not make those interpretations yet. It prepares trustworthy inputs and
lets the local Dashboard use supported US and Hong Kong equities beyond the original three
demonstration symbols.

## Add or remove a stock

In the Dashboard Watchlist, choose `US` or `HK`, enter the symbol, and select **Add US/HK stock**.
For US stocks, enter the ordinary ticker such as `NVDA`. For Hong Kong stocks, `700` and `00700`
both become the canonical five-digit symbol `HK.00700`.

The application asks the configured read-only market-data provider for an exact matching quote
before it changes the local database. The add can fail when no provider is configured, OpenD is
unavailable, the symbol is invalid or unsupported, or the current account lacks quote entitlement.
On any such failure, no Security or Watchlist item is created. Adding the same valid stock again is
safe and does not create duplicates.

Use **Remove** under local Watchlist administration to remove a stock. A successful add refreshes
the selector immediately; the new stock can be selected without reloading the page and uses the
same latest, Daily, and 1-minute views as the original symbols.

Provider quote validation means only that read-only market data was available for the exact symbol.
The stored Security remains a local `USER_SUPPLIED` / unverified identity. It is not a claim that a
broker would accept an order, and the application does not connect to a brokerage account.

## The three prepared timeframes

- W1 is the future PAQS context input, derived from completed Daily bars.
- D1 is the future setup input and always means completed Daily bars.
- 30m is the future trigger input, derived from complete sets of completed 1-minute bars.

H1 and H4 are not required by the approved initial PAQS hierarchy. TASK-006A does not create them.

Only completed bars are used. A current unfinished week or 30-minute interval cannot become a
confirmed input. A 30-minute interval with a missing source minute is unavailable for completed
PAQS input; the application does not fill the gap with a repeated price or zero.

US 1-minute Dashboard history may contain overnight, pre-market, regular-session, and after-hours
observations. Initial PAQS 30-minute input uses only the 09:30–16:00 New York regular session.
Hong Kong input uses 09:30–12:00 and 13:00–16:00 without bridging lunch.

The current Futu history path uses the provider's current QFQ adjustment. It is labelled
`PROVIDER_QFQ_CURRENT` with `historical_replay_safe = false`. That data is useful for current
research input, but it is not a claim that a strict point-in-time historical backtest is safe.

TASK-006A implements no BUY, HOLD, EXIT, structure, setup, target, risk/reward, ranking, or score
behavior. All real trading remains manual in the broker's official client.
