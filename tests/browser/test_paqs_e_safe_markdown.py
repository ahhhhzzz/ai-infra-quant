from __future__ import annotations

import json

import pytest
from playwright.sync_api import Browser, expect

from .test_paqs_e_narrative import make_app, select
from .workbench_support import MODEL, Workbench, narrative_pair

MARKDOWN = """# PAQS-E 研究报告
## 结论
- 当前为 **WATCH_LONG**。
- `CURRENT_PRICE_REFERENCE` 仅供参考。
---
## 关键位置
| 区域 | 角色 | 说明 |
|---|---|---|
| 342\u2013350 | 支撑 | 失败下破候选 |
| 371\u2013377 | 阻力 | 结构确认区 |
1. 等待完成 M30。
2. 不追价。
### 位置
#### 条件
**重要** 与 __强调__、*观察*、`Trigger != Followthrough`
- 条件一
  + 嵌套条件
    * 更深条件
- 条件二
1. 等待
2. 确认
---
> 以冻结 Snapshot 为准
| 项目 | 说明 |
| --- | --- |
| **方向** | `WATCH` |
| 中文 | 非结构化判断 |
```text
精确代码示例 <script>window.attack=1</script>
```
普通段落
下一行
"""


@pytest.mark.parametrize("width,light", [(1440, False), (900, True), (390, False), (390, True)])
def test_formatted_elements_raw_identity_and_local_toggle(
    browser: Browser,
    workbench_server: str,
    width: int,
    light: bool,
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False, width=width)
    result, run = narrative_pair(1, prose=MARKDOWN)
    app.narratives = {result["narrative_result_id"]: result}
    app.narrative_runs = {run["narrative_run_id"]: run}
    app.narrative_history_ids = list(app.narratives)
    page = app.open()
    select(app)
    if light:
        page.locator("#theme-toggle").click()
    formatted = page.locator(".narrative-markdown")
    expect(formatted).to_be_visible()
    for tag in (
        "h1",
        "h2",
        "h3",
        "h4",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "code",
        "pre",
        "hr",
        "blockquote",
        "table",
        "thead",
        "tbody",
        "th",
        "td",
    ):
        assert formatted.locator(tag).count() > 0, tag
    expect(formatted.locator("ul ul ul li")).to_have_text("更深条件")
    expect(formatted.locator("table tbody tr")).to_have_count(4)
    before = page.locator("#decision-audit").text_content()
    assert before is not None
    evidence = page.locator("#evidence-facts").text_content()
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    raw_button = page.get_by_role("button", name="原文", exact=True)
    raw_button.focus()
    page.keyboard.press("Enter")
    expect(raw_button).to_have_attribute("aria-pressed", "true")
    expect(page.locator(".narrative-text")).to_be_visible()
    assert page.locator(".narrative-text").text_content() == MARKDOWN
    page.get_by_role("button", name="格式化", exact=True).click()
    expect(formatted).to_be_visible()
    assert page.locator("#decision-audit").text_content() == before
    assert json.loads(before)["decision"]["response_text_sha256"] == result["response_text_sha256"]
    assert page.locator("#evidence-facts").text_content() == evidence
    assert requests == [] and app.posts == [] and app.errors == []
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    app.close()


