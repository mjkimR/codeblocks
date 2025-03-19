import functools
import uuid

from langchain_core.language_models import BaseChatModel

from .base import BaseLLMPatcher


class LangfuseWrapper(BaseLLMPatcher):
    ALLOWED_CLASSES = [BaseChatModel]

    def __init__(self, session_id=None, user_id=None, **kwargs):
        from langfuse.callback import CallbackHandler

        self.session_id = session_id if session_id is not None else str(uuid.uuid4())
        self.user_id = user_id
        self.handler = CallbackHandler(session_id=self.session_id, user_id=self.user_id, **kwargs)
        self.handler.auth_check()

    def _from_llm(self, instance: BaseChatModel) -> BaseChatModel:
        instance.invoke = self.invoke_wrapper(instance.invoke, self.handler)
        return instance

    @staticmethod
    def invoke_wrapper(func, langfuse_handler):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs, config={"callbacks": [langfuse_handler]})

        return wrapper
