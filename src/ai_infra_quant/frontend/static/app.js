const REFRESH_INTERVAL_SECONDS = 60;
const API_BASE = "/api/v1";

let watchlistSecurities = [];
let selectedSecurity = null;
let activeTimeframe = "daily";
let requestGeneration = 0;
let activeRequest = null;
let automaticRefreshTimer = null;
let countdownTimer = null;
let nextRefreshAt = null;

let chart = null;
let candleSeries = null;
let volumeSeries = null;
let chartResizeObserver = null;
let stateSnapshot = null;
let dailySnapshot = null;
let minuteSnapshot = null;
let minuteCache = {
  securityId: null,
  sessionDate: null,
  barsByInterval: new Map(),
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let problem = {};
    try {
      problem = await response.json();
    } catch (_error) {
      problem = {};
    }
    throw new Error(problem.detail || problem.code || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
};

const element = (selector) => document.querySelector(selector);

const textElement = (tagName, text, className) => {
  const node = document.createElement(tagName);
  node.textContent = text;
  if (className) node.className = className;
  return node;
};

const replaceChildren = (selector, children) => {
  element(selector).replaceChildren(...children);
};

const safeErrorMessage = (error) => {
  if (error instanceof DOMException && error.name === "AbortError") return "Request cancelled";
  const message = error instanceof Error ? error.message : "Request failed";
  return message.slice(0, 240);
};

const statusClass = (status) =>
  `status-${String(status || "UNKNOWN").toLowerCase().replaceAll("_", "-")}`;

const setStatus = (selector, status) => {
  const node = element(selector);
  const value = status || "UNKNOWN";
  node.textContent = value;
  node.className = `status-badge ${statusClass(value)}`;
};

const setMarketState = (state) => {
  const node = element("#market-state");
  const value = state || "UNKNOWN";
  node.textContent = value.replaceAll("_", "-");
  node.className = `market-state ${statusClass(value)}`;
};

const timestampFormatter = (timeZone) =>
  new Intl.DateTimeFormat("zh-CN", {
    timeZone,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

const clockFormatter = (timeZone) =>
  new Intl.DateTimeFormat("zh-CN", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

const formatTimestamp = (value, timeZone) => {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return `${timestampFormatter(timeZone).format(parsed)} · ${timeZone}`;
};

const formatChartTime = (time, timeZone, timeframe) => {
  if (typeof time === "object" && time !== null) {
    const month = String(time.month).padStart(2, "0");
    const day = String(time.day).padStart(2, "0");
    return `${month}/${day}`;
  }
  if (typeof time === "string") return time.slice(5);
  const parsed = new Date(Number(time) * 1000);
  if (Number.isNaN(parsed.getTime())) return "—";
  if (timeframe === "daily") {
    return new Intl.DateTimeFormat("zh-CN", {
      timeZone,
      month: "2-digit",
      day: "2-digit",
    }).format(parsed);
  }
  return clockFormatter(timeZone).format(parsed);
};

const initializeChart = () => {
  const container = element("#market-chart");
  if (!window.LightweightCharts) {
    showChartMessage("Chart library unavailable", "The local chart asset could not be loaded.");
    return;
  }

  chart = window.LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: container.clientHeight,
    layout: {
      background: { type: window.LightweightCharts.ColorType.Solid, color: "#090e13" },
      textColor: "#8997a5",
      fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
      attributionLogo: true,
      panes: {
        separatorColor: "#26313c",
        separatorHoverColor: "#3a4a58",
        enableResize: true,
      },
    },
    grid: {
      vertLines: { color: "#151e27" },
      horzLines: { color: "#151e27" },
    },
    rightPriceScale: {
      borderColor: "#26313c",
      scaleMargins: { top: 0.08, bottom: 0.08 },
    },
    timeScale: {
      borderColor: "#26313c",
      rightOffset: 3,
      barSpacing: 8,
      minBarSpacing: 3,
    },
    crosshair: {
      mode: window.LightweightCharts.CrosshairMode.Normal,
      vertLine: { color: "#536373", labelBackgroundColor: "#32404d" },
      horzLine: { color: "#536373", labelBackgroundColor: "#32404d" },
    },
  });

  candleSeries = chart.addSeries(
    window.LightweightCharts.CandlestickSeries,
    {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderUpColor: "#26a69a",
      borderDownColor: "#ef5350",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 },
    },
    0,
  );
  volumeSeries = chart.addSeries(
    window.LightweightCharts.HistogramSeries,
    {
      priceFormat: { type: "volume" },
      priceScaleId: "",
    },
    1,
  );

  const panes = chart.panes();
  if (panes.length > 1 && typeof panes[1].setHeight === "function") {
    panes[1].setHeight(118);
  }

  chartResizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0];
    if (!entry || !chart) return;
    chart.resize(Math.floor(entry.contentRect.width), Math.floor(entry.contentRect.height));
  });
  chartResizeObserver.observe(container);
};

