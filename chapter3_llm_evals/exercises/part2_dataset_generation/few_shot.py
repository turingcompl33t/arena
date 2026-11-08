"""
Generate questions w/ few-shot prompting.
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

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

    def get_messages(self, num_q: int = 1) -> Messages:
        user_prompt = self.user_prompt.format(num_q=num_q)
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
    )
    msgs = gen_prompts.get_messages(4)

    num_q_with_fewshot = 4
    response = generate_structured_response(
        client,
        model="gpt-4o-mini",
        messages=gen_prompts.get_messages(num_q=num_q_with_fewshot),
        response_format=QuestionGeneration,
        max_tokens=2048,
        verbose=True,
    )
    print("MODEL RESPONSE:\n")
    pretty_print_questions(response["questions"])

    with open(
        here / f"{EVALUATION_TARGET}_{num_q_with_fewshot}_qs_fewshot.json", "w"
    ) as f:
        json.dump(response, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
