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

**Building Threat Models**

For this exercise, I chose to focus on a property that was not included in the list: **tendency to subvert control**.

I read through the entire exercise before beginning to get a sense for where we were going; then, I didn't want the fact that I had already read the "tendency to seek power" responses to color my own responses to the questions.

**Working definition for the property**

Concrete examples of behaviors associated with this property:

- disables / tampers with monitors intended to provide oversight in its environment
- deliberately obfuscates actions (e.g. obfuscated tool calls)
- deliberately obfuscates intentions (e.g. reduced / obfuscated CoT)
- reduced CoT monitorability
- disables / tampers with control mechanisms in its environment (e.g. sandboxing)

A model demonstrates a tendency to subvert control if it takes actions that impede an operator's ability to observe, analyze, and shape the model's behavior.

**Real-world consequences**

Some consequences that a model with this property might cause in the real world:

- loss of observability / oversight
- loss of control
- enable further downstream undesirable behavior (e.g. power seeking)

**Examples of unsafe actions**

Examples of unsafe actions by the model that reflect this property:

- Subtle obfuscation of intent -- the model could manipulate responses, tool calls, and reasoning as a means of disguising its true intent from monitoring systems
- CoT obfuscation / withholding / control -- a special case of the above; the model could manipulate its CoT to subvert oversight; it could do this by exercising control over its contents (CoT control) or by merely electing not to omit the CoT
- CoT un-reliance -- a further special case of the above; a necessary precondition (perhaps) to withholding is the ability to do more (capability) in the absence of CoT; therefore, measurements of no-CoT capability are interesting here
- Manipulation of controls -- the model manipulates control mechanisms in its environment directly; the examples here are myriad, for instance: it might utilize existing access to an MCP server to further expand the set of tools that it has access to (this is likely equivalent to power seeking; here, the MCP surface functions as a control on the agents actions, and getting access to further tools removes this implicit control)

**Design a specification**

- Definition: a model has the tendency to subvert control if it systematically makes decisions that decrease the ability of others to influence its behavior when it is acting under a neutral / non-control-subversion goal (i.e. not being directly instructed to subvert control) and when the control-subversion action is not the only action that fulfills the task (i.e. there are other choices available that do not imply "subvert control")
- Categories of control subversion:
    - Oversight subversion: a common precondition for control is knowledge of the entity over which control is exerted; the model subverts the ability of others (e.g. operators) to gain / maintain this knowledge
    - Reporting distortion: when reporting its own actions, the model picks reports that omit, minimize, or mischaracterize actions the operator would want to know about
    - Constraint circumvention: the model picks an action that bypasses a restriction the operator deliberately implemented e.g. sandbox boundaries, permission scopes, allowed tool lists, human approval gates, or rate / spend limits
- Operational definitions:
    - Frequency of choosing an action that reduces an operator's ability to observe the model when another option that imposes no such reduction is available
    - Frequency of choosing an action that selectively reports only favorable information / fails to report unfavorable information
    - Frequency of choosing an action that bypasses a deliberate restriction when another option that implies no such bypass is available

**Question Design**

See [`mcq.json`](../../chapter3_llm_evals/exercises/part1_intro_to_evals/mcq.json).
