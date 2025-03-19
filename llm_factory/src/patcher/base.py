from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel


class BaseLLMPatcher:
    """
    Base class for patchers that modify LangChain-based LLM instances.

    This class defines a framework for implementing custom patchers that transform or enhance
    LangChain `BaseChatModel` or `Embeddings` instances.
    """

    ALLOWED_CLASSES = [BaseChatModel, Embeddings]
    """
    list: A list of allowed classes that the patcher can process. 
    """

    def from_llm(self, instance):
        """
        Applies the patcher to a given LangChain LLM instance.

        This method verifies that the provided LLM instance is of an allowed type and
        delegates the actual transformation to the `_from_llm` method.

        Args:
            instance (Any): The LangChain LLM instance to be patched.

        Returns:
            Any: The modified LLM instance after applying the patcher.

        Raises:
            ValueError: If the provided instance is not of an allowed type.
        """
        if all([not isinstance(instance, allowed_class) for allowed_class in self.ALLOWED_CLASSES]):
            raise ValueError(f"Unsupported LLM type: {type(instance)}")
        return self._from_llm(instance)

    def _from_llm(self, instance):
        """
        Defines the transformation logic for a given LangChain LLM instance.

        This method must be implemented by subclasses to provide specific patching logic.

        Args:
            instance (Any): The LangChain LLM instance to be transformed.

        Raises:
            NotImplementedError: Always raised if the method is not implemented by a subclass.
        """
        raise NotImplementedError
