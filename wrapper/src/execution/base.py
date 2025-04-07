import functools
import asyncio
from contextlib import contextmanager


class BaseExecutionWrapper:
    """
    A base class that serves as both an execution and a wrapper for synchronous
    and asynchronous functions. This is achieved using the `__call__` method.

    Attributes:
        None
    """

    @contextmanager
    def wrapping_logic(self, *args, **kwargs):
        """
        Default wrapping logic for pre- and post-execution steps.

        This method acts as a context manager and can be overridden to customize
        behavior specific to execution.

        Args:
            *args: Positional arguments that may be passed to the wrapping logic.
            **kwargs: Keyword arguments that may be passed to the wrapping logic.

        Yields:
            None
        """
        print("Default pre-execution steps...")
        yield
        print("Default post-execution steps...")

    def __call__(self, func):
        """
        Decorator to wrap a function for execution, allowing both synchronous
        and asynchronous functions to be managed through the wrapper.

        Args:
            func (Callable): The function to be wrapped. It can be either
            synchronous or asynchronous.

        Returns:
            Callable: A wrapped version of the function, executed with pre-
            and post-processing steps.
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
