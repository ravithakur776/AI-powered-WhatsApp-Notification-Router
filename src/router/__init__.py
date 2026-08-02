"""Unified Notification Router pipeline orchestrating Fast-Path, Deep-Path, and Guardrails."""

import time
from typing import Tuple
from src.context.graph_builder import ContextGraphBuilder
from src.router.fast_path import FastPathRouter
from src.router.deep_path import DeepPathRouter
from src.router.guardrails import OutputGuardrails
from src.schemas.input_models import RawMessage
from src.schemas.output_models import RouterOutput
from src.utils.logger import logger
from src.utils.metrics import metrics_collector


class NotificationRouter:
    def __init__(self, context_builder: ContextGraphBuilder):
        self.context_builder = context_builder
        self.fast_path = FastPathRouter()
        self.deep_path = DeepPathRouter()
        self.guardrails = OutputGuardrails()

    async def route_message(self, message: RawMessage) -> Tuple[RouterOutput, float, bool]:
        """Routes message, returning (RouterOutput, latency_ms, is_fast_path)."""
        start_time = time.perf_counter()

        # 1. Build Enriched Context Graph
        ctx = await self.context_builder.build_context(message)

        # 2. Try Sub-5ms Fast Path
        fast_result = self.fast_path.evaluate(ctx)
        if fast_result is not None:
            sanitized = self.guardrails.validate_and_sanitize(fast_result)
            latency_ms = (time.perf_counter() - start_time) * 1000
            metrics_collector.record_decision(sanitized.action, latency_ms, is_fast_path=True)
            logger.info(f"Routed {message.message_id} -> {sanitized.action.upper()} via FAST PATH in {latency_ms:.2f}ms")
            return sanitized, latency_ms, True

        # 3. Escalate to Deep Path LLM Reasoning
        deep_result = await self.deep_path.route_message(ctx)
        sanitized = self.guardrails.validate_and_sanitize(deep_result)
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics_collector.record_decision(sanitized.action, latency_ms, is_fast_path=False)
        logger.info(f"Routed {message.message_id} -> {sanitized.action.upper()} via DEEP PATH in {latency_ms:.2f}ms")
        return sanitized, latency_ms, False


__all__ = ["NotificationRouter", "FastPathRouter", "DeepPathRouter", "OutputGuardrails"]
