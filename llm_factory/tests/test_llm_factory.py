import pytest

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from llm_factory import LLMFactory
from patcher.buffered_streaming import BufferedStreamingPatcher

from patcher.langfuse_callback_injector import LangfuseCallbackInjector

_MODEL_CONFIGS = {
    "gpt-4o-mini": {
        "llm_type": "chat",
        "provider": "openai",
        "model": "gpt-4o-mini"
    },
    "gpt-4o": {
        "llm_type": "chat",
        "model": "gpt-4o",
        "provider": "openai"
    },
    "local-chat": {
        "llm_type": "chat",
        "model": "gemma-3-12b-it",
        "provider": "lm_studio",
        "base_url": "http://localhost:1234/v1"
    },
    "local-embedding": {
        "llm_type": "embedding",
        "model": "multilingual-e5-large-instruct",
        "provider": "lm_studio",
        "base_url": "http://localhost:1234/v1"
    }
}


@pytest.mark.parametrize("config,call_test", [
    [_MODEL_CONFIGS["local-chat"], True],
])
async def test_create_chat_llm(config, call_test: bool):
    llm = LLMFactory.create_llm(patchers=[
        LangfuseCallbackInjector(),
        BufferedStreamingPatcher(buffer_size=5)
    ], **config)

    assert llm is not None
    assert isinstance(llm, BaseChatModel)

    # Test only if call_test is True (to avoid consuming API credits)
    if call_test:
        msg = "Say 'hi'. Do not say other things."
        # invoke
        assert "hi" in llm.invoke(msg).content.lower()
        # ainvoke
        assert "hi" in (await llm.ainvoke(msg)).content.lower()
        # stream
        assert "hi" in "".join([line.content for line in llm.stream(msg)]).lower()
        # astream
        assert "hi" in "".join([line.content async for line in llm.astream(msg)]).lower()


@pytest.mark.parametrize("config", [_MODEL_CONFIGS["local-embedding"]])
async def test_create_embedding_llm(config):
    llm = LLMFactory.create_llm(**config)
    assert llm is not None
    assert isinstance(llm, Embeddings)


@pytest.mark.parametrize("config", [_MODEL_CONFIGS["local-embedding"]])
async def test_not_allow_test(config):
    with pytest.raises(ValueError):
        llm = LLMFactory.create_llm(patchers=[BufferedStreamingPatcher(buffer_size=5)], **config)
