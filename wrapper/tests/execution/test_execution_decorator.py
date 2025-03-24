import pytest

from execution.execution_decorator import execution_decorator
import time
import asyncio


@execution_decorator
def sync_function(x, y):
    time.sleep(1)
    return x + y


@execution_decorator
async def async_function(x, y):
    await asyncio.sleep(1)
    return x + y

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function(3, 4)
    assert result == 7


def test_sync_function():
    result = sync_function(3, 4)
    assert result == 7
