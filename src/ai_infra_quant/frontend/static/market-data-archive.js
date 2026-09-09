/* Explicit collection only. All list/detail/table interactions are local GETs. */
(() => {
  "use strict";
  const el = (id) => document.getElementById(id);
  const reasonLabel = (code) => ({
    OBSERVATIONAL_COVERAGE_NOT_CERTIFIED: "观察范围，完整覆盖未认证",
    PROVIDER_ERROR: "供应商请求失败", PROVIDER_INVALID: "供应商数据无效",
    CALENDAR_INVALID: "日历校验未通过", CALENDAR_INCOMPLETE: "日历不完整或日型未知",
    CONFLICTING_DUPLICATE: "同一时间的数据冲突，已拒绝该批次",
    EMPTY_BATCH: "未返回已完成行情", NO_DATA: "数据不可用",
  }[code] || (code ? "该批次校验未通过，详见冻结质量信息" : "—"));
  const base = "/api/v1/market-data/archive";
  let security = null, epoch = 0, pending = false, selected = null;
  let listCursor = null, barsCursor = null, listRequest = 0, detailRequest = 0, barsRequest = 0;
  const status = (text) => { el("archive-status").textContent = text; };
  const node = (tag, text) => { const item = document.createElement(tag); item.textContent = text; return item; };
  const controls = () => {
    el("archive-save").disabled = pending || !security;
    el("archive-refresh").disabled = !security;
    el("archive-list-next").disabled = !security || !listCursor;
    el("archive-bars-next").disabled = !selected || !barsCursor;
  };
  async function read(path, options = {}) {
    const response = await fetch(`${base}${path}`, { cache: "no-store", ...options });
    if (!response.ok) throw new Error(`本地存档请求未完成（HTTP ${response.status}）；可手动重试读取。`);
    return response.json();
  }
  async function list(next = false) {
    if (!security) return;
    const token = epoch, request = ++listRequest, id = security.id;
    const cursor = next ? listCursor : null;
    status("读取本地存档列表…");
    try {
      const data = await read(`/securities/${encodeURIComponent(id)}/captures?limit=20${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`);
      if (token !== epoch || request !== listRequest) return;
      el("archive-list").replaceChildren();
      data.items.forEach((item) => {
        const button = node("button", `${item.symbol} · ${item.recorded_at} · D1 ${item.batches.D1.count} / M1 ${item.batches.M1.count} · ${item.status}`);
        button.type = "button";
        button.addEventListener("click", () => detail(item.capture_id));
        el("archive-list").append(button);
      });
      listCursor = data.next_cursor;
      status(data.items.length ? "本地列表已读取；选择一条存档查看。" : "该证券暂无本地存档。");
      controls();
    } catch (error) { if (token === epoch && request === listRequest) status(error.message); }
  }
  async function bars(next = false) {
    if (!selected) return;
    const token = epoch, request = ++barsRequest, id = selected;
    const timeframe = el("archive-timeframe").value, cursor = next ? barsCursor : null;
    barsCursor = null; controls();
    try {
      const data = await read(`/captures/${encodeURIComponent(id)}/bars?timeframe=${timeframe}&limit=500${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`);
      if (token !== epoch || request !== barsRequest || selected !== id) return;
      const body = el("archive-bars").querySelector("tbody");
      body.replaceChildren();
      data.items.forEach((item) => {
        const row = document.createElement("tr");
        [timeframe === "D1" ? item.session_date : item.interval_start, item.open, item.high, item.low, item.close, item.volume].forEach((value) => row.append(node("td", value)));
        body.append(row);
      });
      barsCursor = data.next_cursor; controls();
      status(`已离线读取 ${timeframe} ${data.items.length} 条${barsCursor ? "，还有下一页" : "，本页为末页"}。`);
    } catch (error) { if (token === epoch && request === barsRequest) status(error.message); }
  }
  async function detail(id) {
    const token = epoch, request = ++detailRequest;
    selected = null; barsCursor = null; ++barsRequest; controls();
    el("archive-detail").replaceChildren();
    el("archive-bars").querySelector("tbody").replaceChildren();
    status("读取本地存档详情…");
    try {
      const data = await read(`/captures/${encodeURIComponent(id)}`);
      if (token !== epoch || request !== detailRequest) return;
      selected = data.capture_id;
      el("archive-known-id").value = data.capture_id;
      el("archive-detail").append(node("h3", `${data.market} ${data.symbol} · ${data.status}`), node("p", `Capture ${data.capture_id} · ${data.recorded_at}`));
      const audit = document.createElement("details");
      audit.append(node("summary", "冻结日历、来源、获取时间、区间及质量（精确原值）"), node("pre", JSON.stringify(data, null, 2)));
      for (const name of ["D1", "M1", "calendar"]) {
        const batch = data.batches[name];
        el("archive-detail").append(node("p", `${name}: ${batch.status} · ${batch.count} 条 · ${batch.actual_start || batch.requested_start || "—"} → ${batch.actual_end || batch.requested_end || "—"} · 缺口 ${batch.missing_count ?? "未知"} · ${reasonLabel(batch.reason_code)}`));
      }
      el("archive-detail").append(node("p", `${data.provider} · ${data.adjustment_basis} · 复权基准版本未知`), audit);
      await bars();
    } catch (error) { if (token === epoch && request === detailRequest) status(error.message); }
  }
  document.addEventListener("security-selected", (event) => {
    security = event.detail; ++epoch;
    selected = null; listCursor = null; barsCursor = null;
    el("archive-list").replaceChildren(); el("archive-detail").replaceChildren();
    el("archive-bars").querySelector("tbody").replaceChildren();
    el("archive-known-id").value = "";
    el("archive-security").textContent = security ? `${security.market} ${security.symbol}` : "请选择证券；也可离线按 Capture ID 查询。";
    status(pending ? "已有保存请求执行中；切换证券不会取消服务端保存。" : ""); controls();
    if (el("market-archive").open && security) void list();
  });
  el("archive-save").addEventListener("click", async () => {
    if (pending || !security) return;
    pending = true; const token = epoch, id = security.id;
    controls(); status("正在保存当前行情；请等待，勿重复提交。页面离开不代表服务端取消。");
    try {
      const data = await read("/captures", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ security_id: id }) });
      if (token !== epoch) return;
      await list();
      if (token === epoch) await detail(data.capture_id);
    } catch (error) {
      if (token === epoch) status(`${error.message} 保存结果未知时，请先读取本地列表确认；不会自动重试。`);
    } finally { pending = false; controls(); }
  });
  el("market-archive").addEventListener("toggle", () => { if (el("market-archive").open) void list(); });
  el("archive-refresh").addEventListener("click", () => void list());
  el("archive-list-next").addEventListener("click", () => void list(true));
  el("archive-bars-next").addEventListener("click", () => void bars(true));
  el("archive-timeframe").addEventListener("change", () => { el("archive-bars").querySelector("tbody").replaceChildren(); void bars(); });
  el("archive-known-form").addEventListener("submit", (event) => { event.preventDefault(); void detail(el("archive-known-id").value.trim()); });
})();
