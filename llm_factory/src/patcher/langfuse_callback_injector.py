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

    def _from_llm_class(self, llm_class: type) -> type:
        return type(llm_class.__name__, (llm_class,), {
            "invoke": self.call_wrapper(getattr(llm_class, "invoke"), self.handler),
            "ainvoke": self.call_wrapper(getattr(llm_class, "ainvoke"), self.handler),
            "stream": self.call_wrapper(getattr(llm_class, "stream"), self.handler),
            "astream": self.call_wrapper(getattr(llm_class, "astream"), self.handler),
        })

    @staticmethod
    def _append_handler(configs, handler):
        if "config" not in configs:
            configs["config"] = {"callbacks": [handler]}
        elif "callbacks" not in configs["config"]:
            configs["config"]["callbacks"] = [handler]
        else:
            configs["config"]["callbacks"].append(handler)
        return configs

    @staticmethod
    def call_wrapper(func, langfuse_handler):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **LangfuseCallbackInjector._append_handler(kwargs, langfuse_handler))

        return wrapper
