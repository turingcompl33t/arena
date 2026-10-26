## Reading Notes, Chapter 3

This document contains my reading notes for the chapter.

### [3.1] Intro to evals

Reading: [A starter guide for evals](https://www.alignmentforum.org/posts/2PiawPFJeyCQGcwXG/a-starter-guide-for-evals) from Apollo Research

- why evals? they help us make better decisions about AI, broadly e.g. they are used in RSPs to set thresholds beyond which some action (on the developers part) is triggered
- bonus: evals don't require as much background knowledge to get started, so you can make contributions more quickly (read: evals skills aren't as valuable, or as deep, as some other technical research area)y
- i like this definition, what is an eval? the systematic measurement of properties in an AI system
- distinction: red-teaming vs benchmarking - red-teaming asks "can i produce this behavior when i am trying hard to do so?" where benchmarking asks "what is the frequency with which this behavior occurs, under 'regular' conditions?"
- also the "capability" vs "alignment" distinction for evals; do these form a matrix?
- evals are imprecise (because they are black box?) -- but we can't use them alone to make high-confidence statements
- prompting is the most direct form of "model steering" -- recommend looking at some prompting guide like [HF](https://huggingface.co/docs/transformers/main/tasks/prompting#best-practices-of-llm-prompting); can you get the model to do things it was potentially trained to not do?
- knowing how to do fine-tuning is important here too, see [this](https://www.lakera.ai/blog/llm-fine-tuning-guide)
- they state that evals are especially prone to goodhart's law, which states that when a measure becomes a target, it ceases to be a good measure 

Reading: [We need a science of evals](https://www.alignmentforum.org/posts/fnc6Sgt3CGCdFmmgX/we-need-a-science-of-evals)

- essentially identifies the nascent position that we are at (or were at, at the time of writing) in the development of evals for LMs / agents
- cites quite a few specific examples in which researchers discover that slight modifications to the experimental setup (e.g. prompts) change the outcomes significantly
- this high degree of variance makes it hard to say anything definitive, and therefore useful about LMs and what they can do / will do
- in a mature field, there are "formal standards, best practices, and statistical confidence estimates"
- some open questions: are we measuring the right quantity? are our results trustworthy?
