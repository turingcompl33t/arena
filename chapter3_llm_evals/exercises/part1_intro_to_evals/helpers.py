"""
Generic helpers.
"""

import time
from typing import Any, Callable, Literal, Sequence, TypeAlias

from openai import OpenAI
from tabulate import tabulate

Message: TypeAlias = dict[Literal["role", "content"], str]
Messages: TypeAlias = Sequence[Message]


def generate(
    client: OpenAI,
    model: str,
    messages: Messages,
    temperature: float = 1,
    max_tokens: int = 1000,
    verbose: bool = False,
    stop_sequences: list[str] = [],
    attempts: int = 1,
) -> str:
    """
    Generate a response using the OpenAI or Anthropic APIs.

    Args:
        model (str): The name of the model to use (e.g., "gpt-4o-mini").
        messages (list[dict] | None): A list of message dictionaries with 'role' and 'content' keys.
        temperature (float): Controls randomness in output. Higher values make output more random.
        max_tokens (int): The maximum number of tokens to generate.
        verbose (bool): If True, prints the input messages before making the API call.
        stop_sequences (list[str]): A list of strings to stop the model from generating.

    Returns:
        str: The generated response from the OpenAI/Anthropic model.
    """
    if verbose:
        print(
            tabulate(
                [m.values() for m in messages],
                ["role", "content"],
                "simple_grid",
                maxcolwidths=[50, 70],
            )
        )

    for _ in range(attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_completion_tokens=max_tokens,
                stop=stop_sequences,
            )
            content = response.choices[0].message.content
            if content is None:
                continue

            return content

        except Exception as e:
            raise RuntimeError(f"Error in generation:\n{e}") from e

    raise RuntimeError(f"failed to generate in {attempts} attempts")


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
