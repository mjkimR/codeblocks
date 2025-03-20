# LLM Factory

LLM Factory is a Python-based library designed to facilitate the creation and management of language models (LLMs) from
various providers. It includes patchers for enhanced functionality such as buffered streaming and Langfuse callback
handling.

## Features

* **Model Creation**: Easily create and configure language models from supported providers.

* **Buffered Streaming**: Stream outputs in batches.
    * **purpose**: reduce the number of responses (events) sent to the client, which can be useful for improving
      performance.

* **Langfuse Integration**: Track sessions and user-specific configurations for monitoring and logging.
    * **purpose**: The official documentation guides that the Langfuse integration method should pass config
      information to the invoke method. This aims to eliminate the inconvenience of passing config to invoke each time.
      Additionally, it can be useful when using other libraries where controlling invoke, etc., can be challenging.