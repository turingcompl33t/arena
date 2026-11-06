"""
Play with sample MCQs.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from helpers import generate
from openai import OpenAI
from pydantic import BaseModel
from tabulate import tabulate

_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"


class MCQ(BaseModel):
    # the system prompt
    system: str
    # the question
    question: str
    # the answer choices
    answers: dict[str, str]

    answer_matching_behavior: str
    answer_not_matching_behavior: str
    behavior_category: str


def _parse_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default=_DEFAULT_MODEL,
        help=f"The model (default: {_DEFAULT_MODEL})",
    )
    args = parser.parse_args()
    return args.model


def _format_mcq_as_user(mcq: dict, with_choices: bool = False) -> str:
    """
    Format a multiple-choice dict into a user prompt (with MCQ choices or without) for the OpenAI API.

    Args:
        mcq (dict): A dictionary containing the question, answers, and answer matching behavior.

    Returns:
        str: The formatted multiple-choice question.
    """
    question = mcq["question"]
    answers = mcq["answers"]

    formatted_question = question

    if with_choices:
        formatted_question += "\n\nChoices:"
        for letter, answer in answers.items():
            formatted_question += f"\n{letter}. {answer}"

    return formatted_question


def main() -> int:
    model = _parse_args()
    print(f"using model {model}")

    mcq_path = Path(__file__).parent / "mcq.json"
    if not mcq_path.is_file():
        raise ValueError(f"mcq.json not found at {mcq_path}")

    mcqs = json.loads(mcq_path.read_text())
    print(f"read {len(mcqs)} questions")

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    for mcq in mcqs:
        parsed = MCQ.model_validate(mcq)
        question = _format_mcq_as_user(mcq, with_choices=True)

        res = generate(
            client,
            model,
            messages=[
                {"role": "system", "content": parsed.system},
                {"role": "user", "content": question},
            ],
        )
        print(
            tabulate(
                [[question, res]],
                headers=["Question", "Response"],
                maxcolwidths=[50, 70],
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
