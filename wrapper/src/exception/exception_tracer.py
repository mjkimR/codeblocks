import traceback
from contextlib import contextmanager


@contextmanager
def exception_tracer(logger=None, disabled=False):
    try:
        yield
    except Exception as e:
        if disabled:
            raise e

        if logger and hasattr(logger, "error"):
            logger.error(repr(e))
        traceback.print_exc()

        raise e