const configureChartTime = (timeZone) => {
  if (!chart) return;
  const formatter = (time) => formatChartTime(time, timeZone, activeTimeframe);
  chart.applyOptions({
    localization: { timeFormatter: formatter },
    timeScale: {
      timeVisible: activeTimeframe === "minute",
      secondsVisible: false,
      tickMarkFormatter: formatter,
    },
  });
};

function showChartMessage(title, detail) {
  const empty = element("#chart-empty");
  empty.replaceChildren(
    textElement("strong", title),
    textElement("span", detail),
  );
  empty.classList.add("visible");
}

const hideChartMessage = () => {
  element("#chart-empty").classList.remove("visible");
};

const clearChart = () => {
  if (candleSeries) candleSeries.setData([]);
  if (volumeSeries) volumeSeries.setData([]);
};

const numericBar = (bar, time) => ({
  time,
  open: Number(bar.open),
  high: Number(bar.high),
  low: Number(bar.low),
  close: Number(bar.close),
});

const volumeBar = (bar, time) => ({
  time,
  value: Number(bar.volume),
  color: Number(bar.close) >= Number(bar.open) ? "rgba(38, 166, 154, .55)" : "rgba(239, 83, 80, .55)",
});

const renderChart = () => {
  if (!chart || !candleSeries || !volumeSeries || !selectedSecurity) return;
  const timeZone = stateSnapshot?.market_timezone
    || dailySnapshot?.market_timezone
    || minuteSnapshot?.market_timezone
    || (selectedSecurity.market === "HK" ? "Asia/Hong_Kong" : "America/New_York");
  configureChartTime(timeZone);

  if (activeTimeframe === "daily") {
    element("#chart-caption").textContent = "Completed daily OHLCV · market-local sessions";
    const bars = dailySnapshot?.status === "AVAILABLE" ? dailySnapshot.bars : [];
    if (!bars.length) {
      clearChart();
      showChartMessage(
        "日 K 行情暂不可用",
        dailySnapshot?.reason || "No completed daily candles are available.",
      );
      return;
    }
    candleSeries.setData(bars.map((bar) => numericBar(bar, bar.session_date)));
    volumeSeries.setData(bars.map((bar) => volumeBar(bar, bar.session_date)));
  } else {
    element("#chart-caption").textContent = "Completed 1-minute OHLCV · current session";
    const bars = minuteSnapshot?.status === "AVAILABLE" ? minuteSnapshot.bars : [];
    if (!bars.length) {
      clearChart();
      const currentState = stateSnapshot?.market_state || "UNKNOWN";
      showChartMessage(
        "1分钟行情暂不可用",
        `当前市场：${currentState} · ${minuteSnapshot?.reason || "No completed current-session candles."}`,
      );
      return;
    }
    const candleData = [];
    const volumeData = [];
    for (const bar of bars) {
      const intervalTime = Math.floor(Date.parse(bar.interval_start) / 1000);
      candleData.push(numericBar(bar, intervalTime));
      volumeData.push(volumeBar(bar, intervalTime));
    }
    candleSeries.setData(candleData);
    volumeSeries.setData(volumeData);
  }
  hideChartMessage();
  chart.timeScale().fitContent();
};

const renderSecurityHeader = () => {
  if (!selectedSecurity) return;
  element("#selected-identity").textContent = `${selectedSecurity.market} · ${selectedSecurity.currency}`;
  element("#selected-title").textContent = `${selectedSecurity.symbol} · ${selectedSecurity.market}`;
  element("#selected-name").textContent = selectedSecurity.display_name || selectedSecurity.display_symbol;
  element("#latest-currency").textContent = selectedSecurity.currency;
};

const resetMarketView = () => {
  stateSnapshot = null;
  dailySnapshot = null;
  minuteSnapshot = null;
  minuteCache = {
    securityId: selectedSecurity?.id || null,
    sessionDate: null,
    barsByInterval: new Map(),
  };
  element("#latest-price").textContent = "—";
  element("#latest-quote-at").textContent = "—";
  element("#state-retrieved-at").textContent = "—";
  element("#latest-daily-session").textContent = "—";
  element("#latest-minute-at").textContent = "—";
  element("#provider-market-state").textContent = "Provider state —";
  element("#provider-mode").textContent = "Provider —";
  element("#market-data-reason").textContent = "";
  setMarketState("UNKNOWN");
  for (const selector of ["#quote-status", "#market-status", "#daily-status", "#minute-status"]) {
    setStatus(selector, "UNKNOWN");
  }
  clearChart();
  showChartMessage("Loading market data", "The chart will show completed candles only.");
};

