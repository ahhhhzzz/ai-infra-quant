"""Browser-only synthetic Tavily evidence; routes never call search or model providers."""
# ruff: noqa: RUF001 -- Chinese presentation copy is intentionally full-width.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Route, expect

from ai_infra_quant.application.paqs_e_models import ModelRegistry
from ai_infra_quant.application.paqs_e_runtime import load_strategy_package
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json

from .test_paqs_e_narrative import make_app, select
from .workbench_support import HK, MODEL, STRATEGY, US, Workbench, narrative_pair


class TavilyWorkbench(Workbench):
    def __init__(self, browser: Browser, address: str, *, search_key: bool = False) -> None:
        super().__init__(browser, address, legacy_history=False)
        self.search_key = search_key
        self.credential_writes: list[str] = []
        self.narratives.clear()
        self.narrative_runs.clear()
        for revision, market in [(1, "US"), (2, "US"), (3, "HK")]:
            result, run = narrative_pair(
                revision,
                market=market,
                prose=f"# 合成浏览器验证\n保留原文 [T1]；不是实际联网结果。{revision}",
            )
            payload = json.loads(run["request_payload_json"])
            for item in [result, run, payload]:
                item.update(model_id="deepseek-flash", model_provider="deepseek")
            if revision == 2:
                for item in [result, run, payload]:
                    item["web_research"] = True
                payload["auxiliary_context"] = [
                    {
                        "context_id": "synthetic-tavily",
                        "category": "web_research",
                        "source_label": "Tavily",
                        "content": "[T1] 合成投资者关系资料片段",
                        "provenance": canonical_json(
                            {
                                "schema_version": "paqs-e-tavily-evidence-v1",
                                "provider": "tavily",
                                "retrieved_at": "2026-09-30T01:00:00Z",
                                "snapshot_as_of": result["snapshot_as_of_timestamp"],
                                "requests": [{"status": "SUCCEEDED", "query": "synthetic"}],
                                "sources": [
                                    {
                                        "source_id": "T1",
                                        "title": "合成公司公告 <script>unsafe</script>",
                                        "url": "https://example.org/investor-release",
                                        "content": "合成实际输入片段 <img src=x onerror=alert(1)>",
                                        "published_at": None,
                                    },
                                    {
                                        "source_id": "T2",
                                        "title": "合成仅提供发布日期的公告",
                                        "url": "https://example.org/date-only-release",
                                        "content": "合成日期精度片段",
                                        "published_at": "2026-09-30",
                                    },
                                ],
                            }
                        ),
                    }
                ]
            run["request_payload_json"] = canonical_json(payload)
            run["request_payload_sha256"] = hashlib.sha256(
                run["request_payload_json"].encode()
            ).hexdigest()
            self.narratives[result["narrative_result_id"]] = result
            self.narrative_runs[run["narrative_run_id"]] = run
        self.narrative_history_ids = list(self.narratives)

    def respond(self, route: Route) -> None:
        path = urlparse(route.request.url).path
        if path.endswith("/research-credentials/tavily"):
            if route.request.method == "PUT":
                assert route.request.post_data_json == {"secret": "synthetic-local-key"}
                self.search_key = True
                self.credential_writes.append("PUT")
            elif route.request.method == "DELETE":
                self.search_key = False
                self.credential_writes.append("DELETE")
            return self.fulfill(route, {"credential_configured": self.search_key})
        if path.endswith("/configuration"):
            package = load_strategy_package()
            return self.fulfill(
                route,
                {
                    "default_model_key": "deepseek-flash",
                    "models": [
                        {
                            "model_key": item.model_key,
                            "display_name": item.display_name,
                            "credential_label": item.credential_label,
                            "credential_configured": True,
                            "web_research_supported": item.web_research_supported,
                            "external_web_research_supported": item.provider_id == "deepseek"
                            and not item.web_research_supported,
                        }
                        for item in ModelRegistry().models
                        if item.enabled
                    ],
                    "external_research": {
                        "provider": "tavily",
                        "credential_configured": self.search_key,
                    },
                    "default_strategy_id": STRATEGY,
                    "strategies": [
                        {
                            "strategy_id": STRATEGY,
                            "display_name": "PAQS-E 主策略",
                            "content_sha256": package.content_sha256,
                        }
                    ],
                },
            )
        return super().respond(route)


