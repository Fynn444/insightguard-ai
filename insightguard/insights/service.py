from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol, runtime_checkable


logger = logging.getLogger(__name__)
CONFIDENCE_LEVELS = {'Low', 'Medium', 'High', 'Not assessed'}


class InsightError(RuntimeError):
    """Base error for business insight generation."""


class ResponseValidationError(InsightError):
    """Raised when a provider response does not match the application contract."""


class InsightProviderError(InsightError):
    """Raised when a provider fails while generating an insight."""


@dataclass(frozen=True)
class InsightRequest:
    task: str
    context: dict[str, Any]


@dataclass(frozen=True)
class InsightResponse:
    executive_summary: str
    recommendations: list[str]
    confidence: str
    provider: str
    simulated: bool
    evidence: list[str]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> InsightResponse:
        if not isinstance(value, Mapping):
            raise ResponseValidationError('Insight provider response must be a mapping.')

        summary = value.get('executive_summary')
        recommendations = value.get('recommendations')
        confidence = value.get('confidence')
        provider = value.get('provider')
        simulated = value.get('simulated')
        evidence = value.get('evidence', [])

        if not isinstance(summary, str) or not summary.strip():
            raise ResponseValidationError('Insight response requires a non-empty executive_summary string.')
        if not isinstance(recommendations, list) or any(
            not isinstance(item, str) or not item.strip() for item in recommendations
        ):
            raise ResponseValidationError('Insight response recommendations must be a list of non-empty strings.')
        if not isinstance(confidence, str) or confidence not in CONFIDENCE_LEVELS:
            raise ResponseValidationError(f'Insight confidence must be one of {sorted(CONFIDENCE_LEVELS)}.')
        if not isinstance(provider, str) or not provider.strip():
            raise ResponseValidationError('Insight response requires a provider name.')
        if not isinstance(simulated, bool):
            raise ResponseValidationError('Insight response simulated field must be a boolean.')
        if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
            raise ResponseValidationError('Insight response evidence must be a list of strings.')

        return cls(
            executive_summary=summary.strip(),
            recommendations=[item.strip() for item in recommendations],
            confidence=confidence,
            provider=provider.strip(),
            simulated=simulated,
            evidence=evidence,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class InsightProvider(Protocol):
    name: str
    simulated: bool

    def generate(self, request: InsightRequest) -> Mapping[str, Any]:
        """Generate a response that conforms to the InsightResponse contract."""


class InsightService:
    def __init__(self, provider: InsightProvider):
        self.provider = provider

    def generate(self, task: str, context: dict[str, Any]) -> InsightResponse:
        if not isinstance(task, str) or not task.strip():
            raise ValueError('Insight task must be a non-empty string.')
        if not isinstance(context, dict):
            raise TypeError('Insight context must be a dictionary.')

        try:
            response = InsightResponse.from_mapping(self.provider.generate(InsightRequest(task, context)))
            if response.provider != self.provider.name:
                raise ResponseValidationError('Insight response provider does not match the configured provider.')
            if response.simulated != self.provider.simulated:
                raise ResponseValidationError('Insight response provenance does not match the configured provider.')
            return response
        except InsightError:
            logger.error('Insight provider %s returned an invalid response.', self.provider.name)
            raise
        except Exception as error:
            logger.error('Insight provider %s failed with %s.', self.provider.name, type(error).__name__)
            raise InsightProviderError(f'Insight provider {self.provider.name} failed.') from error