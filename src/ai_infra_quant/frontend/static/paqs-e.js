/* TASK-007C: only the explicit form submission can dispatch Analyze. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const node = (tag, text, className = "") => {
    const item = document.createElement(tag);
    item.textContent = text;
    item.className = className;
    return item;
  };
  const uuid = (value) => typeof value === "string"
    && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
  const identifier = (value) => typeof value === "string" && value.length > 0
    && !/[\s\u001c-\u001f\u0085]/u.test(value);
  const hash = (value) => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const same = (left, right) => left != null && left === right;
  // Identity comparisons retain Python's microseconds; Date.parse loses sub-millisecond digits.
  const utcIdentity = (value) => {
    if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) return null;
    const match = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?(?:Z|\+00:00)$/.exec(value);
    return match ? `${match[1]}.${(match[2] || "").padEnd(6, "0")}` : null;
  };
  const instant = (left, right) => utcIdentity(left) !== null && utcIdentity(left) === utcIdentity(right);
  const zoneFor = (market) => market === "HK" ? "Asia/Hong_Kong" : "America/New_York";
  const stamp = (value, market) => {
    if (!value || !Number.isFinite(Date.parse(value))) return "时间不可用";
    return `${new Intl.DateTimeFormat("zh-CN", {
      timeZone: zoneFor(market), year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
    }).format(new Date(value))} · ${zoneFor(market)}`;
  };
  const labels = {
    support_status: "支持状态", input_quality: "输入质量", data_quality_reasons: "质量原因",
    htf: "W1 · 高周期背景", stf: "D1 · 结构周期", ttf: "M30 · 触发周期",
    states: "结构状态", evidence: "判断依据", regime_summary: "市场结构摘要",
    trend_quality: "趋势质量", market_bias: "市场倾向", avoid_long_flag: "回避做多",
    price_or_zone: "语义价格 / 区域（仅文本）", role: "作用", timeframe: "适用周期",
    rationale: "理由", state_change: "状态改变条件", description: "当前位置", quality: "位置质量",
    current_event: "当前事件", transition_states: "过渡状态", trigger_status: "触发确认",
    followthrough_status: "后续延续确认", impulse_correction_read: "推动 / 修正解读",
    channel_or_exhaustion_context: "通道 / 衰竭背景",
    structural_confirmation_uses_reference_only_quote: "结构确认是否使用仅供参考报价",
    family: "Setup 家族", direction: "方向", stage: "阶段", expiry_reason: "失效原因",
    why_it_qualifies: "成立依据", missing_confirmation: "缺少的确认", alternative_interpretation: "最强替代解释",
    current_price_reference: "当前价格参考", executable_entry_reference: "可执行语义入场参考（非订单）",
    price: "精确价格", timestamp: "参考时间", session_type: "交易时段", freshness_status: "新鲜度",
    policy_basis: "资格政策依据", eligible: "语义参考是否合格", advisory: "建议状态",
    reference_or_zone: "入场参考 / 语义区域", chase_risk: "追价风险", wait_condition: "等待条件",
    level_or_zone: "结构价位 / 语义区域", calculation_reference: "精确计算参考",
    condition: "失效条件", reason: "理由", strength: "失效强度",
    t1_level_or_zone: "T1 结构目标", t1_calculation_reference: "T1 精确计算参考", t1_reason: "T1 理由",
    t1_is_nearest_structural_obstacle: "T1 是否最近结构障碍", t2_level_or_zone: "T2 结构目标",
    t2_calculation_reference: "T2 精确计算参考", t2_reason: "T2 理由", rr_status: "RR 状态",
    risk_per_share: "每股风险（精确值）", rr_t1: "RR T1（精确值）", rr_t2: "RR T2（精确值）", rr_quality: "RR 质量",
    advisory_basis: "条件性持有判断依据", prior_decision_id: "显式前序 Decision", level: "不确定性程度",
    conflicting_evidence: "冲突证据", data_limitations: "数据限制",
  };
  const enums = {
    NO_SETUP: "尚无形态", WATCH_LONG: "观察多头", WATCH_SHORT: "观察空头", NO_TRADE: "暂不参与",
    WAIT_RETEST: "等待回测", LONG_READY: "多头条件就绪", SHORT_READY: "空头条件就绪",
    ENTRY_PENDING_REVALIDATION: "等待重新验证入场", VALID_SETUP_BUT_POOR_ENTRY: "形态有效但入场位置欠佳",
    SETUP_EXPIRED: "形态已过期", DATA_UNAVAILABLE: "数据不可用", UNCERTAIN: "不确定",
    SUPPORTED: "支持", UNSUPPORTED: "不支持", COMPLETE: "完整", PARTIAL: "部分", INVALID: "无效",
    BULL_TREND: "多头趋势", BEAR_TREND: "空头趋势", RANGE: "区间", TRANSITION: "过渡",
    REVERSAL_CANDIDATE: "候选反转", TREND_DETERIORATING: "趋势转弱", BULLISH: "偏多", BEARISH: "偏空",
    NEUTRAL: "中性", MIXED: "混合", NOT_CONFIRMED: "未确认", CONFIRMED: "已确认",
    NOT_APPLICABLE: "不适用", PENDING: "等待中", WEAK: "较弱", UNAVAILABLE: "不可用",
    FINAL: "最终值", PENDING_ENTRY_REFERENCE: "等待入场参考", NOT_COMPUTABLE: "不可计算",
    LOW: "低", MEDIUM: "中", HIGH: "高", REGULAR: "常规时段", PRE: "盘前", POST: "盘后",
    CLOSED_REFERENCE: "休市参考", UNKNOWN: "未知", FRESH: "新鲜", STALE: "过期", DELAYED: "延迟",
    CURRENT_ANALYSIS_THESIS: "当前分析论点", PRIOR_DECISION_ID: "显式前序 Decision", NOT_AVAILABLE: "不可用",
    THESIS_VALID: "论点仍有效", HOLD_WITH_WARNING: "持有需警惕", TARGET_REACHED_REVIEW: "目标到达待复核",
    EXIT_IF_HELD: "若已持有则退出", NONE: "无", LONG: "多头", SHORT: "空头", GOOD: "良好",
    MARGINAL: "临界", POOR: "较差", HARD: "硬失效", SOFT: "软失效",
  };
  const display = (value) => value == null ? "未提供"
    : typeof value === "boolean" ? (value ? "是" : "否")
      : enums[value] ? `${enums[value]} · ${value}` : String(value);
  // Every structured field remains accessible; model prose is always inert text.
  function fields(value, market) {
    const root = node("div", "", "field-list");
    if (Array.isArray(value)) {
      if (!value.length) root.append(node("p", "无已报告项目", "muted"));
      for (const entry of value) root.append(fields(entry, market));
    } else if (value && typeof value === "object") {
      for (const [key, entry] of Object.entries(value)) {
        const row = node("div", "", "field-row");
        row.append(node("span", labels[key] || key, "field-label"));
        if (entry && typeof entry === "object") row.append(fields(entry, market));
        else {
          const text = key === "timestamp" && entry ? `${stamp(entry, market)} / UTC ${entry}` : display(entry);
          row.append(node("p", text, "field-value"));
        }
        root.append(row);
      }
    } else root.append(node("p", display(value), "field-value"));
    return root;
  }

  let security = selectedSecurity;
  let configuration = null;
  let inFlight = null;
  let navigation = 0;
  let detailGeneration = 0;
  let selectionIntent = 0;
  let historyGeneration = 0;
  let runGeneration = 0;
  let history = [];
  let decision = null;
  let snapshot = null;
  let historical = false;
  let earlier = false;
  let evidenceFrame = "W1";
  let frozenMode = false;
  let frozenChart = null;
  let frozenCandles = null;
  let frozenVolume = null;
  let priceLines = [];

  const get = async (path) => {
    const response = await fetch(`/api/v1/paqs-e/${path}`, { headers: { Accept: "application/json" } });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || body.code || `HTTP ${response.status}`);
    return body;
  };
  const updateButton = () => {
    $("analyze-button").disabled = Boolean(inFlight) || !security || !selectedModel()?.credential_configured;
    $("analyze-button").textContent = inFlight ? "分析请求进行中…" : "Analyze · 分析当前快照";
  };
  const state = (message) => { $("analysis-state").textContent = message; };
  const identityLine = (item) => `${item.symbol} · ${item.market} · 修订 ${item.revision_no} · ${item.strategy_id} · ${modelName(item.model_id)} · 快照 ${stamp(item.snapshot_as_of_timestamp, item.market)}`;
  function renderHeading() {
    const text = decision ? `${historical ? "已选择历史 Decision" : "已选 Decision"}${earlier ? " · 较早成功结果（不是本次尝试）" : ""}\n${identityLine(decision)}` : "尚无选中的 Decision";
    $("decision-heading").textContent = text;
    $("evidence-identity").textContent = text;
  }
  function clearEvidence(message = "冻结证据尚不可用") {
    snapshot = null;
    for (const line of priceLines) frozenCandles?.removePriceLine(line);
    priceLines = [];
    frozenCandles?.setData([]);
    frozenVolume?.setData([]);
    $("overlay-labels").replaceChildren();
    $("evidence-facts").replaceChildren();
    $("evidence-empty").textContent = message;
    $("evidence-empty").classList.add("visible");
    $("evidence-status").textContent = message;
  }
  function renderDecision() {
    renderHeading();
    if (!decision) {
      $("decision-result").replaceChildren(node("p", "选择成功历史，或填写模型后显式 Analyze。", "note"));
      $("decision-audit").textContent = "—";
      return;
    }
    const result = decision.result;
    const groups = [
      ["support", "支持与输入质量"], ["context", "多周期背景与方向"],
      ["key_levels", "关键价位 · 语义区域只作文本"], ["current_location", "当前位置"],
      ["price_action", "价格行为 · 触发与延续分别确认"], ["setup", "Setup · 条件与替代解释"],
      ["entry", "入场建议与等待条件"], ["price_references", "价格参考与资格"],
      ["invalidation", "结构失效"], ["targets", "结构目标"], ["risk_reward", "风险回报 · 服务端精确值"],
      ["holder", "若已持有 · 条件性建议，系统不知道实际持仓"], ["uncertainty", "不确定性与限制"],
      ["next_evidence_needed", "下一步所需证据"], ["reason_codes", "原因代码"], ["explanation", "简明解释"],
    ];
    const children = [node("div", display(result.entry.advisory), "advisory-badge"),
      node("p", result.one_line_thesis, "thesis")];
    for (const [key, title] of groups) {
      const section = node("details", "", "result-group");
      section.open = ["support", "context", "entry"].includes(key);
      section.append(node("summary", title), fields(result[key], decision.market));
      children.push(section);
    }
    $("decision-result").replaceChildren(...children);
    $("decision-audit").textContent = JSON.stringify(decision, null, 2);
  }

  const identityKeys = ["symbol", "market", "instrument_type", "snapshot_hash", "analysis_mode",
    "request_schema_version", "output_schema_version", "runtime_config_version", "model_provider", "model_id",
    "prompt_version", "prompt_content_sha256"];
  function assertIdentity(ledger, payload) {
    if (!payload || identityKeys.some((key) => !same(ledger[key], payload[key]))
      || !instant(ledger.snapshot_as_of_timestamp, payload.snapshot_as_of_timestamp)
      || !same(ledger.strategy_id, payload.primary_strategy_id)
      || !same(ledger.strategy_content_sha256, payload.primary_strategy_content_sha256)) {
      throw new Error("响应身份不匹配：证券、模型、策略或快照证据不可关联");
    }
  }
  function assertDecision(item, expected) {
    if (!item || !uuid(item.decision_id) || !uuid(item.analysis_run_id) || !hash(item.snapshot_hash)
      || !Number.isInteger(item.revision_no) || item.revision_no < 1
      || !same(item.security_id, expected.security_id)
      || (expected.decision_id && !same(item.decision_id, expected.decision_id))
      || (expected.analysis_run_id && !same(item.analysis_run_id, expected.analysis_run_id))
      || (expected.model_id && !same(item.model_id, expected.model_id))
      || (expected.strategy_id && !same(item.strategy_id, expected.strategy_id))
      || (expected.snapshot_hash && !same(item.snapshot_hash, expected.snapshot_hash))) {
      throw new Error("Decision 响应身份不匹配");
    }
    assertIdentity(item, item.result?.identity);
    for (const name of ["support", "context", "key_levels", "current_location", "price_action", "setup",
      "entry", "price_references", "invalidation", "targets", "risk_reward", "holder", "uncertainty",
      "next_evidence_needed", "reason_codes", "explanation", "one_line_thesis"]) {
      if (!(name in item.result) || item.result[name] == null) throw new Error("Decision 结构不完整");
    }
  }
  function parseRun(run, expected) {
    if (!run || !uuid(run.analysis_run_id) || !same(run.analysis_run_id, expected.analysis_run_id)
      || (expected.security_id && !same(run.security_id, expected.security_id))
      || (expected.status && !same(run.status, expected.status))
      || (expected.model_id && !same(run.model_id, expected.model_id))
      || (expected.strategy_id && !same(run.strategy_id, expected.strategy_id))
      || !["SUCCEEDED", "PROVIDER_FAILED", "VALIDATION_FAILED"].includes(run.status)
      || typeof run.request_payload_json !== "string" || !hash(run.request_payload_sha256)) {
      throw new Error("Run 响应身份或状态不匹配");
    }
    if (expected.snapshot_hash) {
      for (const key of [...identityKeys, "strategy_id", "strategy_content_sha256", "security_id"])
        if (!same(run[key], expected[key])) throw new Error("Decision 与 Run 身份不匹配");
      if (!instant(run.snapshot_as_of_timestamp, expected.snapshot_as_of_timestamp)) throw new Error("快照时间不匹配");
    }
    const request = JSON.parse(run.request_payload_json);
    assertIdentity(run, request);
    const evidence = request.market_snapshot;
    if (!evidence || !same(evidence.security?.security_id, run.security_id)
      || !same(evidence.security.symbol, run.symbol) || !same(evidence.security.market, run.market)
      || !same(evidence.snapshot_hash, run.snapshot_hash)
      || !instant(evidence.as_of_timestamp, run.snapshot_as_of_timestamp)
      || !same(evidence.security.market_timezone, zoneFor(run.market))) throw new Error("输入快照身份不匹配");
    for (const key of ["w1_bars", "d1_bars", "m30_bars"])
      if (!Array.isArray(evidence[key])) throw new Error("输入证据缺少周期数组");
    return evidence;
  }
  function chartTheme(target, light) {
    target?.applyOptions({ layout: { background: { color: light ? "#ffffff" : "#090e13" },
      textColor: light ? "#435365" : "#b0bfce" }, grid: {
      vertLines: { color: light ? "#e9eef2" : "#151e27" }, horzLines: { color: light ? "#e9eef2" : "#151e27" },
    } });
  }
  function initializeFrozenChart() {
    if (frozenChart || !window.LightweightCharts) return;
    const root = $("frozen-chart");
    frozenChart = window.LightweightCharts.createChart(root, {
      width: root.clientWidth, height: root.clientHeight,
      layout: { attributionLogo: true, panes: { enableResize: true } },
      rightPriceScale: { scaleMargins: { top: .1, bottom: .1 } },
      timeScale: { rightOffset: 3 },
    });
    frozenCandles = frozenChart.addSeries(window.LightweightCharts.CandlestickSeries, {
      upColor: "#26a69a", downColor: "#ef5350", borderVisible: false,
      wickUpColor: "#26a69a", wickDownColor: "#ef5350",
    }, 0);
    frozenVolume = frozenChart.addSeries(window.LightweightCharts.HistogramSeries, { priceFormat: { type: "volume" } }, 1);
    frozenChart.panes()[1].setHeight(85);
    new ResizeObserver(() => frozenChart.resize(root.clientWidth, root.clientHeight)).observe(root);
    chartTheme(frozenChart, document.documentElement.dataset.theme === "light");
  }
  function drawEvidence() {
    if (!snapshot || !decision || !frozenMode) return;
    initializeFrozenChart();
    if (!frozenChart) { clearEvidence("本地图表库不可用"); return; }
    for (const line of priceLines) frozenCandles.removePriceLine(line);
    priceLines = [];
    $("overlay-labels").replaceChildren();
    try {
      const bars = snapshot[{ W1: "w1_bars", D1: "d1_bars", M30: "m30_bars" }[evidenceFrame]];
      const candles = [], volumes = [];
      let previous = null;
      for (const bar of bars) {
        if (bar.is_completed !== true || (evidenceFrame !== "D1" && bar.coverage !== "COMPLETE"))
          throw new Error("证据包含未完成或不完整区间");
        const time = evidenceFrame === "D1" ? bar.session_date : Date.parse(bar.interval_start) / 1000;
        if ((evidenceFrame === "D1" && !/^\d{4}-\d{2}-\d{2}$/.test(time))
          || (evidenceFrame !== "D1" && (!Number.isFinite(time) || !Number.isFinite(Date.parse(bar.interval_end))))
          || (previous != null && time <= previous)) throw new Error("证据区间无效或顺序错误");
        previous = time;
        candles.push(numericBar(bar, time));
        if (bar.volume != null) volumes.push(volumeBar(bar, time));
      }
      const marketZone = zoneFor(decision.market);
      const format = (time) => `${formatChartCrosshairTime(time, marketZone, evidenceFrame === "D1" ? "daily" : "minute")} · ${marketZone}`;
      frozenChart.applyOptions({ localization: { timeFormatter: format }, timeScale: {
        timeVisible: evidenceFrame === "M30",
        tickMarkFormatter: (time) => formatChartAxisTime(time, marketZone,
          evidenceFrame === "M30" ? "minute" : "daily"),
      } });
      frozenCandles.setData(candles);
      frozenVolume.setData(volumes);
      if (candles.length) frozenChart.timeScale().setVisibleLogicalRange({ from: Math.max(0, candles.length - 70), to: candles.length + 2 });
      $("evidence-empty").classList.toggle("visible", !candles.length);
      $("evidence-empty").textContent = "该周期没有已完成的权威证据 K 线";
      $("evidence-status").textContent = `冻结 ${evidenceFrame} · ${candles.length} 根已完成 K 线 · 成交量独立窗格，缺失不补零 · ${marketZone} · 当前复权不代表严格历史时点可重放`;
      const entry = decision.result.price_references.executable_entry_reference;
      const overlays = [
        [`入场参考 · ${entry.session_type} · ${entry.eligible ? "合格" : "不合格"}`, entry.price, "#269e8c"],
        [`失效 · ${decision.result.invalidation.timeframe}`, decision.result.invalidation.calculation_reference, "#d65a58"],
        ["T1 结构计算参考", decision.result.targets.t1_calculation_reference, "#a484de"],
        ["T2 结构计算参考", decision.result.targets.t2_calculation_reference, "#779de0"],
      ];
      for (const [label, value, color] of overlays) {
        if (value == null) continue;
        const price = chartNumber(value);
        $("overlay-labels").append(node("p", `${label}：${value}`, "overlay-label"));
        if (candles.length) priceLines.push(frozenCandles.createPriceLine({ price, color,
          lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: label }));
      }
      const metadata = { ...snapshot };
      delete metadata.w1_bars; delete metadata.d1_bars; delete metadata.m30_bars;
      const exact = node("pre", JSON.stringify(metadata, null, 2));
      const rows = node("div", "", "exact-bars");
      for (const bar of bars) rows.append(node("p", `${evidenceFrame === "D1" ? `${bar.session_date} · 市场交易日` : `${stamp(bar.interval_start, decision.market)} → ${stamp(bar.interval_end, decision.market)}`} | O ${bar.open} H ${bar.high} L ${bar.low} C ${bar.close} V ${display(bar.volume)}`));
      $("evidence-facts").replaceChildren(node("p", "源质量 / 排除的部分周期 / 缺失计数 / 延迟 / 调整事实（原值）", "note"), exact, rows);
    } catch (error) { clearEvidence(`冻结证据不可用：${error.message}`); }
  }
  function mode(frozen) {
    frozenMode = frozen;
    $("mode-current").setAttribute("aria-pressed", String(!frozen));
    $("mode-frozen").setAttribute("aria-pressed", String(frozen));
    $("frozen-section").hidden = !frozen;
    for (const part of document.querySelectorAll(".current-chart-part")) part.hidden = frozen;
    for (const line of priceLines) frozenCandles?.removePriceLine(line);
    priceLines = [];
    $("overlay-labels").replaceChildren();
    if (frozen) drawEvidence();
  }
  async function attachEvidence(item, token, nav) {
    try {
      const run = await get(`analyses/${encodeURIComponent(item.analysis_run_id)}`);
      const evidence = parseRun(run, { ...item, status: "SUCCEEDED" });
      if (token !== detailGeneration || nav !== navigation || decision?.decision_id !== item.decision_id) return;
      snapshot = evidence;
      $("evidence-status").textContent = "冻结输入已按 Decision / Run / 请求身份关联；切换冻结证据查看";
      $("decision-audit").textContent = JSON.stringify({ decision: item, run }, null, 2);
      drawEvidence();
    } catch (error) {
      if (token === detailGeneration && nav === navigation) clearEvidence(`冻结输入证据不可用：${error.message}`);
    }
  }
  async function selectDecision(item, explicit = true) {
    if (!security || !uuid(item.decision_id)) return;
    if (explicit) selectionIntent += 1;
    const token = ++detailGeneration, nav = navigation;
    const expected = { ...item, security_id: security.id };
    decision = null;
    historical = explicit;
    earlier = false;
    clearEvidence("正在读取所选 Decision 的冻结证据…");
    renderDecision();
    try {
      const loaded = await get(`decisions/${encodeURIComponent(item.decision_id)}`);
      assertDecision(loaded, expected);
      if (token !== detailGeneration || nav !== navigation) return;
      decision = loaded;
      renderDecision();
      mode(true);
      await attachEvidence(loaded, token, nav);
    } catch (error) {
      if (token === detailGeneration && nav === navigation) {
        $("decision-heading").textContent = `Decision 呈现失败：${error.message}`;
        clearEvidence("所选 Decision 不可验证，未使用其他证据");
      }
    }
  }
  async function reloadHistory() {
    const token = ++historyGeneration, nav = navigation;
    history = [];
    $("decision-history").replaceChildren();
    if (!security) { $("history-status").textContent = "请选择证券"; return; }
    const id = security.id, strategy = $("history-strategy").value;
    $("history-status").textContent = "读取成功历史…";
    try {
      const result = await get(`securities/${encodeURIComponent(id)}/decisions?limit=20${strategy ? `&strategy_id=${encodeURIComponent(strategy)}` : ""}`);
      if (token !== historyGeneration || nav !== navigation) return;
      if (!Array.isArray(result.items) || result.items.length > 20 || result.items.some((item) =>
        !same(item.security_id, id) || !uuid(item.decision_id) || !uuid(item.analysis_run_id)
        || (strategy && !same(item.strategy_id, strategy)) || !Number.isInteger(item.revision_no)
        || item.revision_no < 1 || !hash(item.snapshot_hash) || !identifier(item.model_id)
        || !identifier(item.strategy_id) || !item.entry_advisory || !item.one_line_thesis
        || (item.status != null && item.status !== "SUCCEEDED") || item.analysis_status != null)) throw new Error("历史响应身份或范围不匹配");
      history = result.items;
      const rows = history.map((item) => {
        const button = node("button", "", "history-row");
        button.type = "button";
        button.dataset.decisionId = item.decision_id;
        button.append(node("strong", `${item.strategy_id} · 修订 ${item.revision_no} · ${display(item.entry_advisory)}`),
          node("span", `${stamp(item.created_at, item.market)} · ${modelName(item.model_id)}`), node("span", item.one_line_thesis));
        button.addEventListener("click", () => selectDecision(item));
        return button;
      });
      $("decision-history").replaceChildren(...rows);
      $("history-status").textContent = rows.length ? `已显示 ${rows.length} 条成功 Decision；不是全部 Run 记录` : "此筛选下暂无成功 Decision";
    } catch (error) {
      if (token === historyGeneration && nav === navigation) $("history-status").textContent = `历史不可用：${error.message}`;
    }
  }
  async function showRun(id, expected = {}) {
    const token = ++runGeneration, nav = navigation;
    $("known-run-detail").textContent = "—";
    if (!uuid(id)) { $("known-run-status").textContent = "请输入合法 Run UUID"; return; }
    $("known-run-status").textContent = "读取已知 Run…";
    try {
      const run = await get(`analyses/${encodeURIComponent(id)}`);
      parseRun(run, { ...expected, analysis_run_id: id });
      if (token !== runGeneration || nav !== navigation) return;
      $("known-run-status").textContent = `${run.symbol} · ${modelName(run.model_id)} · ${run.strategy_id} · ${run.status} · ${run.failure_kind || "无提供方失败"}`;
      $("known-run-detail").textContent = JSON.stringify(run, null, 2);
    } catch (error) {
      if (token === runGeneration && nav === navigation) $("known-run-status").textContent = `Run 不可用：${error.message}`;
    }
  }
  const failures = {
    CONFIGURATION_ERROR: "所选模型凭据缺失或不可用；请配置此模型 API Key",
    PROVIDER_UNAVAILABLE: "推理提供方不可用", PROVIDER_REFUSAL: "推理提供方拒绝回答",
    INVALID_STRUCTURED_OUTPUT: "提供方输出不符合结构约定",
  };
  $("analyze-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (inFlight) return;
    const model = $("model-id").value, strategy = $("strategy-id").value;
    if (!security || !uuid(security.id) || !identifier(model) || !identifier(strategy)
      || !selectedModel()?.credential_configured || !configuration.strategies.some((item) => item.strategy_id === strategy)) {
      state("无法提交：请选择证券、已注册策略，并配置所选模型的凭据。");
      return;
    }
    const payload = Object.freeze({ security_id: security.id, model_key: model, strategy_id: strategy, web_research: $("web-research").checked });
    const attempt = { payload, symbol: security.display_symbol, nav: navigation, intent: selectionIntent };
    inFlight = attempt; // Global page guard acquired synchronously, before the first await.
    updateButton();
    const target = `${attempt.symbol} · ${modelName(model)} · ${strategy}`;
    state(`正在分析：${target}。已提交的目标不会随界面选择改变。`);
    if (decision) { earlier = true; renderHeading(); }
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 180000);
    try {
      // The sole Analyze POST source. No other event invokes this handler.
      const response = await fetch("/api/v1/paqs-e/analyses", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload), signal: controller.signal,
      });
      const body = await response.json();
      if (response.status === 201 && body.status === "SUCCEEDED") {
        assertDecision(body, { security_id: payload.security_id, model_id: payload.model_key, strategy_id: payload.strategy_id });
        state(`已提交成功 Decision：${target} · 修订 ${body.revision_no}。${attempt.nav !== navigation ? "当前已切换证券；请回到原证券查看历史。" : ""}`);
        if (attempt.nav === navigation && security?.id === payload.security_id) {
          if (attempt.intent === selectionIntent) {
            const token = ++detailGeneration;
            decision = body; historical = false; earlier = false;
            clearEvidence("正在读取本次 Run 的冻结证据…");
            renderDecision(); mode(true);
            void attachEvidence(body, token, navigation);
          }
          void reloadHistory();
        }
      } else if ([502, 503].includes(response.status)
        && ["PROVIDER_FAILED", "VALIDATION_FAILED"].includes(body.analysis_status)
        && body.status === response.status && uuid(body.analysis_run_id)
        && body.analysis_run?.analysis_run_id === body.analysis_run_id
        && body.analysis_run.status === body.analysis_status
        && body.analysis_run.failure_kind === body.failure_kind
        && body.analysis_run.validator_version === body.validator_version
        && ((body.analysis_status === "VALIDATION_FAILED" && response.status === 502 && Array.isArray(body.validation_issues))
          || (body.analysis_status === "PROVIDER_FAILED" && failures[body.failure_kind]
            && response.status === (["CONFIGURATION_ERROR", "PROVIDER_UNAVAILABLE"].includes(body.failure_kind) ? 503 : 502)))) {
        const message = body.analysis_status === "VALIDATION_FAILED"
          ? `确定性校验失败 · ${body.validator_version} · ${JSON.stringify(body.validation_issues)}` : failures[body.failure_kind];
        state(`${target}：${message}。本次没有新 Decision。Run ${body.analysis_run_id}`);
        if (attempt.nav === navigation) {
          $("known-run-id").value = body.analysis_run_id;
          void showRun(body.analysis_run_id, { security_id: payload.security_id, model_id: payload.model_key, strategy_id: payload.strategy_id, status: body.analysis_status });
        }
      } else if ([404, 409, 422, 500].includes(response.status) && body.status === response.status && typeof body.code === "string") {
        state(`${target}：${response.status === 500 ? "账本证据无法提交或验证" : "分析前提失败"} · ${body.code} · ${body.detail || ""}。没有确认新的 Decision。`);
      } else throw new Error("未确认响应");
    } catch (_error) {
      state(`${target}：结果未知，响应未能确认（可能断连、超时、格式或身份异常）。服务端可能已保存结果。请检查成功历史或已知 Run，再决定是否显式发起新尝试；不会自动重试。`);
    } finally {
      window.clearTimeout(timeout);
      if (inFlight === attempt) inFlight = null;
      updateButton();
    }
  });

  function onSecurity(item) {
    security = item;
    navigation += 1; selectionIntent += 1; detailGeneration += 1; runGeneration += 1;
    decision = null; historical = false; earlier = false;
    clearEvidence(); renderDecision(); mode(false);
    $("analysis-security").textContent = item ? `${item.display_symbol} · ${item.market} · ${item.currency}` : "请选择证券";
    $("known-run-id").value = "";
    $("known-run-status").textContent = ""; $("known-run-detail").textContent = "—";
    if (!inFlight) state("尚未为当前证券发起新分析；可读取成功历史。");
    updateButton(); void reloadHistory();
  }
  document.addEventListener("security-selected", (event) => onSecurity(event.detail));
  $("watchlist-toggle").addEventListener("click", () => {
    const expanded = $("watchlist-toggle").getAttribute("aria-expanded") !== "true";
    $("watchlist-toggle").setAttribute("aria-expanded", String(expanded));
    $("watchlist-panel").classList.toggle("mobile-open", expanded);
  });
  $("mode-current").addEventListener("click", () => mode(false));
  $("mode-frozen").addEventListener("click", () => mode(true));
  for (const button of document.querySelectorAll("[data-evidence-frame]")) button.addEventListener("click", () => {
    evidenceFrame = button.dataset.evidenceFrame;
    for (const other of document.querySelectorAll("[data-evidence-frame]")) other.setAttribute("aria-pressed", String(other === button));
    drawEvidence();
  });
  $("reload-history").addEventListener("click", reloadHistory);
  $("history-strategy").addEventListener("change", reloadHistory);
  $("latest-decision").addEventListener("click", () => {
    if (history.length) void selectDecision(history[0]);
  });
  $("known-run-form").addEventListener("submit", (event) => {
    event.preventDefault(); void showRun($("known-run-id").value);
  });
  function theme(light) {
    document.documentElement.dataset.theme = light ? "light" : "dark";
    $("theme-toggle").textContent = light ? "深色模式" : "浅色模式";
    chartTheme(chart, light); chartTheme(frozenChart, light);
    try { localStorage.setItem("paqs-e-theme", light ? "light" : "dark"); } catch (_error) { /* Optional preference. */ }
  }
  $("theme-toggle").addEventListener("click", () => theme(document.documentElement.dataset.theme !== "light"));
  try { theme(localStorage.getItem("paqs-e-theme") === "light"); } catch (_error) { theme(false); }
  const selectedModel = () => configuration?.models.find((item) => item.model_key === $("model-id").value);
  const modelName = (id) => configuration?.models.find((item) => item.model_key === id)?.display_name || id;
  let credentialModel = null, credentialBusy = false;
  function modelChanged() {
    const item = selectedModel();
    $("web-research").disabled = !item?.web_research_supported;
    $("web-research").checked = !!item?.web_research_supported;
    $("research-status").textContent = item?.web_research_supported
      ? ""
      : "此模型当前未启用可审计联网研究；可关闭研究后分析。";
    $("configuration-status").textContent = item?.credential_configured
      ? "凭据已存在（仅确认存在，未验证有效性、模型权限或连接）。"
      : "未配置此模型凭据。请配置 API Key；行情与历史仍可读取。";
    updateButton();
  }
  $("model-id").addEventListener("change", modelChanged);
  $("configure-credential").addEventListener("click", async () => {
    if (!selectedModel() || credentialBusy) return;
    credentialModel = selectedModel();
    $("credential-secret").value = "";
    $("credential-service").textContent = `${credentialModel.display_name} · ${credentialModel.credential_label}`;
    $("credential-status").textContent = "";
    $("credential-dialog").showModal();
    try {
      const status = await get(`credentials/${encodeURIComponent(credentialModel.model_key)}`);
      $("credential-status").textContent = status.credential_source === "server_environment_read_only"
        ? "服务器环境变量只读回退已存在；删除本地凭据不会删除环境变量。"
        : status.secure_storage_available ? "Windows 安全存储可用。" : "操作系统安全存储不可用；不能保存。";
    } catch (_error) { $("credential-status").textContent = "无法读取凭据状态。"; }
  });
  $("credential-close").addEventListener("click", () => $("credential-dialog").close());
  $("credential-dialog").addEventListener("close", () => { $("credential-secret").value = ""; });
  async function mutateCredential(method) {
    if (credentialBusy || !credentialModel) return;
    credentialBusy = true;
    const key = credentialModel.model_key;
    const body = method === "PUT" ? { secret: $("credential-secret").value } : {};
    $("credential-save").disabled = true; $("credential-delete").disabled = true;
    try {
      const response = await fetch(`/api/v1/paqs-e/credentials/${encodeURIComponent(key)}`, {
        method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error("Credential mutation failed");
      $("credential-secret").value = "";
      const value = await get("configuration");
      configuration.models = value.models;
      $("configuration-status").textContent = selectedModel()?.credential_configured ? "凭据已存在；权限与余额未验证。" : "未配置此模型凭据。";
      $("credential-status").textContent = method === "PUT" ? "已安全保存；未验证权限或余额。" : "已删除本地凭据；服务器环境变量回退不受影响。";
    } catch (_error) { $("credential-status").textContent = "操作未能确认；请检查安全存储状态后手动重试。"; }
    finally {
      delete body.secret;
      credentialBusy = false; $("credential-save").disabled = false; $("credential-delete").disabled = false;
      updateButton();
    }
  }
  $("credential-form").addEventListener("submit", (event) => { event.preventDefault(); void mutateCredential("PUT"); });
  $("credential-delete").addEventListener("click", () => { void mutateCredential("DELETE"); });
  async function configure() {
    try {
      const value = await get("configuration");
      if (!Array.isArray(value.models) || !value.models.length
        || !value.models.some((item) => item.model_key === value.default_model_key)
        || new Set(value.models.map((item) => item.model_key)).size !== value.models.length
        || value.models.some((item) => !identifier(item.model_key) || typeof item.display_name !== "string"
          || typeof item.credential_configured !== "boolean" || typeof item.web_research_supported !== "boolean")
        || !Array.isArray(value.strategies) || !value.strategies.length
        || !value.strategies.some((item) => item.strategy_id === value.default_strategy_id)
        || new Set(value.strategies.map((item) => item.strategy_id)).size !== value.strategies.length
        || value.strategies.some((item) => !identifier(item.strategy_id) || !hash(item.content_sha256)
          || typeof item.display_name !== "string" || !item.display_name.trim())) throw new Error("配置格式无效");
      configuration = value;
      for (const item of value.strategies) {
        const option = node("option", `${item.display_name} · ${item.strategy_id}`);
        option.value = item.strategy_id; $("strategy-id").append(option);
        const filter = option.cloneNode(true); $("history-strategy").append(filter);
      }
      $("strategy-id").value = value.default_strategy_id; $("strategy-id").disabled = false;
      for (const item of value.models) {
        const option = node("option", item.display_name);
        option.value = item.model_key; $("model-id").append(option);
      }
      $("model-id").value = value.default_model_key; $("model-id").disabled = false;
      modelChanged();
    } catch (_error) { $("configuration-status").textContent = "服务器策略配置不可用，请检查注册文件后重启。未提供替代策略。"; }
    updateButton();
  }
  void configure();
  if (security) onSecurity(security);
  fetch("/health").then((response) => { $("service-health").textContent = response.ok ? "● 本地服务正常" : "服务异常"; })
    .catch(() => { $("service-health").textContent = "服务不可用"; });
})();