def test_key_configuration_and_navigation_do_not_dispatch_analysis(
    browser: Browser, workbench_server: str, tmp_path: Path
) -> None:
    app = TavilyWorkbench(browser, workbench_server)
    page = app.open()
    page.locator("#branch-e").click()
    expect(page.locator("#web-research-label")).to_have_text("联网研究 · Tavily")
    expect(page.locator("#web-research")).to_be_disabled()
    expect(page.locator("#research-status")).to_contain_text("请配置搜索服务")
    expect(page.locator("#analyze-button")).to_be_enabled()
    page.locator("#configure-research-credential").click()
    expect(page.locator("#credential-service")).to_contain_text("独立搜索凭据")
    page.locator("#credential-secret").fill("synthetic-local-key")
    page.locator("#credential-save").click()
    expect(page.locator("#credential-status")).to_contain_text("已安全保存")
    expect(page.locator("#credential-secret")).to_have_value("")
    page.locator("#credential-close").click()
    expect(page.locator("#web-research")).to_be_enabled()
    expect(page.locator("#web-research")).not_to_be_checked()
    expect(page.locator("#research-status")).to_contain_text("搜索与模型请求可能产生费用")
    page.locator("#web-research").check()
    page.locator("#tab-compare").click()
    expect(page.locator("#q-e-selection")).to_contain_text("请关闭联网后运行同快照 E")
    page.locator("#model-id").select_option(MODEL)
    expect(page.locator("#web-research-label")).to_have_text("联网研究")
    expect(page.locator("#web-research")).not_to_be_checked()
    page.locator("#model-id").select_option("deepseek-flash")
    expect(page.locator("#web-research")).not_to_be_checked()
    page.locator(f'[data-security-id="{HK}"]').click()
    page.reload()
    expect(page.locator("#web-research")).not_to_be_checked()
    page.locator("#branch-e").click()
    page.screenshot(path=str(tmp_path / "tavily-configured.png"), full_page=True)
    page.locator("#configure-research-credential").click()
    page.locator("#credential-delete").click()
    expect(page.locator("#credential-status")).to_contain_text("已删除")
    page.locator("#credential-close").click()
    expect(page.locator("#web-research")).to_be_disabled()
    assert app.credential_writes == ["PUT", "DELETE"]
    assert app.posts == [] and app.errors == []
    assert "synthetic-local-key" not in page.content()
    assert "synthetic-local-key" not in page.evaluate("JSON.stringify(localStorage)")
    app.close()


def test_explicit_tavily_sources_and_history_preserve_text_and_security(
    browser: Browser, workbench_server: str, tmp_path: Path
) -> None:
    app = TavilyWorkbench(browser, workbench_server, search_key=True)
    page = app.open()
    page.locator("#branch-e").click()
    page.locator("#web-research").check()
    assert app.posts == []
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("已提交成功 Narrative")
    expect(page.locator("#external-research-evidence")).to_be_visible()
    evidence = page.locator("#external-research-evidence")
    expect(evidence).to_contain_text("联网研究：Tavily")
    expect(evidence).to_contain_text("检索时间")
    expect(evidence).to_contain_text("行情快照")
    expect(evidence).to_contain_text("未知（未用检索时间替代）")
    expect(evidence).to_contain_text("发布时间：2026-09-30（仅日期，具体时刻未知）")
    expect(evidence).not_to_contain_text("2026/09/29 20:00:00")
    expect(evidence.locator("a").first).to_have_attribute(
        "href", "https://example.org/investor-release"
    )
    expect(evidence.locator("a").first).to_have_attribute("rel", "noopener noreferrer")
    evidence.locator("summary").first.click()
    expect(evidence).to_contain_text("合成实际输入片段")
    assert evidence.locator("script,img").count() == 0
    result = app.narratives["20000000-0000-4000-8000-000000000002"]
    assert page.locator(".narrative-text").text_content() == result["response_text"]
    page.screenshot(path=str(tmp_path / "tavily-sources.png"), full_page=True)
    page.locator("#tab-history").click()
    select(app, 2)
    expect(evidence).to_be_visible()
    page.locator("#refresh-market").click()
    assert len(app.posts) == 1 and app.posts[0]["web_research"] is True
    page.locator("#tab-history").click()
    select(app, 1)  # Old history without external provenance remains readable.
    expect(evidence).to_be_hidden()
    expect(page.locator(".narrative-text")).to_contain_text("结果。1")
    page.locator(f'[data-security-id="{HK}"]').click()
    expect(page.locator("#decision-heading")).to_have_text("尚无选中的分析结果")
    expect(evidence).to_be_hidden()
    assert page.locator(".narrative-text").count() == 0
    page.locator("#tab-history").click()
    select(app, 3)
    expect(page.locator("#decision-heading")).to_contain_text("00700")
    assert len(app.posts) == 1 and app.errors == []
    app.close()


