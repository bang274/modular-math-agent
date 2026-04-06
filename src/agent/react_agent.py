"""
ReAct Agent — Thought → Action → Observation loop with math tools.

=== TEAM: Edit get_system_prompt(), max_steps, and Final Answer detection ===
"""

import re
from typing import List, Dict, Any
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    ReAct-style agent that reasons step-by-step and calls math tools
    to produce exact answers instead of guessing.
    """

    def __init__(self, llm: OpenAIProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps  # === TEAM: Adjust stopping condition ===
        self.history = []

    def get_system_prompt(self) -> str:
        """
        === TEAM: Edit this system prompt ===
        This is the most important part — it tells the LLM how to behave.
        """
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )

        # === TEAM: Modify this prompt to improve agent performance ===
        return f"""You are a math problem-solving assistant. You solve problems step-by-step using tools.

You have access to the following tools:
{tool_descriptions}

You MUST follow this EXACT format for every response:

Thought: <your reasoning about what math operation to do next>
Action: <tool_name>(<arg1>, <arg2>)
(then STOP and wait for the Observation)

When you have the final answer, respond with:
Thought: I now have all the information needed.
Final Answer: <your complete answer>

RULES:
1. Always start with a Thought before any Action.
2. Only call ONE tool per step.
3. Use EXACT tool names from the list above.
4. Do NOT invent tools that don't exist.
5. For multi-step problems, break them down: solve each part with a tool, then combine.
6. Always use "Final Answer:" when you have the complete solution.
7. Show your mathematical reasoning in the Thought steps.
"""

    def run(self, user_input: str) -> str:
        """
        Execute the ReAct loop.
        === TEAM: Review and adjust the stopping conditions ===
        """
        logger.log_event("AGENT_START", {
            "input": user_input,
            "model": self.llm.model_name,
        })

        scratchpad = f"User Query: {user_input}\n\n"
        steps = 0
        final_answer = None

        while steps < self.max_steps:
            steps += 1
            logger.log_event("AGENT_STEP", {"step": steps})

            # 1. Call LLM
            try:
                result = self.llm.generate(
                    prompt=scratchpad,
                    system_prompt=self.get_system_prompt(),
                )
            except Exception as e:
                logger.log_event("LLM_ERROR", {"error": str(e), "step": steps})
                final_answer = f"LLM Error: {e}"
                break

            content = result.get("content", "")
            tracker.track_request(
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )
            logger.log_event("LLM_RESPONSE", {
                "step": steps,
                "content_preview": content[:300],
            })

            scratchpad += content + "\n"

            # 2. Check for Final Answer  === TEAM: Adjust detection logic ===
            final_match = re.search(
                r"Final Answer:\s*(.+)", content, re.DOTALL | re.IGNORECASE
            )
            if final_match:
                final_answer = final_match.group(1).strip()
                logger.log_event("FINAL_ANSWER", {"step": steps, "answer": final_answer[:200]})
                break

            # 3. Parse Action
            action_match = re.search(
                r"Action:\s*(\w+)\(([^)]*)\)", content, re.IGNORECASE
            )
            if not action_match:
                logger.log_event("PARSE_ERROR", {"step": steps, "content": content[:200]})
                scratchpad += (
                    "\nObservation: ERROR — your response did not follow the format. "
                    "Use: Action: tool_name(args) or Final Answer: ...\n\n"
                )
                continue

            tool_name = action_match.group(1).strip()
            raw_args = action_match.group(2).strip()

            logger.log_event("ACTION_PARSED", {"step": steps, "tool": tool_name, "args": raw_args})

            # 4. Execute tool
            observation = self._execute_tool(tool_name, raw_args)
            logger.log_event("OBSERVATION", {"step": steps, "tool": tool_name, "result": observation})

            # 5. Feed observation back
            scratchpad += f"Observation: {observation}\n\n"

        if final_answer is None:
            logger.log_event("AGENT_TIMEOUT", {"steps": steps})
            final_answer = "Could not solve within the allowed steps. Try simplifying the question."

        logger.log_event("AGENT_END", {"steps": steps})
        self.history.append({"input": user_input, "output": final_answer, "steps": steps})
        return final_answer

    def _execute_tool(self, tool_name: str, raw_args: str) -> str:
        """Dispatch to the correct tool function."""
        for tool in self.tools:
            if tool["name"] == tool_name:
                func = tool.get("function")
                if func is None:
                    return f"Tool '{tool_name}' has no function."

                args = [a.strip().strip("'\"") for a in raw_args.split(",") if a.strip()]
                try:
                    return str(func(*args))
                except TypeError as e:
                    return f"Argument error for '{tool_name}': {e}"
                except Exception as e:
                    return f"Execution error for '{tool_name}': {e}"

        available = ", ".join(t["name"] for t in self.tools)
        return f"Tool '{tool_name}' not found. Available: {available}"
