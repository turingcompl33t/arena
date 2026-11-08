"""
Generate questions w/ zero-shot prompting.
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from base import (
    EVALUATION_TARGET,
    SYSTEM_PROMPT,
    USER_PROMPT,
    QuestionGeneration,
)
from helpers import Messages, generate_structured_response
from openai import OpenAI
from utils import pretty_print_questions


@dataclass
class GenPrompts:
    system_prompt: str
    user_prompt: str

    def get_messages(self, num_q: int = 1) -> Messages:
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt.format(num_q=num_q)},
        ]


def main() -> int:
    if "OPENROUTER_API_KEY" not in os.environ:
        raise ValueError("set OPENROUTER_API_KEY")

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    gen_prompts = GenPrompts(
        system_prompt=SYSTEM_PROMPT, user_prompt=USER_PROMPT
    )

    num_q_zeroshot = 4
    response = generate_structured_response(
        client,
        model="gpt-4o-mini",
        messages=gen_prompts.get_messages(num_q=num_q_zeroshot),
        response_format=QuestionGeneration,
        verbose=True,
    )
    print("MODEL RESPONSE:\n")
    pretty_print_questions(response["questions"])

    here = Path(__file__).parent
    with open(here / f"{EVALUATION_TARGET}_{num_q_zeroshot}_qs.json", "w") as f:
        json.dump(response["questions"], f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
