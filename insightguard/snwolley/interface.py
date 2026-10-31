from __future__ import annotations

import logging
from typing import Any

from insightguard.config import get_settings
from insightguard.insights.mock import MockInsightsProvider
from insightguard.insights.service import InsightService, InsightResponse


logger = logging.getLogger(__name__)


class SnwolleyIntegrationUnavailable(RuntimeError):
    """Raised when official Snwolley setup cannot be used safely."""


class SnwolleyClient:
    """Compatibility facade around the provider-neutral insight service."""

    def __init__(self, use_mock: bool | None = None, api_key: str | None = None):
        settings = get_settings()
        self.use_mock = settings['SNWOLLEY_USE_MOCK'] if use_mock is None else use_mock
        credential = api_key if api_key is not None else settings['SNWOLLEY_API_KEY']

        if not self.use_mock:
            if not credential:
                logger.warning('Snwolley mock mode is disabled, but no credentials are configured.')
                raise SnwolleyIntegrationUnavailable(
                    'Snwolley credentials are missing. Enable development mock mode or provide credentials after official setup is documented.'
                )
            logger.warning('Snwolley credentials are configured, but the official toolkit contract is unavailable.')
            raise SnwolleyIntegrationUnavailable(
                'Official Snwolley toolkit documentation is unavailable; no network request was made.'
            )

        self._service = InsightService(MockInsightsProvider())

    def generate_insight(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        return self._service.generate(task, context).to_dict()
