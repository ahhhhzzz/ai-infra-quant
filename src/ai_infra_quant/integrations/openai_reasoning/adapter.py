from __future__ import annotations

import hashlib
import os
from typing import Any

from openai import OpenAI
from pydantic import SecretStr, ValidationError

from ai_infra_quant.core.domain.paqs_e_reasoning import (
    OPENAI_PROVIDER_ID,
    PaqsEReasoningRequestV1,
    PromptPackage,
    StrategyPackage,
)
from ai_infra_quant.core.domain.paqs_market_snapshot import canonical_json
from ai_infra_quant.core.ports.paqs_e_reasoning import (
    ReasoningFailureKind,
    ReasoningProviderFailure,
    ReasoningProviderOutcome,
    ReasoningProviderSuccess,
)
from ai_infra_quant.integrations.openai_reasoning.schema import (
    PaqsEReasoningResultSchemaV1,
)


class OpenAIPaqsEReasoningAdapter:
    def __init__(
        self,
        *,
        api_key: SecretStr | str | None = None,
        client: Any | None = None,
    ) -> None:
        self._api_key = (
            api_key
            if isinstance(api_key, SecretStr)
            else SecretStr(api_key)
            if api_key is not None
            else None
        )
        self._client = client

    def reason(
        self,
        *,
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
    ) -> ReasoningProviderOutcome:
        configuration_failure = self._configuration_failure(request, strategy, prompt)
        if configuration_failure is not None:
            return configuration_failure
        client = self._client
        if client is None:
            secret = self._api_key
            if secret is None:
                environment_value = os.environ.get("OPENAI_API_KEY")
                secret = SecretStr(environment_value) if environment_value is not None else None
            if secret is None or not secret.get_secret_value().strip():
                return ReasoningProviderFailure(
                    kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                    reason="OPENAI_API_KEY is not configured",
                )
            try:
                client = OpenAI(api_key=secret.get_secret_value())
            except Exception:
                return ReasoningProviderFailure(
                    kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                    reason="OpenAI client configuration failed",
                )

        instructions = (
            f"{prompt.content}\n\n"
            f"Runtime prompt identity: {prompt.prompt_version} / {prompt.content_sha256}.\n"
            f"Selected primary strategy: {strategy.strategy_id} / {strategy.content_sha256}."
        )
        strategy_input = (
            f"PRIMARY STRATEGY MARKDOWN\n"
            f"strategy_id={strategy.strategy_id}\n"
            f"content_sha256={strategy.content_sha256}\n\n"
            f"{strategy.content}"
        )
        try:
            response = client.responses.parse(
                model=request.model_id,
                instructions=instructions,
                input=[
                    {"role": "developer", "content": strategy_input},
                    {"role": "user", "content": canonical_json(request)},
                ],
                text_format=PaqsEReasoningResultSchemaV1,
                store=False,
            )
        except ValidationError:
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.INVALID_STRUCTURED_OUTPUT,
                reason="OpenAI response did not match the strict PAQS-E output schema",
            )
        except Exception:
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.PROVIDER_UNAVAILABLE,
                reason="OpenAI Responses API request failed",
            )

        parsed = getattr(response, "output_parsed", None)
        if isinstance(parsed, PaqsEReasoningResultSchemaV1):
            try:
                result = parsed.to_domain()
            except (TypeError, ValueError):
                return ReasoningProviderFailure(
                    kind=ReasoningFailureKind.INVALID_STRUCTURED_OUTPUT,
                    reason="OpenAI response contained invalid exact-value fields",
                )
            response_id = getattr(response, "id", None)
            return ReasoningProviderSuccess(
                result=result,
                provider_response_id=response_id if isinstance(response_id, str) else None,
            )
        if _contains_refusal(response):
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.PROVIDER_REFUSAL,
                reason="OpenAI declined to produce the requested PAQS-E analysis",
            )
        return ReasoningProviderFailure(
            kind=ReasoningFailureKind.INVALID_STRUCTURED_OUTPUT,
            reason="OpenAI response did not contain a parsed PAQS-E result",
        )

    @staticmethod
    def _configuration_failure(
        request: PaqsEReasoningRequestV1,
        strategy: StrategyPackage,
        prompt: PromptPackage,
    ) -> ReasoningProviderFailure | None:
        if request.model_provider != OPENAI_PROVIDER_ID:
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="request model provider is not supported by this adapter",
            )
        if (
            strategy.strategy_id != request.primary_strategy_id
            or strategy.content_sha256 != request.primary_strategy_content_sha256
            or hashlib.sha256(strategy.content.encode("utf-8")).hexdigest()
            != strategy.content_sha256
        ):
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="strategy package identity does not match request",
            )
        if (
            prompt.prompt_version != request.prompt_version
            or prompt.content_sha256 != request.prompt_content_sha256
            or hashlib.sha256(prompt.content.encode("utf-8")).hexdigest() != prompt.content_sha256
        ):
            return ReasoningProviderFailure(
                kind=ReasoningFailureKind.CONFIGURATION_ERROR,
                reason="prompt package identity does not match request",
            )
        return None


def _contains_refusal(response: object) -> bool:
    output = getattr(response, "output", ())
    if not isinstance(output, list | tuple):
        return False
    for item in output:
        content = getattr(item, "content", ())
        if not isinstance(content, list | tuple):
            continue
        for part in content:
            if getattr(part, "type", None) == "refusal" or getattr(part, "refusal", None):
                return True
    return False
