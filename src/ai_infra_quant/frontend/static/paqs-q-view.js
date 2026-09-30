/* Deterministic presentation of saved fields only. No strategy or geometry calculation. */
(() => {
  "use strict";
  const node = (tag, text = "", cls = "") => {
    const el = document.createElement(tag); el.textContent = text; el.className = cls; return el;
  };
  const STATES = {
    AVAILABLE: "可用", INSUFFICIENT: "证据不足，暂无法判断", UNAVAILABLE: "不可用",
    INVALID: "输入或结果无效", ERROR: "执行错误", FAILED: "失败", SUCCEEDED: "已完成",
    CREATED: "形态已建立", OBSERVED: "已观察", TRIGGER_PENDING: "等待触发",
    FOLLOW_THROUGH_PENDING: "等待延续确认", FOLLOW_THROUGH_CONFIRMED: "延续已确认",
    FOLLOW_THROUGH_NONE: "窗口内未确认延续", FOLLOW_THROUGH_FAILED: "延续失败",
    ENTRY_PENDING_REVALIDATION: "确认评估通过，待下一开盘验证", LONG_READY: "符合入场规则",
    OBSERVATIONAL_LONG_QUALIFIED: "观察性规则满足，未获正式入场资格",
    VALID_SETUP_BUT_POOR_ENTRY: "形态有效，入场条件不佳", NO_TRADE: "规则未满足，不形成入场资格",
    INVALIDATED: "形态已失效", EXPIRED: "形态已过期", UNDETERMINED: "无法判断",
    EXIT_IF_HELD: "若持有：硬失效，退出条件已触发", TARGET_REACHED_REVIEW: "若持有：目标已触及，需复核",
    HOLD_WITH_WARNING: "若持有：延续失败，需警惕", THESIS_VALID: "若持有：形态依据仍有效",
    BULL_TREND: "上升趋势", BEAR_TREND: "下降趋势", RANGE: "区间", UNCERTAIN: "背景不确定",
    TRANSITION: "趋势转换", UP: "向上", DOWN: "向下", HIGH: "高点", LOW: "低点",
    MAJOR: "主要结构", MICRO: "微观结构", SUPPORT: "支撑", RESISTANCE: "阻力",
    HH: "高点抬高", LH: "高点降低", EH: "等高", HL: "低点抬高", LL: "低点降低", EL: "等低",
    CANDIDATE: "候选", CONFIRMED: "已确认", PENDING: "等待确认", START: "开始",
    HOLD: "保持", FAILURE: "失败", NONE: "未形成", CANCELLED: "已取消",
    ATTEMPT: "突破尝试", BREAKOUT: "向上突破", BREAKDOWN: "向下突破", EXCURSION: "越界触价",
    FAILED_BREAK: "突破尝试失败", BREAKOUT_FAILURE: "有效突破后失败", RETEST: "回踩 / 回抽",
    PRICE_PATTERN: "价格形态", PRICE_TRIGGER_CANDIDATE: "价格触发候选", FOLLOW_THROUGH: "后续延续",
    EVENT_INVALIDATED: "事件失效", COMPLETE: "完整", PARTIAL: "部分覆盖", UNKNOWN: "未知",
    TREND_PULLBACK_LONG: "趋势回踩做多", RANGE_FAILED_BREAKDOWN_LONG: "区间下破失败做多",
    RIGHT_SIDE_BREAKOUT_LONG: "右侧突破做多", OBSERVATIONAL: "观察性分析", AS_OF: "严格历史时点",
  };
  const REASONS = {
    SCHEDULED_CALENDAR_EXCLUDES_EMERGENCY_CLOSURES: "日历包含计划交易日、周末和假日，但不认证临时休市或历史日历版本",
    NO_QUALIFIED_SETUP: "当前没有符合规则的候选形态",
    UPSTREAM_STRUCTURE_UNAVAILABLE: "上游结构结果不可用，价格事件无法继续判断",
    W1_COMPLETED_CONTEXT_STALE_OR_MISSING: "周线已完成背景缺失或过旧", W1_CONTEXT_UNAVAILABLE: "周线背景不可用",
    D1_ATR_UNAVAILABLE: "日线 ATR 尚不可用", D1_CONTEXT_UNAVAILABLE: "日线背景不可用",
    W1_CONTEXT_QUALITY_INSUFFICIENT: "周线背景质量不足", TARGET_COVERAGE_INSUFFICIENT: "目标结构覆盖不足",
    TARGET_UNAVAILABLE: "没有可用目标", RISK_GEOMETRY_INVALID: "风险几何不满足规则",
    ENTRY_INSIDE_RESISTANCE: "入场参考位于阻力区内", SETUP_D1_CLOCK_EXPIRED: "形态的日线有效窗口已结束",
    SETUP_CREATION_BAR_ALREADY_INVALIDATED: "形态建立时的日线已经触发失效",
    FROZEN_SETUP_SOURCE: "形态来源已冻结", RANGE_RECLAIM_SOURCE_OR_W1_BLOCKED: "区间收复来源或周线条件未满足",
    SETUP_CLOCK_CALENDAR_OR_D1_BAR_INSUFFICIENT: "形态计时所需的日历或日线不足",
    D1_CLOSE_BELOW_FROZEN_ANCHOR: "日线收盘低于冻结锚点", NEXT_M30_BAR_MISSING: "缺少下一根常规半小时行情",
    ENTRY_REFERENCE_UNAVAILABLE_AT_OPEN: "开盘时尚无可用的独立价格证据",
    ENTRY_REFERENCE_PRICE_BASIS_CONFLICT: "独立开盘证据的价格口径冲突",
    W1_CONTEXT_BLOCKED_AT_ENTRY: "开盘验证时周线条件未满足", D1_BEAR_CONTEXT_AT_ENTRY: "开盘验证时日线为下降背景",
    ENTRY_INSIDE_ORIGINAL_T1: "入场参考进入原目标区", ORIGINAL_T1_OVERRUN: "入场参考已越过原目标",
    T1_NOT_ABOVE_ENTRY: "第一目标未高于入场参考", WAIT_RETEST: "等待回踩确认", RR_T1_BELOW_2: "第一目标盈亏比低于规则要求",
    ALL_ENTRY_GATES_PASS: "已记录的入场规则均通过", LATE_OPEN_REFERENCE_NOT_OPEN_TIME_QUALIFICATION: "迟到的开盘证据不能回填当时资格",
    NEXT_REGULAR_M30_OPEN_UNKNOWN: "下一常规半小时开盘尚未知晓", W1_CONTEXT_NO_LONGER_ALLOWED: "周线背景不再满足形态要求",
    M30_FT_WINDOW_END: "半小时延续窗口结束", WAIT_M30_TRIGGER: "等待半小时触发",
    SETUP_BOUND_M30_MICRO: "半小时微观触发已关联此形态", SETUP_BOUND_M30_STRONG: "半小时强触发已关联此形态",
    M30_Q_PLUS_1_TO_Q_PLUS_3: "检查触发后的第 1 至第 3 根半小时行情",
    HISTORICAL_PRICE_AVAILABILITY_UNKNOWN: "缺少价格在历史时点已知的证据",
    HISTORICAL_CALENDAR_AVAILABILITY_UNKNOWN: "缺少日历事实在历史时点已知的证据",
    CLOSED_DAY_FACTS_UNAVAILABLE: "缺少闭市日期的事实", DERIVED_BAR_SOURCE_RETRIEVAL_UNAVAILABLE: "派生行情缺少来源获取证据",
    INDEPENDENT_M30_OPEN_REFERENCE_MISSING: "缺少独立的下一常规半小时开盘证据",
    ADJUSTMENT_HISTORY_NOT_POINT_IN_TIME: "复权数据缺少严格历史版本证明", CURRENT_QFQ_NOT_POINT_IN_TIME: "当前前复权数据不是严格历史时点证据",
    M30_COVERAGE_INCOMPLETE: "半小时行情覆盖不完整", CALENDAR_SOURCE_NOT_AVAILABLE: "日历来源不可用",
    CALENDAR_FUTURE_RETRIEVAL_EXCLUDED: "已排除分析时点之后获取的日历", CALENDAR_DATE_FACTS_MISSING: "缺少日期日历事实",
    INPUT_MISSING: "周期输入缺失", SESSION_FACT_MISSING: "缺少交易时段事实", OBSERVATIONAL_NOT_POINT_IN_TIME: "观察性数据未认证严格历史可知性",
    NO_COMPLETED_BARS: "没有已完成行情", PREVIOUS_BAR_NOT_KNOWN_BEFORE_NEXT_START: "前一根行情在下一根开始前尚不可知",
    INCOMPLETE_BAR_COVERAGE: "行情覆盖不完整", ADJUSTMENT_EVIDENCE_UNKNOWN: "复权证据未知",
    STRICT_QUALITY_REQUIRED: "严格模式需要完整质量证据", STRICT_ADJUSTMENT_UNPROVEN: "严格模式的复权来源未获证明",
    HISTORICAL_EVIDENCE_REFERENCES_REQUIRED: "缺少历史证据引用", HISTORICAL_PRICE_NOT_KNOWN_AT_COMPLETION: "行情完成时尚无价格可知证据",
    STRICT_CALENDAR_UNPROVEN: "严格日历未获证明", CALENDAR_MISSING: "缺少日历", CALENDAR_DATE_MISSING: "日历缺少必要日期",
    CALENDAR_UNKNOWN: "日历事实未知", WEEK_INCOMPLETE: "周线尚未完成", CALENDAR_NOT_STRICT: "日历不满足严格模式",
    HISTORICAL_CALENDAR_NOT_KNOWN_AT_COMPLETION: "行情完成时日历事实尚不可知", MISSING_EXPECTED_WEEK: "缺少应有周线", MISSING_EXPECTED_BAR: "缺少应有行情",
    NO_TRACEABLE_SETUP: "没有可追溯的形态", MULTIPLE_INDEPENDENT_SETUPS: "多个独立形态分别判断，不合成持有结论",
    FROZEN_TARGET_BINDING_UNAVAILABLE: "尚无有效的候选目标绑定", TARGET_STRUCTURE_NOT_KNOWN_AT_BINDING: "目标绑定时来源结构尚未知晓",
    CONFLICTING_STAGE_A_TARGET_FOR_CANDIDATE: "同一候选的确认目标冲突", CONFLICTING_OR_FUTURE_STAGE_B_TARGET: "开盘目标冲突或包含未来结构",
    MULTIPLE_CANDIDATE_TARGETS_AMBIGUOUS: "多个候选的有效目标冲突，无法确定唯一持有目标", FROZEN_TARGET_UNAVAILABLE: "冻结目标不可用",
    COMPLETE_M30_TARGET_EVIDENCE_MISSING: "缺少完整半小时目标观察证据", M30_OR_TARGET_BINDING_NOT_AVAILABLE_AS_OF: "分析时点无法使用目标绑定或半小时证据",
    POST_TARGET_COMPLETE_M30_EVIDENCE_MISSING: "目标绑定之后尚无完整半小时行情",
    POST_TARGET_M30_CALENDAR_OR_BUCKET_COVERAGE_UNPROVEN: "目标绑定后的日历或半小时覆盖未获证明",
    FROZEN_SETUP_D1_CLOSE_HARD_INVALIDATION: "日线收盘触发冻结形态的硬失效",
    W1_CONTEXT_NO_LONGER_ALLOWED_HOLDER_UNDETERMINED: "周线背景不再允许原形态，持有结论无法确定",
    SETUP_EXPIRED_NO_CURRENT_THESIS: "形态已过期，没有当前持有依据", FROZEN_T1_TOUCHED_AFTER_SETUP_BINDING: "有效目标绑定后的完成半小时行情已触及第一目标",
    SETUP_FOLLOW_THROUGH_FAILED_WITHOUT_HARD_INVALIDATION: "延续失败，但尚未触发硬失效",
    TRACEABLE_SETUP_NO_HARD_INVALIDATION_OR_T1_TOUCH: "可追溯形态尚未硬失效，完整观察区间未触及第一目标",
    LATEST_SETUP_STATUS_NOT_HOLDER_THESIS_EVIDENCE: "最新形态状态不足以支持持有判断",
  };
  const state = (code) => STATES[code] || (code ? `未识别状态：${code}` : "未提供");
  const reason = (code) => {
    if (REASONS[code]) return REASONS[code];
    const period = /^(W1|D1|M30)_(.+)$/.exec(code);
    if (period && REASONS[period[2]]) return `${period[1]} · ${REASONS[period[2]]}`;
    if (/^CALENDAR_DATE_FACTS_MISSING:\d+$/.test(code)) return `缺少 ${code.split(":")[1]} 个日期的日历事实`;
    if (/^SETUP_RESULT_(INSUFFICIENT|INVALID)$/.test(code)) return `形态结果：${state(code.slice(13))}`;
    return `未识别的原因：${code}`;
  };
  const time = (raw) => {
    if (!raw) return "未提供";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return `时间无法解析：${raw}`;
    return new Intl.DateTimeFormat("zh-CN", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).format(d) + " UTC+8";
  };
  const exactPrice = (value) => typeof value === "string" && /^-?\d+(\.\d+)?$/.test(value) ? value : "未形成 / 无法评估";
  const stamp = (raw) => { const el = node("time", time(raw)); if (raw) { el.dateTime = raw; el.title = raw; } return el; };
  function reasons(codes = [], limit = 3) {
    const root = node("div"), list = node("ul", "", "q-reasons");
    const unique = [...new Set(codes)];
    unique.slice(0, limit).forEach(code => { const li = node("li", reason(code)); li.title = code; list.append(li); });
    if (unique.length) root.append(list);
    if (unique.length > limit) { const more = node("details"); more.append(node("summary", `其余 ${unique.length - limit} 项原因`), reasons(unique.slice(limit), Infinity)); root.append(more); }
    return root;
  }
  function technical(title, value) {
    const el = node("details", "", "q-technical"), text = JSON.stringify(value, null, 2);
    const copy = node("button", "复制 JSON"); copy.type = "button";
    copy.addEventListener("click", async () => { try { await navigator.clipboard.writeText(text); copy.textContent = "已复制"; } catch { copy.textContent = "复制不可用，请选中文本复制"; } });
    el.append(node("summary", title), copy, node("pre", text)); return el;
  }
  function table(headers, rows) {
    const wrap = node("div", "", "q-table-wrap"), el = node("table", "", "q-table");
    const head = node("tr"); headers.forEach(v => head.append(node("th", v))); const thead = node("thead"); thead.append(head); el.append(thead);
    const body = node("tbody"); rows.forEach(row => { const tr = node("tr"); row.forEach(v => tr.append(node("td", v ?? "未提供"))); body.append(tr); });
    el.append(body); wrap.append(el); return wrap;
  }
  function groups(payload) {
    const facts = (payload.setup?.facts || []).map((fact, index) => ({fact, index})).sort((a,b) => (Date.parse(a.fact.effective_at) - Date.parse(b.fact.effective_at)) || a.index-b.index).map(x=>x.fact);
    const candidates = new Map(), terminals = new Map();
    facts.forEach(f => {
      if (["INVALIDATED", "EXPIRED"].includes(f.status) && !f.candidate_key) terminals.set(f.setup_key, f);
      if (!f.candidate_key) return;
      const key = `${f.setup_key}/${f.candidate_key}`;
      if (!candidates.has(key)) candidates.set(key, []);
      candidates.get(key).push(f);
    });
    return [...candidates.values()].map((items, index) => ({ items, latest: items.at(-1), terminal: terminals.get(items[0].setup_key), number: index + 1 }));
  }
  const currentFact = group => group.terminal || group.latest;
  const ended = f => ["INVALIDATED", "EXPIRED"].includes(f?.status);
  function stage(f, items = []) {
    if (!f.candidate_key) return "形态生命周期（无入场候选）";
    if (f.status === "ENTRY_PENDING_REVALIDATION") return "确认后指示性评估 · Stage A";
    if (f.entry_reference_price_at || ["LONG_READY", "OBSERVATIONAL_LONG_QUALIFIED"].includes(f.status)
      || items.some(a => a.status === "ENTRY_PENDING_REVALIDATION" && Date.parse(a.effective_at) < Date.parse(f.effective_at))) return "下一常规 M30 开盘验证 · Stage B";
    return "候选事实（阶段以原始记录为准）";
  }
  function factLabel(f, items = []) {
    const el = node("p", `${stage(f, items)} · ${time(f.effective_at)}`, "q-stamp");
    el.dataset.factKey = f.fact_key || ""; el.dataset.effectiveAt = f.effective_at || "";
    return el;
  }
  function setupGroups(p) {
    const bySetup = new Map();
    [...(p.setup?.facts || [])].sort((a,b)=>Date.parse(a.effective_at)-Date.parse(b.effective_at)).forEach(f=>{
      if (!bySetup.has(f.setup_key)) bySetup.set(f.setup_key, []);
      bySetup.get(f.setup_key).push(f);
    });
    return [...bySetup.values()];
  }
  function headline(record) {
    const p = record.payload || {};
    if (record.status !== "AVAILABLE") return state(record.status);
    const candidates = groups(p), states = candidates.map(g => currentFact(g).status);
    if (states.includes("LONG_READY") && p.qualification_mode === "AS_OF" && p.setup?.strict_confirmation === true) return "符合入场规则";
    if (states.includes("LONG_READY") || states.includes("OBSERVATIONAL_LONG_QUALIFIED")) return "观察性规则满足，资格未认证";
    if (states.includes("ENTRY_PENDING_REVALIDATION")) return "确认评估通过，待开盘验证";
    if (states.some(s => ["TRIGGER_PENDING", "FOLLOW_THROUGH_PENDING", "FOLLOW_THROUGH_CONFIRMED"].includes(s))) return "候选仍在等待规则确认";
    return "规则未满足，尚无入场资格";
  }
  function prices(fact, valid = true) {
    const grid = node("dl", "", "q-prices");
    const rows = [["入场参考", fact?.reference_price], ["失效参考", fact?.risk_reference_price], ["第一目标", fact?.target1?.effective_price], ["盈亏比 · T1", fact?.rr_t1]];
    rows.forEach(([title, value]) => { const cell = node("div"); cell.append(node("dt", title), node("dd", valid ? exactPrice(value) : "未形成 / 无法评估")); grid.append(cell); }); return grid;
  }
  const validGeometry = f => ["ENTRY_PENDING_REVALIDATION", "LONG_READY", "OBSERVATIONAL_LONG_QUALIFIED", "VALID_SETUP_BUT_POOR_ENTRY"].includes(f?.status);
  function candidate(group, compact = false, strictAllowed = false) {
    const f = currentFact(group), latest = group.latest;
    const entryLabel = code => code === "LONG_READY" && !strictAllowed ? "资格声明未认证，不构成正式入场资格" : state(code);
    const root = node("section", "", "q-candidate");
    root.dataset.candidateKey = latest.candidate_key; root.dataset.setupKey = latest.setup_key;
    root.append(node("h3", `候选 ${group.number} · ${state(latest.family)}`), node("p", entryLabel(f.status)), factLabel(f, group.items));
    if (f.status === "LONG_READY") root.append(node("p", "不代表已成交", "note"));
    if (compact) {
      root.append(prices(f, validGeometry(f)), reasons(f.reasons, 1));
    } else {
      const a = group.items.filter(x => x.status === "ENTRY_PENDING_REVALIDATION").at(-1);
      const b = group.items.filter(x => a && Date.parse(x.effective_at) >= Date.parse(a.effective_at)
        && ["LONG_READY", "OBSERVATIONAL_LONG_QUALIFIED", "VALID_SETUP_BUT_POOR_ENTRY", "NO_TRADE"].includes(x.status)).at(-1);
      root.append(reasons(f.reasons));
      if (group.terminal) root.append(node("p", "该形态已结束。以下阶段事实仅供历史复盘，不代表当前资格。", "q-limit"));
      for (const [title, item] of [["确认后指示性评估 · Stage A", a], ["下一常规 M30 开盘验证 · Stage B", b]]) {
        root.append(node("h4", title));
        if (!item) { root.append(node("p", title.includes("Stage A") ? "尚无通过确认的指示性评估。失败或等待原因见上方最新事实。" : "尚无此候选的下一开盘验证事实；不能用已完成 K 线的 open 回填。", "note")); continue; }
        root.append(node("p", entryLabel(item.status)), stamp(item.effective_at), prices(item, validGeometry(item)), reasons(item.reasons));
        if (item.target2 || item.rr_t2) root.append(table(["第二目标", "盈亏比 · T2"], [[validGeometry(item) ? exactPrice(item.target2?.effective_price) : "无法评估", validGeometry(item) ? exactPrice(item.rr_t2) : "无法评估"]]));
        root.append(technical("阶段事实与精确时间", item));
      }
      const history = node("details", "", "q-candidate-history");
      history.append(node("summary", "候选完整事实与历史原因（按时间）"));
      group.items.forEach(item=>{
        const row = node("section"); row.dataset.factKey = item.fact_key || "";
        row.append(factLabel(item, group.items), node("p", entryLabel(item.status)), reasons(item.reasons, Infinity));
        history.append(row);
      });
      root.append(history);
    }
    return root;
  }
  function currentIssues(p) {
    const result = [];
    for (const layer of ["context", "event"]) for (const [tf, value] of Object.entries(p[layer] || {})) {
      if (value && typeof value === "object" && value.status && value.status !== "AVAILABLE") result.push({label: `${tf} · ${layer === "context" ? "市场背景" : "价格事件"}`, status: value.status, codes: value.reason_codes || []});
    }
    // AVAILABLE Setup.reasons is a whole-replay diagnostic set, without candidate/time scope.
    if (p.setup?.status && p.setup.status !== "AVAILABLE") result.push({label: "形态输入", status: p.setup.status, codes: p.setup.reasons || []});
    const d1 = p.context?.D1, frame = d1?.evidence?.frames?.at(-1);
    if (d1?.status === "AVAILABLE" && frame?.atr === null) result.push({label: "日线最新完成行情 · ATR 字段未形成", codes: ["D1_ATR_UNAVAILABLE"], at: p.q_inputs?.D1?.payload?.bars?.[frame.index]?.completed_at});
    return result;
  }
  function historicalDiagnostics(p) {
    const el = node("details", "", "q-run-diagnostics");
    el.append(node("summary", "历史回放诊断 · 非当前结论"), node("p", "以下原因是整段回放的汇总，未保存候选、阶段或发生时间关联；不能当作当前失败原因，也不能强行归给某个候选。候选原因见各自事实。", "note"), reasons(p.setup?.reasons, Infinity));
    if (p.setup?.reasons?.includes("D1_ATR_UNAVAILABLE")) {
      const frames = p.context?.D1?.evidence?.frames || [], bars = p.q_inputs?.D1?.payload?.bars || [];
      const missing = frames.filter(f=>f.atr === null);
      if (missing.length) {
        el.append(node("p", "可核对的日线 Context 事实如下；这是 ATR 未就绪的行情时间，不是补造诊断或候选绑定时间。", "note"));
        const audit = node("details"); audit.append(node("summary", `${missing.length} 根日线 ATR 未就绪 · ${time(bars[missing[0].index]?.completed_at)} 至 ${time(bars[missing.at(-1).index]?.completed_at)}`));
        audit.append(table(["日线下标", "完成时间", "字段"], missing.map(f=>[String(f.index), time(bars[f.index]?.completed_at), "ATR 未提供"]))); el.append(audit);
      }
    }
    return el;
  }
  function summary(record, source = "查看历史 · 已保存快照") {
    const p = record.payload || {}, snap = p.market_snapshot || {}, root = node("div");
    root.append(node("div", `${snap.security?.display_symbol || snap.security?.symbol || "所选证券"} · Q 规则分析`, "q-result-title"), node("div", source, "q-badge"));
    const date = node("p", "分析时点：", "q-stamp"); date.append(stamp(snap.as_of_timestamp)); root.append(date);
    root.append(node("p", `快照参考报价：${snap.current_price_reference?.status === "AVAILABLE" ? exactPrice(snap.current_price_reference.price) : "未提供"}（不是最新报价或入场价）`, "q-stamp"));
    const title = headline(record); root.append(node("h2", title, "q-headline"));
    root.append(node("p", record.status === "INSUFFICIENT" ? "当前证据无法完成规则判断；这不表示看空，也不等于没有机会。" : record.status !== "AVAILABLE" ? "本次结果不可用于规则判断。可查看具体原因与原始记录。" : title === "符合入场规则" ? "所列候选的入场规则已满足，不代表已成交。各候选分别判断。" : "以下是已保存的规则事实；候选与阶段独立展示，不构成统一买卖结论。", "q-thesis"));
    const issues = currentIssues(p), missing = node("section", "", "q-current-evidence");
    missing.append(node("h3", "当前数据缺失 / 模块状态"));
    issues.forEach(v=>missing.append(node("p", `${v.label}${v.status ? ` · ${state(v.status)}` : ""}${v.at ? ` · ${time(v.at)}` : ""}`), reasons(v.codes)));
    if (!issues.length) missing.append(node("p", record.status === "AVAILABLE" ? "本记录各模块未报告输入阻断；严格资格限制另列。" : "返回结果未列明模块原因，请查看各层证据。", "note"));
    root.append(missing);
    if (p.qualification_mode === "OBSERVATIONAL" || p.strict_historical_as_of === false) root.append(node("p", "适用限制：观察性分析，历史可知性未认证；不能据此获得正式入场资格。", "q-limit"));
    if (p.diagnostics?.includes("INDEPENDENT_M30_OPEN_REFERENCE_MISSING")) root.append(node("p", "缺少独立开盘证据：确认后的指示性评估不等于下一开盘资格。", "q-limit"));
    const strictAllowed = p.qualification_mode === "AS_OF" && p.setup?.strict_confirmation === true;
    const all = groups(p).filter(g=>!ended(currentFact(g))).sort((a,b)=>(Date.parse(currentFact(b).effective_at) - Date.parse(currentFact(a).effective_at)));
    root.append(node("h3", "当前候选 · 规则状态"));
    if (record.status === "AVAILABLE" && all.length) {
      root.append(node("p", `共 ${all.length} 个候选 · 下方「入场资格」可查看各阶段`, "note"));
      all.slice(0,2).forEach(g=>root.append(candidate(g, true, strictAllowed)));
      if (all.length > 2) { const rest = node("details"); rest.append(node("summary", `另 ${all.length-2} 个候选`)); all.slice(2).forEach(g=>rest.append(candidate(g,true,strictAllowed))); root.append(rest); }
    } else { root.append(node("p", record.status === "AVAILABLE" ? "本记录没有未结束的入场候选；不等同于当前数据缺失。" : "尚无可展示的有效入场候选；模块不可用时不能据此判断规则是否满足。", "note"), prices(null, false)); }
    const historical = setupGroups(p).filter(items=>ended(items.at(-1)));
    root.append(node("p", `历史候选 / 形态失效：${historical.length} 个已失效或过期形态，原因和时间见下方对应详情。`, "q-history-status"));
    return root;
  }
  function basis(record) {
    const p = record.payload || {}, snap = p.market_snapshot || {}, root = node("div");
    const module = title => { const el = node("section", "", "q-module"); el.append(node("h3", title)); root.append(el); return el; };
    const cover = module("数据与分析快照");
    cover.append(node("p", "上方图表单独标明当前行情或 E 冻结证据；查看 Q 记录不会更换图表数据。", "note"));
    cover.append(node("p", `质量：${state(snap.data_quality)} · 记录保存于 ${time(record.created_at)} · 所有时间显示 UTC+8`));
    cover.append(table(["周期", "快照内行情数", "证据状态"], [["W1","w1_bars"],["D1","d1_bars"],["M30","m30_bars"]].map(([tf,key])=>[tf, Array.isArray(snap[key]) ? String(snap[key].length) : "未提供", state((snap.timeframe_evidence_status?.[tf.toLowerCase()] || snap.timeframe_evidence_status?.[tf])?.source_status)])));
    cover.append(node("p", `快照最近完成日线收盘：${exactPrice(snap.d1_bars?.at(-1)?.close)}。与页面最新报价、当前行情日线分别标示。`, "note"));
    const context = module("市场背景 · Context"), periods = node("div", "", "q-periods");
    for (const tf of ["W1","D1","M30"]) {
      const result = p.context?.[tf], evidence = result?.evidence, frame = evidence?.frames?.at(-1), col = node("section");
      col.append(node("h4", {W1:"周线",D1:"日线",M30:"半小时"}[tf]), node("p", result ? state(result.status) : "输入或结果未提供"));
      if (result?.status === "AVAILABLE" && frame) {
        col.append(node("p", state(frame.base_regime)), node("p", `ATR：${exactPrice(frame.atr)}`, "note"));
        col.append(node("p", `对应完成行情：${time(p.q_inputs?.[tf]?.payload?.bars?.[frame.index]?.completed_at)}`, "q-stamp"));
        const keys = new Set([...(frame.major || []), ...(frame.micro || []), ...(frame.zones || [])]);
        const pivots = (evidence.pivots || []).filter(v=>keys.has(v.key));
        if (pivots.length) col.append(table(["结构","价格","确认时间"], pivots.map(v=>[`${state(v.hierarchy)} · ${state(v.kind)}（${state(v.label)}）`,exactPrice(v.price),time(v.confirmation_time)])));
        const zones = (evidence.zones || []).filter(v=>keys.has(v.key));
        if (zones.length) col.append(table(["区域","范围"],zones.map(v=>[`${state(v.role)} · ${state(v.status)}`,`${v.lower} – ${v.upper}`])));
        const range = (evidence.ranges || []).find(v=>v.version_key === frame.active_range || v.key === frame.active_range);
        if (range) col.append(node("p", `当前区间：${range.lower} – ${range.upper}`));
        if (frame.readiness) col.append(node("p", `结构可用性：${Object.entries(frame.readiness).map(([k,v])=>`${({atr:"ATR",micro:"微观",major:"主要",zone:"区域",range:"区间"})[k] || k}${v ? "已就绪" : "未就绪"}`).join("、")}`, "note"));
      }
      col.append(reasons(result?.reason_codes)); periods.append(col);
    }
    context.append(periods);
    const events = module("价格事件 · Event");
    for (const tf of ["W1","D1","M30"]) {
      const result = p.event?.[tf]; events.append(node("h4", `${tf} · ${result ? state(result.status) : "结果未提供"}`), reasons(result?.reason_codes));
      if (result?.evidence?.regime) events.append(node("p", `事件输出背景：${state(result.evidence.regime)}`));
      const records = result?.records || [];
      if (records.length) events.append(table(["时间","事件","状态","方向"],records.slice(-6).map(row=>{const r=row.record || row, e=r.evidence || {};return [time(r.effective_at),state(e.kind || r.event_type),state(e.status),state(e.direction)];})));
      else events.append(node("p", result?.status === "AVAILABLE" ? "此周期没有已记录事件。" : "证据不足时不能将空列表解释为没有机会。", "note"));
      if (records.length>6) events.append(node("p", `展示最近 6 / ${records.length} 条，完整记录在技术详情。`, "note"));
    }
    const setups = module("候选形态 · Setup"), facts = p.setup?.facts || [], origins = new Map();
    facts.forEach(f=>{ if (!origins.has(f.setup_key)) origins.set(f.setup_key,f); });
    setups.append(node("p", `结果：${state(p.setup?.status)} · ${origins.size} 个独立形态`));
    if (p.setup?.status !== "AVAILABLE") setups.append(reasons(p.setup?.reasons));
    else if (p.setup?.reasons?.length) setups.append(historicalDiagnostics(p));
    if (origins.size) setups.append(table(["形态","最早记录","锚点（非成交止损）"],[...origins.values()].map(f=>[state(f.family),time(f.effective_at),exactPrice(f.anchor_price)])));
    setupGroups(p).forEach((items, index)=>{
      const last = items.at(-1), detail = node("details", "", "q-setup-history"); detail.dataset.setupKey = last.setup_key;
      detail.append(node("summary", `${ended(last) ? "历史已结束" : "形态最新事实"} · 形态 ${index+1} · ${state(last.family)} · ${state(last.status)} · ${time(last.effective_at)}`));
      items.filter(f=>!f.candidate_key).forEach(f=>{
        const row = node("section"); row.dataset.factKey = f.fact_key || "";
        row.append(factLabel(f), node("p", state(f.status)), reasons(f.reasons, Infinity)); detail.append(row);
      });
      setups.append(detail);
    });
    const entries = module("入场资格 · Entry"); entries.append(node("p", "确认后的指示性评估与下一根常规 M30 开盘验证分开。LONG_READY 表示符合入场规则，不代表已成交。", "note"));
    const candidates = groups(p); if (!candidates.length) entries.append(node("p", "尚无可追溯候选及有效几何，入场参考、失效位与目标均无法评估。"));
    candidates.forEach(g=>entries.append(candidate(g, false, p.qualification_mode === "AS_OF" && p.setup?.strict_confirmation === true)));
    const holder = module("若已持有 · Holder"); holder.append(node("p", "仅假设持有对应形态；不推断实际持仓。入场不合格不等于应退出。", "note"), reasons(p.holder?.reasons));
    if (!p.holder?.items?.length) holder.append(node("p", state(p.holder?.status || "UNDETERMINED")));
    (p.holder?.items || []).forEach(item=>{
      holder.append(node("h4", `${state(item.family)} · ${state(item.status)}`), reasons(item.reasons));
      const binding = item.target_binding;
      if (binding) {
        const match = candidates.find(g=>g.latest.setup_key===binding.setup_key && g.latest.candidate_key===binding.candidate_key);
        holder.append(node("p", `目标归属：${match ? `候选 ${match.number}` : "见绑定事实"} · 绑定生效 ${time(binding.effective_at)} · 冻结 T1 ${exactPrice(item.target1)}`));
      }
      if (item.target_touch) holder.append(node("p", `触价证据：${time(item.target_touch.start)} 至 ${time(item.target_touch.completed_at)} · 最高价 ${exactPrice(item.target_touch.high)}`));
      holder.append(technical("持有判断的绑定与证据", item));
    });
    const replayCodes = new Set(p.setup?.status === "AVAILABLE" ? p.setup.reasons || [] : []);
    const limits = module("适用限制与补证据"); limits.append(node("p", "以下为输入限制与诊断集合，不自动等同于本次结论的直接失败原因。历史回放汇总另见候选形态详情。", "note"), reasons((p.diagnostics || []).filter(code=>!replayCodes.has(code)), Infinity));
    (p.evidence_guidance || []).filter(g=>!replayCodes.has(g.code)).forEach(g=>limits.append(node("p", `${reason(g.code)}：${g.action}`)));
    (snap.warnings || []).forEach(w=>limits.append(node("p", w, "note")));
    root.append(technical("技术详情 · 原始枚举、身份、manifest、输入及完整 JSON", record)); return root;
  }
  window.PaqsQView = { node, state, reason, time, technical, summary, basis, headline, groups };
})();