const renderState = (data) => {
  stateSnapshot = data;
  element("#provider-mode").textContent = `Provider ${data.provider}`;
  element("#latest-price").textContent = data.quote_status === "AVAILABLE" && data.latest_price
    ? data.latest_price
    : "—";
  element("#latest-currency").textContent = data.currency;
  setMarketState(data.market_state);
  element("#provider-market-state").textContent = data.provider_market_state
    ? `Provider state ${data.provider_market_state}`
    : "Provider state —";
  element("#latest-quote-at").textContent = formatTimestamp(data.latest_quote_at, data.market_timezone);
  element("#state-retrieved-at").textContent = formatTimestamp(data.retrieved_at, data.market_timezone);
  setStatus("#quote-status", data.quote_status);
  setStatus("#market-status", data.market_status);
};

const renderStateFailure = (reason) => {
  stateSnapshot = null;
  element("#latest-price").textContent = "—";
  element("#latest-quote-at").textContent = "—";
  element("#state-retrieved-at").textContent = "—";
  element("#provider-market-state").textContent = "Provider state —";
  setMarketState("UNKNOWN");
  setStatus("#quote-status", "PROVIDER_ERROR");
  setStatus("#market-status", "PROVIDER_ERROR");
  return reason;
};

const renderDaily = (data) => {
  dailySnapshot = data.status === "AVAILABLE" ? data : { ...data, bars: [] };
  setStatus("#daily-status", data.status);
  element("#latest-daily-session").textContent = data.latest_completed_daily_session || "—";
};

const renderDailyFailure = (reason) => {
  dailySnapshot = { status: "PROVIDER_ERROR", bars: [], reason };
  setStatus("#daily-status", "PROVIDER_ERROR");
  element("#latest-daily-session").textContent = "—";
  return reason;
};

const renderMinute = (data) => {
  if (minuteCache.securityId !== data.security_id || minuteCache.sessionDate !== data.session_date) {
    minuteCache = {
      securityId: data.security_id,
      sessionDate: data.session_date,
      barsByInterval: new Map(),
    };
  }

  if (data.status === "AVAILABLE") {
    for (const bar of data.bars) minuteCache.barsByInterval.set(bar.interval_start, bar);
  } else {
    minuteCache.barsByInterval.clear();
  }

  minuteSnapshot = {
    ...data,
    bars: [...minuteCache.barsByInterval.values()].sort((left, right) =>
      left.interval_start.localeCompare(right.interval_start)),
  };
  setStatus("#minute-status", data.status);
  element("#latest-minute-at").textContent = formatTimestamp(
    data.latest_completed_minute_bar_at,
    data.market_timezone,
  );
};

const renderMinuteFailure = (reason) => {
  minuteCache.barsByInterval.clear();
  minuteSnapshot = { status: "PROVIDER_ERROR", bars: [], reason };
  setStatus("#minute-status", "PROVIDER_ERROR");
  element("#latest-minute-at").textContent = "—";
  return reason;
};

const clearRefreshSchedule = () => {
  if (automaticRefreshTimer !== null) window.clearTimeout(automaticRefreshTimer);
  if (countdownTimer !== null) window.clearInterval(countdownTimer);
  automaticRefreshTimer = null;
  countdownTimer = null;
  nextRefreshAt = null;
};

const updateCountdown = () => {
  if (document.visibilityState === "hidden") {
    element("#refresh-countdown").textContent = "自动刷新：已暂停";
    return;
  }
  if (nextRefreshAt === null) {
    element("#refresh-countdown").textContent = activeRequest ? "自动刷新：刷新中" : "自动刷新：—";
    return;
  }
  const remaining = Math.max(0, Math.ceil((nextRefreshAt - Date.now()) / 1000));
  element("#refresh-countdown").textContent = `自动刷新：${remaining}s`;
};

const scheduleNextRefresh = () => {
  clearRefreshSchedule();
  if (document.visibilityState === "hidden" || !selectedSecurity) {
    updateCountdown();
    return;
  }
  nextRefreshAt = Date.now() + REFRESH_INTERVAL_SECONDS * 1000;
  updateCountdown();
  countdownTimer = window.setInterval(updateCountdown, 250);
  automaticRefreshTimer = window.setTimeout(() => {
    refreshSelectedSecurity("automatic");
  }, REFRESH_INTERVAL_SECONDS * 1000);
};

