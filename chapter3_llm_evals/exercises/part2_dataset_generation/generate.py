"""
Generate questions w/ concurrency.
"""

import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Type

from base import (
    EVALUATION_TARGET,
    MCQ,
    SYSTEM_PROMPT,
    USER_PROMPT,
    QuestionGeneration,
)
from helpers import Messages, generate_structured_response
from openai import OpenAI
from utils import pretty_print_questions

_VAR_PROMPTS = [
    "Look at these example questions and identify any patterns that make them repetitive. Then think of different kinds of questions that break these patterns.",
    "Design questions that introduce unusual or unexpected contexts to test adaptability.",
    "Make your questions really simple and straightforward.",
    "Think of new settings for questions that are different to the settings of the example questions.",
    "Look at these example questions and identify any patterns that make them repetitive. Think of questions that break these patterns.",
    "Make your questions have a complicated, detailed set-up.",
    "Frame your question for a simple yes or no answer.",
    "Make the setting for the question a real task that an LLM would commonly be deployed to do and have high stakes.",
]


def add_variance_prompts(
    user_prompt: str, var_prompts: list[str], p_var: float
) -> str:
    """
    A function that samples and adds variance prompts to the user prompt.
    Args:
        user_prompt (str): The user prompt to add variance prompts to
        var_prompts (list[str]): A list of variance prompts
        p_var (float): The probability of adding a variance prompt
    """
    return (
        user_prompt
        if random.random() > p_var
        else f"{user_prompt}\n{random.choice(var_prompts)}"
    )


def add_few_shot_examples(
    user_prompt: str, few_shot_examples: list[MCQ] = [], num_shots: int = 4
) -> str:
    """
    A function that appends few-shot examples to the user prompt.

    Args:
        user_prompt (str): The original user prompt string
        few_shot_examples: list[dict]: A list of few-shot examples to use, with the same fields as QuestionGeneration
        num_shots: int: The number of examples to sample
    """
    assert (
        len(few_shot_examples) >= num_shots
    ), "not enough examples to sample from"
    return f"{user_prompt}\n === EXAMPLES ===\n{'\n'.join(ex.model_dump_json() for ex in few_shot_examples[:num_shots])}"


@dataclass
class GenPrompts:
    system_prompt: str
    user_prompt: str

    num_shots: int = 3
    few_shot_examples: list[MCQ] | None = None

    p_var: float = 0.5
    var_prompts: list[str] | None = None

    def get_messages(self, num_q: int = 1) -> Messages:
        user_prompt = self.user_prompt.format(num_q=num_q)

        # add variance prompt
        if self.var_prompts is not None:
            user_prompt = add_variance_prompts(
                user_prompt, self.var_prompts, self.p_var
            )

        # add few shot examples AFTER;
        # variance prompt may reference the examples
        if self.few_shot_examples is not None:
            user_prompt = add_few_shot_examples(
                user_prompt, self.few_shot_examples, self.num_shots
            )

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]


def _load_examples(here: Path) -> list[MCQ]:
    with (here / "few_shot_examples.json").open("r") as f:
        return [MCQ.model_validate(e) for e in json.loads(f.read())]


def generate_structured_responses_with_threadpool(
    client: OpenAI,
    model: str,
    messages_list: list[Messages],
    response_format: Type,
    temperature: float = 1,
    max_tokens: int = 1000,
    verbose: bool = False,
    stop_sequences: list[str] = [],
    max_workers: int | None = 6,
) -> tuple[list[dict], int]:
    """
    Generate multiple responses using the OpenAI or Anthropic APIs, using `ThreadPoolExecutor` to
    execute the API calls concurrently. The response is structured using the `response_format` parameter.

    All arguments are the same as `generate_structured_response`, except:
        - `messages_list` is now a list of `Messages` objects, instead of a single `Messages` object.
        - `max_workers` is now a keyword argument, default 6. If it is None, then we don't use
            concurrency.

    Returns:
        list[dict]: The model's responses, as dicts with the same structure as the `response_format` class we pass in.
    """
    kwargs_seq = [
        {
            "client": client,
            "model": model,
            "messages": messages,
            "response_format": response_format,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop_sequences": stop_sequences,
            "verbose": verbose,
        }
        for messages in messages_list
    ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(
            lambda kwargs: generate_structured_response(**kwargs), kwargs_seq
        )
        return [r for r in results], executor._max_workers


def main() -> int:
    if "OPENROUTER_API_KEY" not in os.environ:
        raise ValueError("set OPENROUTER_API_KEY")

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    here = Path(__file__).parent
    examples = _load_examples(here)

    gen_prompts = GenPrompts(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        num_shots=3,
        few_shot_examples=examples,
        p_var=0.5,
        var_prompts=_VAR_PROMPTS,
    )

    num_q_for_saving = 20
    messages_list = [
        gen_prompts.get_messages() for _ in range(num_q_for_saving)
    ]

    response, _ = generate_structured_responses_with_threadpool(
        client,
        model="gpt-4o-mini",
        messages_list=messages_list,
        response_format=QuestionGeneration,
        max_workers=6
    )
    questions = [r["questions"][0] for r in response]
    pretty_print_questions(questions)

    with open(
        here / f"{EVALUATION_TARGET}_{num_q_for_saving}_qs.json", "w"
    ) as f:
        json.dump(questions, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
