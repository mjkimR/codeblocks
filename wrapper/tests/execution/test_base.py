import asyncio

import pytest
from contextlib import contextmanager
from execution.base import BaseExecutionWrapper
import time


class Timer(BaseExecutionWrapper):
    @contextmanager
    def wrapping_logic(self, *args, **kwargs):
        start_time = time.time()
        yield
        end_time = time.time()
        print(f"end - start: {end_time - start_time:0.2f}")


@Timer()
def sample_sync_function(x, y):
    time.sleep(1)
    return x + y


@Timer()
async def sample_async_function(x, y):
    await asyncio.sleep(1)
    return x + y


def test_sync_function():
    result = sample_sync_function(3, 4)
    assert result == 7


@pytest.mark.asyncio
async def test_async_function():
    result = await sample_async_function(3, 4)
    assert result == 7
