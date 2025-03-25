import functools
import asyncio
from contextlib import contextmanager


class BaseExecutionWrapper:
    """
    A base class that acts as both a execution and a wrapper for synchronous
    and asynchronous functions, using the __call__ method.
    """

    @contextmanager
    def wrapping_logic(self, *args, **kwargs):
        """
        Default wrapping logic. Override this method to customize behavior.
        """
        print("Default pre-execution steps...")
        yield
        print("Default post-execution steps...")

    def __call__(self, func):
        """
        Allow the class to be used as a execution without creating an instance.
        """
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.wrapping_logic(*args, **kwargs):
                    result = await func(*args, **kwargs)
                return result

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.wrapping_logic(*args, **kwargs):
                    result = func(*args, **kwargs)
                return result

            return sync_wrapper
