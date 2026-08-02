"""Integration tests for end-to-end Notification Router pipeline."""

import asyncio
import pytest
from data.loader import DatasetLoader
from src.context.graph_builder import ContextGraphBuilder
from src.router import NotificationRouter


def test_end_to_end_notification_router():
    async def _test():
        loader = DatasetLoader()
        builder = ContextGraphBuilder(loader)
        router = NotificationRouter(builder)

        for msg in loader.messages[:3]:
            out, latency, is_fast = await router.route_message(msg)
            assert out.message_id == msg.message_id
            assert out.action in {"notify", "digest", "mute"}
            assert 0.0 <= out.confidence <= 1.0
            assert isinstance(out.reason, str)
            assert latency >= 0.0

    asyncio.run(_test())

