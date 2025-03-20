import functools
from typing import AsyncIterable, Iterable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, merge_content
from langchain_core.utils._merge import merge_dicts

from .base import BaseLLMPatcher


def merge_base_messages(messages: list[BaseMessage]) -> BaseMessage:
    """
    Merges a list of `BaseMessage` instances into a single `BaseMessage`.

    Args:
        messages (list[BaseMessage]): A list of `BaseMessage` instances to be merged.

    Returns:
        BaseMessage: A single `BaseMessage` instance containing merged content, additional_kwargs, and response_metadata.

    Raises:
        ValueError: If the provided list of messages is empty.
    """
    if not messages:
        raise ValueError("At least one message must be provided")

    content = merge_content(*[msg.content for msg in messages])
    additional_kwargs = merge_dicts(*[msg.additional_kwargs for msg in messages])
    response_metadata = merge_dicts(*[msg.response_metadata for msg in messages])

    return BaseMessage(
        content=content,
        additional_kwargs=additional_kwargs,
        response_metadata=response_metadata,
        type=messages[0].type,
        name=messages[0].name,
        id=messages[0].id
    )


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

    def _from_llm_class(self, llm_class: type) -> type:
        """
        Modifies a LangChain `BaseChatModel` class by injecting buffering logic into its stream and astream methods.

        Args:
            llm_class (type): The LangChain model class to be modified.

        Returns:
            type: The modified LangChain model class with batch streaming capabilities.
        """
        return type(llm_class.__name__, (llm_class,), {
            "stream": self.stream_wrapper(getattr(llm_class, "stream")),
            "astream": self.astream_wrapper(getattr(llm_class, "astream")),
        })

    def stream_wrapper(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Iterable[BaseMessage]:
            buffer = []
            for item in func(*args, **kwargs):
                buffer.append(item)
                if len(buffer) >= self.buffer_size:
                    yield merge_base_messages(buffer)
                    buffer = []
            if buffer:  # Emit any remaining items
                yield merge_base_messages(buffer)

        return wrapper

    def astream_wrapper(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> AsyncIterable[BaseMessage]:
            buffer = []
            async for item in func(*args, **kwargs):
                buffer.append(item)
                if len(buffer) >= self.buffer_size:
                    yield merge_base_messages(buffer)
                    buffer = []
            if buffer:  # Emit any remaining items
                yield merge_base_messages(buffer)

        return wrapper
