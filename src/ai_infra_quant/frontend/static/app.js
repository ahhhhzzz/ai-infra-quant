const api = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const problem = await response.json();
    throw new Error(problem.detail || problem.code || "Request failed");
  }
  return response.status === 204 ? null : response.json();
};

const textElement = (tagName, text, className) => {
  const element = document.createElement(tagName);
  element.textContent = text;
  if (className) element.className = className;
  return element;
};

const replaceChildren = (selector, children) => {
  document.querySelector(selector).replaceChildren(...children);
};

const renderWatchlist = async () => {
  const data = await api("/api/v1/watchlist");
  document.querySelector("#watchlist-status").textContent =
    `${data.items.length} identities`;
  const rows = data.items.map(({ security }) => {
    const row = document.createElement("div");
    row.className = "watchlist-row";
    row.append(
      textElement("span", security.display_symbol, "symbol"),
      textElement("span", security.currency),
      textElement("span", security.metadata_status, "status"),
    );
    const button = textElement("button", "Remove", "remove");
    button.type = "button";
    button.dataset.securityId = security.id;
    button.addEventListener("click", async () => {
      await api(`/api/v1/watchlist/${button.dataset.securityId}`, {
        method: "DELETE",
      });
      await renderWatchlist();
    });
    row.append(button);
    return row;
  });
  replaceChildren("#watchlist", rows);
};

const load = async () => {
  const [portfolio, performance, brokers, market, fundamental, events] = await Promise.all([
    api("/api/v1/portfolio"), api("/api/v1/performance"), api("/api/v1/brokers"),
    api("/api/v1/market-data/providers"), api("/api/v1/fundamental-data/providers"),
    api("/api/v1/event-data/providers")
  ]);
  document.querySelector("#equity").textContent =
    `${portfolio.base_currency} ${portfolio.total_equity}`;
  document.querySelector("#cash").textContent =
    `${portfolio.base_currency} ${portfolio.cash_value}`;
  document.querySelector("#nav").textContent = portfolio.nav;
  document.querySelector("#units").textContent = portfolio.units_outstanding;
  document.querySelector("#invested").textContent = portfolio.invested_ratio;
  document.querySelector("#return").textContent = performance.summary.since_inception_return;
  const statuses = [...brokers.items, ...market.items, ...fundamental.items, ...events.items];
  const providerRows = statuses.map((item) => {
    const row = document.createElement("div");
    row.className = "status-row";
    row.append(
      textElement("span", item.name),
      textElement(
        "span",
        `${item.implementation_status} / ${item.connection_status}`,
        "status",
      ),
    );
    return row;
  });
  replaceChildren("#providers", providerRows);
  await renderWatchlist();
};

document.querySelector("#security-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form.entries());
  if (!payload.display_name) delete payload.display_name;
  const result = document.querySelector("#form-result");
  try {
    const security = await api("/api/v1/securities", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await api("/api/v1/watchlist", {
      method: "POST",
      body: JSON.stringify({ security_id: security.id }),
    });
    result.textContent = `${security.display_symbol} created as USER_SUPPLIED_UNVERIFIED and added to the watchlist.`;
    event.target.reset();
    await renderWatchlist();
  } catch (error) {
    result.textContent = error.message;
  }
});

load().catch((error) => {
  document.querySelector("#watchlist-status").textContent = error.message;
});
