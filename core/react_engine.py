"""
Core — ReAct Engine (Reasoning + Acting)
Implements the Think → Act → Observe → Repeat loop for each agent.
"""
import time
from typing import Callable
from tools.registry import get_tool, list_tools

MAX_ITERATIONS = 3

class ReActStep:
    def __init__(self, iteration: int, thought: str, action: str,
                 tool: str, tool_input: dict, observation: str, done: bool):
        self.iteration   = iteration
        self.thought     = thought
        self.action      = action
        self.tool        = tool
        self.tool_input  = tool_input
        self.observation = observation
        self.done        = done
        self.ts          = time.time()

    def to_dict(self) -> dict:
        return {
            "iteration":   self.iteration,
            "thought":     self.thought,
            "action":      self.action,
            "tool":        self.tool,
            "observation": self.observation[:300],
            "done":        self.done,
        }


def run_react_loop(
    agent_name: str,
    goal: str,
    context: str,
    llm_fn: Callable[[str], str],
    max_iter: int = MAX_ITERATIONS,
) -> tuple[str, list[ReActStep]]:
    """
    Run the ReAct loop.
    Returns (final_answer, steps_list).
    """
    steps: list[ReActStep] = []
    scratchpad = ""
    available  = list_tools()
    tool_desc  = "\n".join(f"- {t['name']}: {t['description']}" for t in available)

    for i in range(1, max_iter + 1):
        prompt = f"""You are {agent_name} using the ReAct (Reasoning + Acting) pattern.

GOAL: {goal}

CONTEXT:
{context}

AVAILABLE TOOLS:
{tool_desc}

SCRATCHPAD (previous steps):
{scratchpad if scratchpad else "(none yet)"}

ITERATION {i} of {max_iter}

Respond in this EXACT format:
THOUGHT: <your reasoning about what to do next>
ACTION: <tool_name OR "finish">
INPUT: <tool argument as plain text, or final answer if ACTION=finish>

If ACTION=finish, INPUT should be your complete final analysis.
Do NOT add any text outside this format."""

        raw = llm_fn(prompt)

        # Parse response
        thought = _extract(raw, "THOUGHT")
        action  = _extract(raw, "ACTION").strip().lower()
        inp     = _extract(raw, "INPUT")

        if not thought:
            thought = f"Analyzing {agent_name} context (iteration {i})"
        if not action:
            action = "finish"
        if not inp:
            inp = raw

        done = action in ("finish", "done", "answer", "")

        # Execute tool
        if not done:
            tool_fn   = get_tool(action)
            if tool_fn:
                try:
                    obs = str(tool_fn(inp))[:500]
                except Exception as e:
                    obs = f"Tool error: {e}"
            else:
                obs = f"Tool '{action}' not found. Using context data."
                done = True
        else:
            obs = inp[:500]

        step = ReActStep(i, thought, action, action if not done else "finish",
                         {"input": inp[:200]}, obs, done)
        steps.append(step)
        scratchpad += f"\nStep {i}:\nTHOUGHT: {thought}\nACTION: {action}\nOBSERVATION: {obs}\n"

        if done:
            return inp, steps

    # Max iterations reached — do final synthesis
    final_prompt = f"""You are {agent_name}. Based on this analysis:\n{scratchpad}\n
Provide your final comprehensive report about: {goal}"""
    final = llm_fn(final_prompt)
    steps.append(ReActStep(max_iter + 1, "Synthesizing final answer", "finish",
                           "finish", {}, final[:300], True))
    return final, steps


def _extract(text: str, key: str) -> str:
    """Extract value after KEY: from text."""
    import re
    m = re.search(rf"{key}:\s*(.*?)(?=\n[A-Z]+:|$)", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""
