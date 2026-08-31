from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", uuid4()))


def problem_response(
    request: Request,
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    errors: list[dict[str, str]] | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"https://local.ai-infra-quant/errors/{code.lower().replace('_', '-')}",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail,
        "instance": request.url.path,
        "request_id": request_id(request),
        "errors": errors or [],
    }
    if extra:
        body.update(extra)
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "code": str(error["type"]).upper(),
            "message": str(error["msg"]),
        }
        for error in exc.errors()
    ]
    stable_codes = {"INVALID_MARKET", "INVALID_SYMBOL"}
    code = next(
        (
            str(error["type"]).upper()
            for error in exc.errors()
            if str(error["type"]).upper() in stable_codes
        ),
        "VALIDATION_ERROR",
    )
    return problem_response(
        request,
        status=422,
        code=code,
        title="Validation error",
        detail="The request did not satisfy the Phase 1 contract.",
        errors=errors,
    )
