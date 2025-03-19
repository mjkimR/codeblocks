import functools
import uuid

from langchain_core.language_models import BaseChatModel

from .base import BaseLLMPatcher


class LangfuseCallbackInjector(BaseLLMPatcher):
    """
    A LangChain-based wrapper for modifying `BaseChatModel` instances with Langfuse integration.

    This patcher integrates Langfuse callback handling into LangChain models, enabling session tracking
    and user-specific configurations for enhanced monitoring and logging.
    """

    ALLOWED_CLASSES = [BaseChatModel]
    """
    list: Specifies the allowed classes for this patcher. Only `BaseChatModel` instances are supported.
    """

    def __init__(self, session_id=None, user_id=None, **kwargs):
        """
        Initializes the LangfuseWrapper with session and user-specific information.

        This method sets up the Langfuse callback handler and performs an authentication check.

        Args:
            session_id (str, optional): The session identifier for tracking. Defaults to a generated UUID.
            user_id (str, optional): The user identifier for tracking. Defaults to None.
            **kwargs: Additional keyword arguments passed to the Langfuse `CallbackHandler`.
        """
        from langfuse.callback import CallbackHandler

        self.session_id = session_id if session_id is not None else str(uuid.uuid4())
        self.user_id = user_id
        self.handler = CallbackHandler(session_id=self.session_id, user_id=self.user_id, **kwargs)
        self.handler.auth_check()

    def _from_llm(self, instance: BaseChatModel) -> BaseChatModel:
        """
        Modifies a LangChain `BaseChatModel` instance by integrating Langfuse callback handling.

        Args:
            instance (BaseChatModel): The LangChain model to be modified.

        Returns:
            BaseChatModel: The modified LangChain model with integrated Langfuse callbacks.
        """
        instance.invoke = self.invoke_wrapper(instance.invoke, self.handler)
        return instance

    @staticmethod
    def invoke_wrapper(func, langfuse_handler):
        """
        Wraps a model's invocation method with Langfuse callback handling.

        This method dynamically adds Langfuse callbacks to the invocation process, enabling tracking and logging.

        Args:
            func (callable): The original invocation method of the model.
            langfuse_handler (CallbackHandler): The Langfuse handler to be injected into the invocation process.

        Returns:
            callable: The wrapped invocation method with integrated Langfuse handling.
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs, config={"callbacks": [langfuse_handler]})

        return wrapper
