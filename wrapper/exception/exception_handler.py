import json
from contextlib import contextmanager


@contextmanager
def exception_handler(**kwargs):
    """
    Context manager for handling exceptions with additional context details.

    Args:
        **kwargs: Key-value pairs providing contextual details.
    """
    details = "; ".join(f"{key}: {value}" for key, value in kwargs.items())
    try:
        yield
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Error: File not found. Context: [{details}]") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error: Failed to parse JSON. Context: [{details}]", e.doc, e.pos) from e
    except Exception as e:
        raise Exception(f"Error: An unexpected issue occurred. Context: [{details}]") from e
