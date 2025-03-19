from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class BaseLLMPatcher:
    ALLOWED_CLASSES = [BaseChatModel, Embeddings]

    def from_llm(self, instance):
        if all([not isinstance(instance, allowed_class) for allowed_class in self.ALLOWED_CLASSES]):
            raise ValueError(f"Unsupported LLM type: {type(instance)}")
        return self._from_llm(instance)

    def _from_llm(self, instance):
        raise NotImplementedError
