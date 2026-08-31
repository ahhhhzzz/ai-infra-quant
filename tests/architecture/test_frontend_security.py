from pathlib import Path


def test_user_controlled_rendering_avoids_unsafe_html_sinks() -> None:
    source = Path("src/ai_infra_quant/frontend/static/app.js").read_text(encoding="utf-8")
    for unsafe_sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert unsafe_sink not in source
    assert "document.createElement" in source
    assert "textContent" in source
    assert "addEventListener" in source
