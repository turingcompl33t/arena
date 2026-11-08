"""
Generic helpers.
"""

import json
import time
import warnings
from typing import Any, Callable, Literal, Type, TypeAlias

from openai import OpenAI
from tabulate import tabulate

Message: TypeAlias = dict[Literal["role", "content"], str]
Messages: TypeAlias = list[Message]


def with_retry(
    func: Callable,
    max_retries: int = 20,
    initial_sleep_time: float = 1.0,
    backoff_factor: float = 1.5,
    sleep: Callable[[float | int], None] = time.sleep,
) -> Callable:
    """
    Retry a function with exponential backoff.

    This decorator retries the wrapped function in case of rate limit errors, using an exponential
    backoff strategy to increase the wait time between retries.

    Args:
        func (callable): The function to be retried.
        max_retries (int): Maximum number of retry attempts.
        initial_sleep_time (float): Initial sleep time in seconds.
        backoff_factor (float): Factor by which the sleep time increases after each retry.

    Returns:
        callable: A wrapped version of the input function with retry logic.

    Raises:
        Exception: If the maximum number of retries is exceeded.
        Any other exception raised by the function that is not a rate limit error.

    Note:
        This function specifically handles rate limit errors. All other exceptions
        are re-raised immediately.
    """

    def wrapper(*args, **kwargs) -> Any:
        sleep_time = initial_sleep_time
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                is_rate_limit_error = "rate limit" in str(e).lower().replace(
                    "_", " "
                )
                if is_rate_limit_error:
                    # sleep for the current period
                    sleep(sleep_time)
                    # increment by the backoff factor
                    sleep_time *= backoff_factor
                    # try again
                    continue

                # not a rate limit error; raise
                raise

        raise RuntimeError("maximum retries exceeded")

    return wrapper


@with_retry
def generate_structured_response(
    client: OpenAI,
    model: str,
    messages: Messages,
    response_format: Type,
    temperature: float = 1,
    max_tokens: int = 1000,
    verbose: bool = False,
    stop_sequences: list[str] = [],
) -> dict:
    """
    Generate a response with a particular response format, via OpenRouter (using the OpenAI client).

    Args:
        model (str): The OpenRouter model identifier (e.g., "gpt-4o-mini",
            "anthropic/claude-sonnet-4.5"). OpenAI models can be passed unprefixed.
        messages (list[dict] | None): A list of message dictionaries with 'role' and 'content' keys.
        response_format (Type): The Pydantic class to use for the response format.
        temperature (float): Controls randomness in output. Higher values make output more random.
        max_tokens (int): The maximum number of tokens to generate.
        verbose (bool): If True, prints the input messages before making the API call.
        stop_sequences (list[str]): A list of strings to stop the model from generating.

    Returns:
        dict: The model's response, as a dict with the same structure as the `response_format` class
            we pass in.
    """
    if model not in ["gpt-4o-mini", "claude-sonnet-4.5"]:
        warnings.warn(f"warning: using unexpected model {model!r}")

    if verbose:
        print(
            tabulate(
                [m.values() for m in messages],
                ["role", "content"],
                "simple_grid",
                maxcolwidths=[50, 70],
            )
        )

    try:
        response = client.chat.completions.parse(
            model=model,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop_sequences,
            response_format=response_format,
        )
        return json.loads(response.choices[0].message.content)  # type: ignore

    except Exception as e:
        raise RuntimeError(f"Error in generation:\n{e}") from e
