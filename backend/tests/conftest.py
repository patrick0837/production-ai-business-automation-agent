import asyncio
import selectors


def create_selector_event_loop():
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


def pytest_asyncio_loop_factories(config, item):
    return {
        "selector": create_selector_event_loop,
    }