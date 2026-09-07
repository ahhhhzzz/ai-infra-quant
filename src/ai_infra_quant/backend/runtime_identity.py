"""Bounded launcher identity, captured by the application at startup only."""

import os
import re


def capture_source_revision() -> str:
    revision = os.environ.get("AI_INFRA_SOURCE_REVISION", "")
    return revision if re.fullmatch(r"[0-9a-f]{40}", revision) else "unknown"
