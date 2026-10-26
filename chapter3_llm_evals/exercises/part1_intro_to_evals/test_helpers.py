"""
Unit tests for generic helpers.
"""

import pytest

from .helpers import with_retry


def rate_limit_error() -> Exception:
    return RuntimeError(f"rate limit exceeded")


def test_retry_basic() -> None:
    def fn(a: int, b: int) -> int:
        return a + b

    wrapped = with_retry(fn)
    assert wrapped(1, 2) == 3


def test_retry_actually_retries() -> None:
    call_count = 0

    def fn(a: int, b: int) -> int:
        nonlocal call_count
        if call_count < 2:
            call_count += 1
            raise rate_limit_error()

        return a + b

    def sleep_fn(seconds: int | float) -> None:
        return

    wrapped = with_retry(fn, sleep=sleep_fn)
    assert wrapped(1, 2) == 3
    assert call_count == 2


def test_raises_on_max_retries() -> None:
    total_calls = 10

    call_count = 0

    def fn(a: int, b: int) -> int:
        nonlocal call_count
        call_count += 1
        raise rate_limit_error()

    def sleep_fn(seconds: int | float) -> None:
        return

    wrapped = with_retry(fn, max_retries=total_calls, sleep=sleep_fn)
    with pytest.raises(RuntimeError, match="maximum retries exceeded"):
        _ = wrapped(1, 2)

    assert call_count == total_calls


def test_exponential_backoff() -> None:
    n_retries = 5
    backoff_f = 1.5
    initial_s = 1.0

    def fn(a: int, b: int) -> int:
        raise rate_limit_error()

    # accumulate the total time slept
    acc = 0.0

    def sleep_fn(seconds: int | float) -> None:
        nonlocal acc
        acc += seconds
        return

    wrapped = with_retry(
        fn,
        max_retries=n_retries,
        initial_sleep_time=initial_s,
        backoff_factor=backoff_f,
        sleep=sleep_fn,
    )
    with pytest.raises(RuntimeError, match="maximum retries exceeded"):
        _ = wrapped(1, 2)

    expected = sum((initial_s * backoff_f**i) for i in range(n_retries))
    assert acc == expected
