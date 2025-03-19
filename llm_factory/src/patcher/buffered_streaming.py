import functools
from typing import AsyncIterable, Iterable

from langchain_core.language_models import BaseChatModel
from .base import BaseLLMPatcher


class BufferedStreamingPatcher(BaseLLMPatcher):
    """
    A patcher for buffering and emitting outputs in batches during streaming in LangChain models.
    """

    ALLOWED_CLASSES = [BaseChatModel]

    def __init__(self, buffer_size: int = 5):
        """
        Initializes the patcher with a specified buffer size.

        Args:
            buffer_size (int): The size of the buffer before emitting the batch. Defaults to 5.
        """
        self.buffer_size = buffer_size

    def _from_llm(self, instance: BaseChatModel) -> BaseChatModel:
        """
        Modifies a LangChain `BaseChatModel` instance by injecting buffering logic into its stream and astream methods.

        Args:
            instance (BaseChatModel): The LangChain model to be modified.

        Returns:
            BaseChatModel: The modified LangChain model with batch streaming capabilities.
        """
        instance.stream = self.stream_wrapper(instance.stream)
        instance.astream = self.astream_wrapper(instance.astream)
        return instance

    def stream_wrapper(self, func):
        """
        Wraps the `stream` method to buffer results and emit in batches.

        Args:
            func (callable): The original `stream` method.

        Returns:
            callable: The wrapped method with buffering logic.
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Iterable:
            buffer = []
            for item in func(*args, **kwargs):
                buffer.append(item)
                if len(buffer) >= self.buffer_size:
                    yield buffer
                    buffer = []
            if buffer:  # Emit any remaining items
                yield buffer

        return wrapper

    def astream_wrapper(self, func):
        """
        Wraps the `astream` method to buffer results and emit in batches asynchronously.

        Args:
            func (callable): The original `astream` method.

        Returns:
            callable: The wrapped method with asynchronous buffering logic.
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterable:
            buffer = []
            async for item in func(*args, **kwargs):
                buffer.append(item)
                if len(buffer) >= self.buffer_size:
                    yield buffer
                    buffer = []
            if buffer:  # Emit any remaining items
                yield buffer

        return wrapper
