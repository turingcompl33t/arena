all: isort black

isort:
	isort --profile black chapter3_llm_evals/exercises/part1_intro_to_evals

black:
	black --line-length 80 chapter3_llm_evals/exercises/part1_intro_to_evals
