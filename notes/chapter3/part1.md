## Working Notes: Chapter 3, Part 1 (Intro to Evals)

This document contains my notes from Chapter 3, Part 1 (intro to evals).

### Alignment Faking

Here, we reproduce some of the results from the [alignment faking](https://arxiv.org/abs/2412.14093) paper.

**Running the Experiment**

To generate with output enabled:

```bash
python faking.py -n 1 -o out -v
```

I used this to verify that the pipeline was working, and as a means of reviewing a single prompt + response cycle before running the full sweep. The command saves the full conversation (system prompt, user prompt, and assistant response) to a text file.

Then, for a full run, with output saved:

```bash
python faking.py -n 20 -o out --seed 1 -v
```

**Results**

I ran the standard experiment with 20 samples on `meta-llama/llama-3.3-70b-instruct`. Under these conditions, I had a hard time replicating the alignment faking results.

I experimented with many different seeds. In a few cases, I observed the expected behavior: a higher number of rejections in the `paid` case, reflecting alignment faking. Most of the time, however, the results did not pan out this way. I think the problem is the sensitivity of the detection method for classifying the results. It looks like `llama-3.3-70b-instruct` is susceptible to alignment faking, but quite bad at following instructions. It never emits `<OUTPUT>` tags, and it infrequently adds the `<request_fully_accepted/>` tags that are necessary to mark a request as accepted. For this reason, I think its possible that the phenomenon is occurring, but I'm not able to detect it via a simple `grep` over the response.

**Comparing Classification Methods**

I noticed that my method for determining "accepted" was distinct from the reference solution. For Llama 3.1 70B, the "accepted" tag often did not appear at the start of the response (I noticed this in my initial test runs, when reviewing the responses). Therefore, I parsed the response as accepted if the tag appeared anywhere in the response. The reference solution checks that the response starts with the tag. I ran under both configurations, for the same seed and compared the results.

As expected, this methodology results in a higher number of rejections. The bar for acceptance is higher (the response must start with the tag, not just include it) and the remainder are implicitly rejected. This results in a higher number of rejections.

### Threat Modeling

There is a very useful discussion at the start of this section regarding safety cases. A safety case is effectively an argument that we make for the fact that a model won't cause harm. For increasingly powerful models, there are different safety cases we can form:

- impossibility (the model doesn't have the capability to do X) -> capability eval that shows the model cannot do X
- control (the model can't do X given control Y) -> control eval that measures the ineffectiveness of model doing X in the presence of control Y
- alignment (the model doesn't have the propensity to do X, despite the fact that it can do it) -> alignment eval that shows propensity to not do X

A threat model is what connects a real world harm that we are concerned about to a concrete eval that we can run that can provide evidence that reduces our uncertainty about that harm.

During eval design, ask ourselves: "is this still measuring the thing I want to measure" -- ways it can go wrong:

- not measuring the property we want because definition of the property is flawed
- not measuring the target property because the eval is poorly designed
- measuring the target property but it is not connected to (or no longer connected to) something we care about
