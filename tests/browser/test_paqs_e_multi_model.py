from __future__ import annotations

import pytest
from playwright.sync_api import Browser, Route, expect

from ai_infra_quant.application.paqs_e_models import ModelRegistry

from .workbench_support import MODEL, MODEL_NAME, STRATEGY, US, Workbench


def test_exact_flat_catalog_model_and_research_changes_are_not_analysis(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    assert page.locator("#model-id option").all_text_contents() == [
        "DeepSeek V4 Flash",
        "DeepSeek V4 Pro",
        "Qwen3.8 Flash",
        "Qwen3.8 Max",
        "Qwen3.7 Plus",
        "GLM-5.2",
        "Kimi K3",
        "Hy4 Preview",
        "GPT-5.6 Luna",
        "GPT-5.6 Terra",
        "GPT-5.6 Sol",
    ]
    expect(page.locator("#model-id optgroup")).to_have_count(0)
    expect(page.locator('input[name="model_id"]')).to_have_count(0)
    expect(page.locator("#model-id")).to_have_value("deepseek-v4-flash")
    for model in ModelRegistry().models:
        page.locator("#model-id").select_option(model.model_key)
        if model.web_research_supported:
            expect(page.locator("#web-research")).to_be_checked()
            page.locator("#web-research").uncheck()
            page.locator("#web-research").check()
        else:
            expect(page.locator("#web-research")).not_to_be_checked()
            expect(page.locator("#web-research")).to_be_disabled()
            expect(page.locator("#research-status")).to_contain_text("未启用")
    assert app.posts == [] and app.errors == []
    app.close()


@pytest.mark.parametrize("width,light", [(1440, False), (390, True)])
def test_credential_dialog_save_delete_clear_and_no_browser_secret_storage(
    browser: Browser, workbench_server: str, width: int, light: bool
) -> None:
    app = Workbench(browser, workbench_server, configured=False)
    app.page.set_viewport_size({"width": width, "height": 900})
    registry = ModelRegistry()
    saved: dict[str, str] = {}
    mutations: list[str] = []
    sentinel = "synthetic-browser-007c1-only"

    def credentials(route: Route) -> None:
        model = registry.resolve(route.request.url.rsplit("/", 1)[1])
        if route.request.method == "PUT":
            assert route.request.post_data_json == {"secret": sentinel}
            saved[model.credential_slot] = sentinel
            mutations.append("PUT")
        elif route.request.method == "DELETE":
            assert route.request.post_data_json == {}
            saved.pop(model.credential_slot, None)
            mutations.append("DELETE")
        app.fulfill(
            route,
            {
                "credential_configured": model.credential_slot in saved,
                "credential_source": "secure_store" if saved else "missing",
                "secure_storage_available": True,
            },
        )

    def configuration(route: Route) -> None:
        app.fulfill(
            route,
            {
                "default_model_key": registry.default_model_key,
                "models": [
                    {
                        "model_key": item.model_key,
                        "display_name": item.display_name,
                        "credential_label": item.credential_label,
                        "credential_configured": item.credential_slot in saved,
                        "web_research_supported": item.web_research_supported,
                    }
                    for item in registry.models
                ],
                "default_strategy_id": STRATEGY,
                "strategies": [
                    {
                        "strategy_id": STRATEGY,
                        "display_name": "Synthetic primary",
                        "content_sha256": "a" * 64,
                    }
                ],
            },
        )

    app.page.route("**/paqs-e/credentials/*", credentials)
    app.page.route("**/paqs-e/configuration", configuration)
    page = app.open()
    if light:
        page.locator("#theme-toggle").click()
    expect(page.locator("#analyze-button")).to_be_disabled()
    page.locator("#configure-credential").click()
    expect(page.locator("#credential-dialog")).to_be_visible()
    expect(page.locator("#credential-secret")).to_have_attribute("type", "password")
    page.locator("#credential-secret").fill(sentinel)
    page.locator("#credential-save").click()
    expect(page.locator("#credential-status")).to_contain_text("已安全保存")
    expect(page.locator("#credential-secret")).to_have_value("")
    assert sentinel not in page.content()
    assert (
        page.evaluate(
            "Object.values(localStorage).join(' ') + "
            "Object.values(sessionStorage).join(' ') + document.cookie"
        ).find(sentinel)
        == -1
    )
    assert page.evaluate("async () => (await indexedDB.databases()).length") == 0
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.locator("#credential-close").click()
    expect(page.locator("#analyze-button")).to_be_enabled()
    page.locator("#model-id").select_option("deepseek-v4-pro")
    expect(page.locator("#analyze-button")).to_be_enabled()
    page.locator("#configure-credential").click()
    expect(page.locator("#credential-secret")).to_have_value("")
    page.locator("#credential-delete").click()
    expect(page.locator("#credential-status")).to_contain_text("已删除")
    page.locator("#credential-close").click()
    expect(page.locator("#analyze-button")).to_be_disabled()
    page.reload()
    page.locator("#configure-credential").click()
    expect(page.locator("#credential-secret")).to_have_value("")
    assert mutations == ["PUT", "DELETE"]
    assert app.posts == [] and app.errors == []
    app.close()


def test_web_toggle_is_captured_before_await_and_advanced_identity_remains_visible(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    page.locator("#model-id").select_option(MODEL)
    page.locator("#web-research").uncheck()
    app.hold = "/paqs-e/narrative-analyses"
    page.locator("#analyze-button").click()
    page.locator("#web-research").check()
    page.locator("#model-id").select_option("qwen3.8-max")
    assert app.posts == [
        {"security_id": US, "model_key": MODEL, "strategy_id": STRATEGY, "web_research": False}
    ]
    app.hold = None
    app.respond(app.pending.pop())
    expect(page.locator("#decision-heading")).to_contain_text(MODEL_NAME)
    page.locator(".audit > summary").click()
    expect(page.locator("#decision-audit")).to_contain_text('"model_provider": "openai"')
    expect(page.locator("#decision-audit")).to_contain_text(MODEL)
    assert len(app.posts) == 1
    app.close()


def test_research_precondition_failure_preserves_prior_historical_decision(
    browser: Browser, workbench_server: str
) -> None:
    app = Workbench(browser, workbench_server)
    page = app.open()
    app.select(1)
    app.post_status = 422
    app.post_body = {
        "status": 422,
        "code": "PAQS_E_RESEARCH_PRECONDITION_FAILED",
        "detail": "Requested web research failed",
        "failure_kind": "PROVIDER_UNAVAILABLE",
    }
    app.analyze()
    expect(page.locator("#analysis-state")).to_contain_text("PAQS_E_RESEARCH_PRECONDITION_FAILED")
    expect(page.locator("#decision-heading")).to_contain_text("历史")
    assert len(app.posts) == 1 and app.errors == []
    assert "analysis_run_id" not in app.post_body
    app.close()
