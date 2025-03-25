import functools
import asyncio
from contextlib import contextmanager


# Context manager for wrapping logic
@contextmanager
def execution_wrapper(*args, **kwargs):
    """
    A general-purpose wrapper to execute logic before and after a function runs.
    """
    print("Pre-execution steps...")
    yield
    print("Post-execution steps...")


# Generalized function execution
def execution_decorator(target_function):
    """
    A execution that wraps both synchronous and asynchronous functions
    with the provided execution logic.
    """
    if asyncio.iscoroutinefunction(target_function):
        @functools.wraps(target_function)
        async def async_wrapper(*args, **kwargs):
            with execution_wrapper(*args, **kwargs):
                result = await target_function(*args, **kwargs)
            return result

        return async_wrapper
    else:
        @functools.wraps(target_function)
        def sync_wrapper(*args, **kwargs):
            with execution_wrapper(*args, **kwargs):
                result = target_function(*args, **kwargs)
            return result

        return sync_wrapper
