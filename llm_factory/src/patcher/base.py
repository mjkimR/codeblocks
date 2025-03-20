from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class BaseLLMPatcher:
    """
    Base class for patchers that modify LangChain-based LLM classes.

    This class defines a framework for implementing custom patchers that transform or enhance
    LangChain `BaseChatModel` or `Embeddings` classes.
    """

    ALLOWED_CLASSES = [BaseChatModel, Embeddings]
    """
    list: A list of allowed classes that the patcher can process. 
    """

    def from_llm_class(self, llm_class: type):
        # if all([not isinstance(instance, allowed_class) for allowed_class in self.ALLOWED_CLASSES]):
        #     raise ValueError(f"Unsupported LLM type: {type(instance)}")
        return self._from_llm_class(llm_class)

    def _from_llm_class(self, llm_class: type) -> type:
        """
        Converts a given LLM class to a patched version.

        Args:
            llm_class (type): The LLM class to be patched.

        Raises:
            NotImplementedError: This method should be implemented by subclasses.

        Returns:
            type: The patched LLM class.
        """
        raise NotImplementedError
