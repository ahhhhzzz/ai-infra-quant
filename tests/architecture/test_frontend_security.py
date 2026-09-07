from pathlib import Path


def test_user_controlled_rendering_avoids_unsafe_html_sinks() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/ai_infra_quant/frontend/static").glob("*.js")
    )
    for unsafe_sink in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "new Function",
    ):
        assert unsafe_sink not in source
    assert "document.createElement" in source
    assert "textContent" in source
    assert "addEventListener" in source
