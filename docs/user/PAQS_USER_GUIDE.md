# PAQS User Guide — through TASK-006B Structure

PAQS is a read-only way to explain market structure and support investment research. TASK-006A
prepares trustworthy inputs and lets the local Dashboard use supported US and Hong Kong equities.
TASK-006B now interprets the structure of completed W1, D1, and regular-session 30-minute bars. It
still does not say BUY, HOLD, SELL, or whether any setup should be traded.

## Add or remove a stock

In the Dashboard Watchlist, choose `US` or `HK`, enter the symbol, and select **Add US/HK stock**.
For US stocks, enter the ordinary ticker such as `NVDA`. For Hong Kong stocks, `700` and `00700`
both become the canonical five-digit symbol `HK.00700`.

The application asks the configured read-only market-data provider for an exact matching quote and
an explicit equity classification before it changes the local database. The add can fail when no
provider is configured, OpenD is unavailable, the symbol is invalid, unsupported or not an equity,
or the current account lacks quote entitlement. On any such failure, no Security or Watchlist item
is created. Adding the same valid stock again is safe and does not create duplicates.

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

## Reading the TASK-006B structure output

The developer structure endpoint shows three independent views: W1 context, D1 setup-timeframe
structure, and 30-minute trigger-timeframe structure. A lower timeframe cannot rewrite a higher
one.

ATR measures recent price movement and provides a common distance scale. It is not bullish or
bearish. ATR is unavailable until 14 completed bars exist; unavailable does not mean zero.

A Pivot records two different bars. The **extreme bar** contains the High or Low. A later
**confirmation bar** closes far enough away, measured in ATR. A same-bar wick cannot establish the
order of extreme and reversal, so it cannot confirm itself. Micro Pivots use a smaller reversal
threshold and describe denser local structure. Major Pivots use a larger threshold and supply the
structure used for levels, Zones, Ranges, and trend Regime.

Swing labels compare confirmed Pivots of the same kind:

- Highs are `HH` (higher), `LH` (lower), or `EH` (equal within tolerance).
- Lows are `HL` (higher), `LL` (lower), or `EL` (equal within tolerance).

A Major Pivot creates a one-price Key Level. A Zone is an area built from nearby same-role Major
Pivots. One independent touch is only a candidate Zone; two or more separated touches confirm it.
Support and resistance observations are never mixed into one Zone.

A Range requires confirmed support and resistance Zones, alternating reactions on both sides,
enough completed history, enough closes inside its boundaries, and reasonable ATR-normalized
width. A Range is active only while the latest completed close remains inside. An outside close
simply makes it inactive in TASK-006B; no breakout meaning is assigned.

Base Regime has only four meanings:

- `BULL_TREND`: confirmed Major `HH` and `HL` structure remains coherent.
- `BEAR_TREND`: confirmed Major `LH` and `LL` structure remains coherent.
- `RANGE`: an active confirmed Range takes precedence.
- `UNCERTAIN`: history, ATR, Pivots or Swing agreement is insufficient, equal, conflicting, or no
  longer coherent. This is a legitimate truthful result, not an error and not a neutral trade call.

The structure output is diagnostic research evidence. It contains no setup qualification, target,
risk/reward, Entry or Holder advisory, score, ranking, account observation, or order function. All
real trading remains manual in the broker's official client.