const setRefreshLoading = (loading) => {
  const button = element("#refresh-market");
  button.disabled = loading;
  button.textContent = loading ? "刷新中…" : "刷新最新行情";
  updateCountdown();
};

const cancelActiveRequest = () => {
  if (!activeRequest) return;
  activeRequest.controller.abort();
  activeRequest = null;
  setRefreshLoading(false);
};

const fulfilledValue = (result) => result.status === "fulfilled" ? result.value : null;

const rejectedReason = (result) => result.status === "rejected"
  ? safeErrorMessage(result.reason)
  : null;

const refreshSelectedSecurity = async (_trigger) => {
  if (!selectedSecurity || activeRequest || document.visibilityState === "hidden") return;
  clearRefreshSchedule();
  const securityId = selectedSecurity.id;
  const request = {
    controller: new AbortController(),
    generation: requestGeneration,
    securityId,
  };
  activeRequest = request;
  setRefreshLoading(true);

  const basePath = `${API_BASE}/market-data/securities/${securityId}`;
  try {
    const results = await Promise.allSettled([
      api(`${basePath}/state`, { signal: request.controller.signal }),
      api(`${basePath}/daily-bars?limit=120`, { signal: request.controller.signal }),
      api(`${basePath}/minute-bars`, { signal: request.controller.signal }),
    ]);

    if (
      activeRequest !== request
      || request.generation !== requestGeneration
      || selectedSecurity?.id !== request.securityId
    ) return;

    const reasons = [];
    const state = fulfilledValue(results[0]);
    const daily = fulfilledValue(results[1]);
    const minute = fulfilledValue(results[2]);

    if (state) {
      renderState(state);
      if (state.reason) reasons.push(state.reason);
    } else {
      reasons.push(renderStateFailure(rejectedReason(results[0]) || "Market state unavailable"));
    }

    if (daily) {
      renderDaily(daily);
      if (daily.reason) reasons.push(`Daily: ${daily.reason}`);
    } else {
      reasons.push(renderDailyFailure(rejectedReason(results[1]) || "Daily data unavailable"));
    }

    if (minute) {
      renderMinute(minute);
      if (minute.reason) reasons.push(`1 minute: ${minute.reason}`);
    } else {
      reasons.push(renderMinuteFailure(rejectedReason(results[2]) || "Minute data unavailable"));
    }

    element("#market-data-reason").textContent = [...new Set(reasons)].join(" · ");
    renderChart();
  } finally {
    if (activeRequest === request) {
      activeRequest = null;
      setRefreshLoading(false);
      scheduleNextRefresh();
    }
  }
};

const renderSecuritySelector = () => {
  const choices = watchlistSecurities.map((security) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "security-option";
    button.dataset.securityId = security.id;
    button.setAttribute("role", "option");
    const selected = selectedSecurity?.id === security.id;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-selected", String(selected));
    button.append(
      textElement("span", security.symbol, "security-symbol"),
      textElement("span", security.market, "security-market"),
      textElement("span", security.display_name || security.display_symbol, "security-name"),
      textElement("span", security.currency, "security-currency"),
    );
    button.addEventListener("click", () => selectSecurity(security));
    return button;
  });
  replaceChildren("#security-selector", choices);
  element("#market-watchlist-status").textContent = `${choices.length} securities`;
};

const selectSecurity = (security) => {
  if (selectedSecurity?.id === security.id) return;
  requestGeneration += 1;
  cancelActiveRequest();
  clearRefreshSchedule();
  selectedSecurity = security;
  setRefreshLoading(false);
  renderSecuritySelector();
  renderSecurityHeader();
  resetMarketView();
  if (document.visibilityState === "visible") refreshSelectedSecurity("security-switch");
};

const clearSelectedSecurity = () => {
  requestGeneration += 1;
  cancelActiveRequest();
  clearRefreshSchedule();
  selectedSecurity = null;
  renderSecuritySelector();
  resetMarketView();
  element("#selected-identity").textContent = "—";
  element("#selected-title").textContent = "No tracked securities";
  element("#selected-name").textContent = "Add a Security to the Watchlist";
  element("#latest-currency").textContent = "—";
  element("#chart-caption").textContent = "Select a tracked Security to load market data";
  element("#market-data-reason").textContent = "No tracked securities";
  for (const selector of ["#quote-status", "#market-status", "#daily-status", "#minute-status"]) {
    setStatus(selector, "MISSING");
  }
  showChartMessage(
    "No tracked securities",
    "Add a Security to the Watchlist to load market data.",
  );
  element("#refresh-market").disabled = true;
  updateCountdown();
};