@pytest.mark.parametrize(
    "prose",
    [
        "<script>window.attack=1</script>"
        '<img src="https://attack.example/x" onerror="window.attack=2">',
        '<a href="javascript:alert(1)">a</a><style>body{display:none}</style>'
        '<iframe src="https://attack.example"></iframe>'
        '<iframe srcdoc="<script>alert(1)</script>"></iframe>',
        "[x](javascript:alert(1)) ![image](https://attack.example/image) "
        "![bad](javascript:alert(1)) "
        "[d](data:text/html,x) [f](file:///x) [r](//attack.example)",
        "| title | value |\n| --- | --- |\n| malformed |\n**unmatched and `code",
        "```unclosed\n<script>window.attack=1</script>\n**literal**",
        r"\# 转义标题\n\*星号\* \_下划线\_ \`代码\` \|",
        "长" * 6000,
        "| A | B |\n| --- | --- |\n| <img src=x onerror=alert(1)> | `a|b` |",
        "```text\n" + "x" * 6000 + "\n```",
        "| A | B |\n| --- | --- |\n| " + "x" * 6000 + " | value |",
    ],
    ids=[
        "script-image",
        "html-style-frame",
        "unsafe-links",
        "bad-table",
        "unclosed-fence",
        "escaped",
        "long-token",
        "safe-table-cells",
        "long-code",
        "long-table",
    ],
)
def test_hostile_and_malformed_markdown_is_inert_and_raw_exact(
    browser: Browser,
    workbench_server: str,
    prose: str,
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False, width=390)
    result, run = narrative_pair(1, prose=prose)
    app.narratives = {result["narrative_result_id"]: result}
    app.narrative_runs = {run["narrative_run_id"]: run}
    app.narrative_history_ids = list(app.narratives)
    external = []
    app.page.on(
        "request",
        lambda request: external.append(request.url) if "attack.example" in request.url else None,
    )
    page = app.open()
    select(app)
    expect(page.locator(".narrative-markdown")).to_be_visible()
    assert (
        page.locator(
            "#decision-result script, #decision-result img, #decision-result iframe, "
            "#decision-result style, #decision-result a"
        ).count()
        == 0
    )
    assert page.evaluate("window.attack") is None and external == []
    page.get_by_role("button", name="原文", exact=True).click()
    assert page.locator(".narrative-text").text_content() == prose
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert app.posts == [] and app.errors == []
    app.close()


def test_delayed_history_read_and_view_toggles_keep_latest_selected_identity(
    browser: Browser,
    workbench_server: str,
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    select(app, 2)
    app.hold = "narrative-results/20000000"
    page.locator('[data-narrative-result-id="20000000-0000-4000-8000-000000000001"]').click()
    page.wait_for_timeout(100)
    app.hold = None
    select(app, 2)
    page.get_by_role("button", name="原文", exact=True).click()
    before = page.locator("#decision-audit").text_content()
    for route in app.pending:
        app.respond(route)
    page.get_by_role("button", name="格式化", exact=True).click()
    assert page.locator("#decision-audit").text_content() == before
    assert app.posts == [] and app.errors == []
    app.close()


def test_research_default_off_explicit_on_and_model_change_reset(
    browser: Browser,
    workbench_server: str,
) -> None:
    app = Workbench(browser, workbench_server, legacy_history=False)
    page = app.open()
    expect(page.locator("#web-research")).not_to_be_checked()
    expect(page.locator("#research-status")).to_contain_text("API 成本")
    app.post_status = 422
    app.post_body = {"status": 422, "code": "SYNTHETIC_PRECONDITION", "detail": "Fixture"}
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("SYNTHETIC_PRECONDITION")
    assert dict(app.posts[-1])["web_research"] is False
    app.post_status = 201
    app.post_body = None
    page.locator("#model-id").select_option(MODEL)
    page.locator("#web-research").check()
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("已提交成功")
    assert len(app.posts) == 2 and app.posts[-1]["web_research"] is True
    page.locator("#model-id").select_option("deepseek-v4-pro")
    expect(page.locator("#web-research")).not_to_be_checked()
    page.locator("#web-research").check()
    page.reload()
    expect(page.locator("#web-research")).not_to_be_checked()
    assert len(app.posts) == 2 and app.errors == []
    app.close()


def test_research_failure_keeps_prior_narrative_and_never_retries(
    browser: Browser,
    workbench_server: str,
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    select(app)
    before = page.locator("#decision-audit").text_content()
    app.post_status = 422
    app.post_body = {
        "status": 422,
        "code": "PAQS_E_RESEARCH_PRECONDITION_FAILED",
        "detail": "Requested web research failed",
    }
    page.locator("#web-research").check()
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("PAQS_E_RESEARCH_PRECONDITION_FAILED")
    page.get_by_role("button", name="原文", exact=True).click()
    page.locator("#refresh-market").click()
    assert page.locator("#decision-audit").text_content() == before
    assert len(app.posts) == 1 and app.posts[0]["web_research"] is True
    assert app.errors == []
    app.close()
