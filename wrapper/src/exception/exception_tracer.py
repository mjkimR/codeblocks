import traceback
from contextlib import contextmanager


@contextmanager
def exception_tracer(logger=None, disabled=False):
    """
    A context manager to trace exceptions with an optional logger.

    This context manager can be used to wrap a block of code and handle
    exceptions that occur within it. If a logger is provided, it logs
    the exception using the `error` method of the logger. Optionally,
    exception tracing can be disabled.

    Args:
        logger (logging.Logger, optional): A logger instance to log the
            exceptions. The logger should have an `error` method. Defaults to None.
        disabled (bool, optional): If set to True, exceptions will not be
            traced or logged but raised normally. Defaults to False.

    Yields:
        None: Allows the wrapped code block to execute.

    Raises:
        Exception: Any exception raised in the wrapped code block is logged
        (if logger is available) and re-raised.
    """
    try:
        yield
    except Exception as e:
        if disabled:
            raise e

        if logger and hasattr(logger, "error"):
            logger.error(repr(e))
        traceback.print_exc()

        raise e