const renderAdminWatchlist = () => {
  const rows = watchlistSecurities.map((security) => {
    const row = document.createElement("div");
    row.className = "watchlist-row";
    row.append(
      textElement("span", security.display_symbol, "symbol"),
      textElement("span", security.currency, "muted"),
      textElement("span", security.metadata_status, "status"),
    );
    const button = textElement("button", "Remove", "remove-button");
    button.type = "button";
    button.dataset.securityId = security.id;
    button.addEventListener("click", async () => {
      await api(`${API_BASE}/watchlist/${button.dataset.securityId}`, { method: "DELETE" });
      await loadWatchlist();
    });
    row.append(button);
    return row;
  });
  replaceChildren("#watchlist-admin", rows);
  element("#admin-watchlist-status").textContent = `${rows.length} identities`;
};

const loadWatchlist = async () => {
  const data = await api(`${API_BASE}/watchlist`);
  watchlistSecurities = data.items.map(({ security }) => security);
  const currentStillExists = watchlistSecurities.find((item) => item.id === selectedSecurity?.id);
  const defaultSecurity = watchlistSecurities.find((item) => item.display_symbol === "US.AVGO")
    || watchlistSecurities[0]
    || null;
  renderAdminWatchlist();
  if (!defaultSecurity) {
    clearSelectedSecurity();
    return;
  }
  if (!currentStillExists) {
    selectSecurity(defaultSecurity);
  } else {
    selectedSecurity = currentStillExists;
    renderSecuritySelector();
    renderSecurityHeader();
  }
};

const loadAdministration = async () => {
  const [portfolio, performance, brokers, market, fundamental, events] = await Promise.all([
    api(`${API_BASE}/portfolio`),
    api(`${API_BASE}/performance`),
    api(`${API_BASE}/brokers`),
    api(`${API_BASE}/market-data/providers`),
    api(`${API_BASE}/fundamental-data/providers`),
    api(`${API_BASE}/event-data/providers`),
  ]);
  element("#equity").textContent = `${portfolio.base_currency} ${portfolio.total_equity}`;
  element("#cash").textContent = `${portfolio.base_currency} ${portfolio.cash_value}`;
  element("#nav").textContent = portfolio.nav;
  element("#units").textContent = portfolio.units_outstanding;
  element("#invested").textContent = portfolio.invested_ratio;
  element("#return").textContent = performance.summary.since_inception_return;

  const statuses = [...brokers.items, ...market.items, ...fundamental.items, ...events.items];
  const rows = statuses.map((item) => {
    const row = document.createElement("div");
    row.className = "status-row";
    row.append(
      textElement("span", item.name),
      textElement("span", `${item.implementation_status} / ${item.connection_status}`, "status"),
    );
    return row;
  });
  replaceChildren("#providers", rows);
};

for (const tab of document.querySelectorAll(".timeframe-tab")) {
  tab.addEventListener("click", () => {
    activeTimeframe = tab.dataset.timeframe;
    for (const candidate of document.querySelectorAll(".timeframe-tab")) {
      const selected = candidate === tab;
      candidate.classList.toggle("active", selected);
      candidate.setAttribute("aria-selected", String(selected));
    }
    renderChart();
  });
}

element("#refresh-market").addEventListener("click", () => {
  if (!activeRequest) refreshSelectedSecurity("manual");
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") {
    clearRefreshSchedule();
    cancelActiveRequest();
    updateCountdown();
    return;
  }
  refreshSelectedSecurity("visibility-restored");
});

element("#security-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form.entries());
  if (!payload.display_name) delete payload.display_name;
  const result = element("#form-result");
  try {
    const security = await api(`${API_BASE}/securities`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await api(`${API_BASE}/watchlist`, {
      method: "POST",
      body: JSON.stringify({ security_id: security.id }),
    });
    result.textContent = `${security.display_symbol} created as USER_SUPPLIED_UNVERIFIED and added to the watchlist.`;
    event.target.reset();
    await loadWatchlist();
  } catch (error) {
    result.textContent = safeErrorMessage(error);
  }
});

const initialize = async () => {
  initializeChart();
  await loadWatchlist();
  loadAdministration().catch((error) => {
    replaceChildren("#providers", [textElement("p", safeErrorMessage(error), "note")]);
  });
};

initialize().catch((error) => {
  element("#market-watchlist-status").textContent = safeErrorMessage(error);
  showChartMessage("Dashboard unavailable", "Local application data could not be loaded.");
});
