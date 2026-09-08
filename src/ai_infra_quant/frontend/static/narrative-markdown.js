/* Local presentation subset. All model content enters text nodes; links/images stay inert. */
(() => {
  "use strict";
  const element = (tag, text) => {
    const value = document.createElement(tag);
    if (text !== undefined) value.textContent = text;
    return value;
  };
  function inline(parent, text, depth = 0) {
    if (depth > 8) { parent.append(document.createTextNode(text)); return; }
    let plain = "";
    const flush = () => { if (plain) parent.append(document.createTextNode(plain)); plain = ""; };
    for (let i = 0; i < text.length;) {
      if (text[i] === "\\" && /[\\`*_[\]{}()#+.!|>-]/.test(text[i + 1] || "")) {
        plain += text[i + 1]; i += 2; continue;
      }
      const token = ["`", "**", "__", "*", "_"].find(mark => text.startsWith(mark, i));
      const end = token ? text.indexOf(token, i + token.length) : -1;
      if (token && end > i + token.length) {
        flush();
        const child = element(token === "`" ? "code" : token.length === 2 ? "strong" : "em");
        const content = text.slice(i + token.length, end);
        if (token === "`") child.textContent = content; else inline(child, content, depth + 1);
        parent.append(child); i = end + token.length;
      } else { plain += text[i]; i += 1; }
    }
    flush();
  }
  function cells(line) {
    const text = line.trim().replace(/^\|/, "").replace(/(?<!\\)\|$/, "");
    const result = []; let cell = "", code = false;
    for (let i = 0; i < text.length; i++) {
      if (text[i] === "\\" && i + 1 < text.length) { cell += text[i] + text[++i]; continue; }
      if (text[i] === "`") code = !code;
      if (text[i] === "|" && !code) { result.push(cell.trim()); cell = ""; }
      else cell += text[i];
    }
    result.push(cell.trim()); return result;
  }
  const list = line => /^( {0,12})([-*+]|\d+[.)])\s+(.+)$/.exec(line);
  const rule = line => /^\s*(---+|\*\*\*+|___+)\s*$/.test(line);
  function render(text) {
    const root = element("div"); root.className = "narrative-markdown";
    const lines = text.split(/\r\n|\n|\r/);
    for (let i = 0; i < lines.length;) {
      const line = lines[i];
      if (!line.trim()) { i++; continue; }
      const fence = /^\s*(```+|~~~+)[^`~]*$/.exec(line);
      if (fence) {
        const marker = fence[1]; let end = i + 1;
        while (end < lines.length && lines[end].trim() !== marker) end++;
        if (end < lines.length) {
          const pre = element("pre"); pre.append(element("code", lines.slice(i + 1, end).join("\n")));
          root.append(pre); i = end + 1; continue;
        }
        root.append(element("p", lines.slice(i).join("\n"))); break;
      }
      const heading = /^(#{1,4})\s+(.+)$/.exec(line);
      if (heading) {
        const h = element(`h${heading[1].length}`); inline(h, heading[2]); root.append(h); i++; continue;
      }
      if (rule(line)) { root.append(element("hr")); i++; continue; }
      if (line.includes("|") && i + 1 < lines.length) {
        const header = cells(line), separator = cells(lines[i + 1]);
        if (header.length > 1 && header.length === separator.length && separator.every(c => /^:?-{3,}:?$/.test(c))) {
          let end = i + 2; const rows = [];
          while (end < lines.length && lines[end].trim() && lines[end].includes("|")) rows.push(cells(lines[end++]));
          if (rows.every(row => row.length === header.length)) {
            const wrap = element("div"), table = element("table"), thead = element("thead"), tbody = element("tbody");
            wrap.className = "narrative-table-scroll"; wrap.tabIndex = 0; wrap.setAttribute("aria-label", "分析表格，可横向滚动");
            for (const [values, parent, tag] of [[header, thead, "th"], ...rows.map(row => [row, tbody, "td"])]) {
              const tr = element("tr"); for (const value of values) { const cell = element(tag); inline(cell, value); tr.append(cell); }
              parent.append(tr);
            }
            table.append(thead, tbody); wrap.append(table); root.append(wrap); i = end; continue;
          }
          root.append(element("p", lines.slice(i, end).join("\n"))); i = end; continue;
        }
      }
      if (list(line)) {
        const stack = [];
        while (i < lines.length && list(lines[i]) && !rule(lines[i])) {
          const match = list(lines[i++]), indent = match[1].length, tag = /^\d/.test(match[2]) ? "ol" : "ul";
          while (stack.length && stack.at(-1).indent > indent) stack.pop();
          if (!stack.length || stack.at(-1).indent < indent || stack.at(-1).tag !== tag) {
            if (stack.length && stack.at(-1).indent === indent) stack.pop();
            const container = element(tag), parent = stack.length ? stack.at(-1).last : root;
            parent.append(container); stack.push({ indent, tag, container, last: container });
          }
          const li = element("li"); inline(li, match[3]); stack.at(-1).container.append(li); stack.at(-1).last = li;
        }
        continue;
      }
      if (/^>\s?/.test(line)) {
        const quote = element("blockquote"); inline(quote, line.replace(/^>\s?/, "")); root.append(quote); i++; continue;
      }
      const paragraph = element("p"); inline(paragraph, line); root.append(paragraph); i++;
    }
    return root;
  }
  window.PaqsNarrativeMarkdown = Object.freeze({ render });
})();
