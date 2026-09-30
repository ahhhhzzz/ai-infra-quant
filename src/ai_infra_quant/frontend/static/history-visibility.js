/* Explicit, reversible local operations. No analysis or research requests. */
(() => {
  "use strict";
  const pending = new Set();
  function button(kind, item, security, deleted) {
    const id = kind === "Q" ? item.analysis_id : item.narrative_result_id;
    const key = `${kind}/${id}`;
    const el = document.createElement("button"); el.type = "button";
    el.className = "history-visibility"; el.textContent = deleted ? "恢复" : "删除";
    el.disabled = pending.has(key);
    el.addEventListener("click", async () => {
      if (pending.has(key)) return;
      const identity = `${security.display_name || security.symbol} · ${security.display_symbol} · ${kind} 分析 · ${item.created_at}`;
      if (!deleted && !window.confirm(`${identity}\n从历史列表移除，可恢复；原始证据仍保留。不释放数据库空间。\n确认删除？`)) return;
      pending.add(key); el.disabled = true;
      const detail = {kind, id, security_id: security.id, deleted: !deleted};
      document.dispatchEvent(new CustomEvent("analysis-visibility-changing", {detail}));
      try {
        const response = await fetch(`/api/v1/analysis-history/${key}/visibility`, {
          method: "PUT", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({security_id: security.id, deleted: !deleted}),
        });
        const body = await response.json();
        if (!response.ok) throw new Error(body.detail || "操作失败");
        el.textContent = deleted ? "已恢复" : "已删除";
        document.dispatchEvent(new CustomEvent("analysis-visibility-changed", {detail}));
      } catch (error) { el.textContent = `操作未确认：${error.message}；刷新列表核对`; }
      finally { pending.delete(key); el.disabled = false; }
    });
    return el;
  }
  window.HistoryVisibility = {button};
})();