def test_search_off_runs_original_analysis_even_without_search_key(
    browser: Browser, workbench_server: str
) -> None:
    app = TavilyWorkbench(browser, workbench_server)
    page = app.open()
    page.locator("#branch-e").click()
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("已提交成功 Narrative")
    expect(page.locator("#external-research-evidence")).to_be_hidden()
    assert len(app.posts) == 1 and app.posts[0] == {
        "security_id": US,
        "model_key": "deepseek-flash",
        "strategy_id": STRATEGY,
        "web_research": False,
    }
    assert app.errors == []
    app.close()


def test_native_research_remains_separate_and_old_frozen_context_readable(
    browser: Browser, workbench_server: str
) -> None:
    app = make_app(browser, workbench_server)
    page = app.open()
    page.locator("#branch-e").click()
    page.locator("#model-id").select_option(MODEL)
    expect(page.locator("#web-research-label")).to_have_text("联网研究")
    expect(page.locator("#configure-research-credential")).to_be_hidden()
    page.locator("#web-research").check()
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text("已提交成功 Narrative")
    page.wait_for_function("document.querySelector('#research-evidence').textContent !== '—'")
    evidence = json.loads(page.locator("#research-evidence").text_content() or "")
    assert evidence[0]["context_id"] == "synthetic-browser-research"
    expect(page.locator("#external-research-evidence")).to_be_hidden()
    page.locator("#tab-history").click()
    select(app, 2)
    assert json.loads(page.locator("#research-evidence").text_content() or "") == evidence
    assert len(app.posts) == 1 and app.posts[0]["web_research"] is True
    assert app.errors == []
    app.close()


@pytest.mark.parametrize(
    "failure,explanation",
    [
        ("NOT_CONFIGURED", "请配置搜索服务"),
        ("AUTHENTICATION_FAILED", "认证失败"),
        ("RATE_LIMITED", "限流或额度不足"),
        ("TIMEOUT", "搜索超时"),
        ("EMPTY_RESULTS", "未返回可用"),
        ("INVALID_RESPONSE", "响应格式异常"),
        ("FROZEN_SNAPSHOT_EXTERNAL_RESEARCH_BLOCKED", "历史 Q 快照"),
    ],
)
def test_tavily_failure_is_explained_without_new_success(
    browser: Browser, workbench_server: str, failure: str, explanation: str
) -> None:
    app = TavilyWorkbench(browser, workbench_server, search_key=True)
    page = app.open()
    page.locator("#tab-history").click()
    select(app, 1)
    before = page.locator(".narrative-text").text_content()
    page.locator("#web-research").check()
    app.post_status = 422
    app.post_body = {
        "status": 422,
        "code": "PAQS_E_RESEARCH_PRECONDITION_FAILED",
        "external_research": {
            "provider": "tavily",
            "failure_code": failure,
            "research_id": "synthetic-research-evidence-id",
        },
    }
    page.locator("#analyze-button").click()
    expect(page.locator("#analysis-state")).to_contain_text(explanation)
    expect(page.locator("#analysis-state")).to_contain_text("没有确认新的 Narrative")
    expect(page.locator("#decision-heading")).to_contain_text("较早成功结果")
    assert page.locator(".narrative-text").text_content() == before
    assert not page.locator("#analysis-state details").get_attribute("open")
    expect(page.locator("#analysis-state details")).to_contain_text(failure)
    assert len(app.posts) == 1 and app.errors == []
    app.close()
