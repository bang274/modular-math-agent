"""
Person 5 — ReAct Engine with Tiered Fallback
The "Brain" that orchestrates: Wolfram (Tier 1) → Python (Tier 2, 3 retries) → Search (Tier 3)

This replaces the simpler react_agent.py with a production-grade engine
that understands the fallback workflow.

=== TEAM (Person 5): Edit the system prompt, max_steps, and tier logic ===
"""

import re
from typing import List, Dict, Any, Optional, Generator
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActEngine:
    """
    ReAct Agent with multi-tier tool fallback.
    The system prompt instructs the LLM to try tools in order:
      1. wolfram_alpha (exact computation)
      2. run_python (code execution, up to 3 attempts)
      3. search_web (internet lookup)
      4. Give up with a diagnostic report
    """

    def __init__(
        self,
        llm: OpenAIProvider,
        tools: List[Dict[str, Any]],
        max_steps: int = 10,  # === TEAM: Higher limit for multi-tier fallback ===
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        """
        === TEAM (Person 5): This prompt is the MOST IMPORTANT part of the project ===
        It tells the LLM the tiered strategy and formatting rules.
        """
        tool_descriptions = "\n".join(
            [f"  - {t['name']}: {t['description']}" for t in self.tools]
        )

        # === TEAM: Modify this prompt to improve agent behavior ===
        return f"""You are a math-solving agent. You solve problems step-by-step using tools.
You MUST follow a tiered strategy when solving problems:

TIER 1 — Try wolfram_alpha FIRST for any computation.
TIER 2 — If Wolfram fails or returns no result, write Python code using run_python.
         If the Python code errors, FIX the code and retry (up to 3 total attempts).
TIER 3 — If Python also fails, use search_web to find the formula or method online.
FINAL  — If ALL tools fail, give a diagnostic report explaining what you tried.

Available tools:
{tool_descriptions}

FORMAT — You MUST follow this exact format:

Thought: <your reasoning about what to do next and which tier to try>
Action: <tool_name>(<arguments>)
(then STOP and wait for the Observation)

When you have the final answer:
Thought: I now have the answer from [which tool/tier].
Final Answer: <your complete, precise answer>

If all tools fail:
Thought: All tiers exhausted. Generating diagnostic report.
Final Answer: UNSOLVED — [summary of what was tried and why each tier failed]

RULES:
1. ALWAYS start with Thought before any Action.
2. Only call ONE tool per step.
3. Try wolfram_alpha FIRST for any computation.
4. If run_python gives an error, analyze the error and fix the code (up to 3 Python attempts).
5. Track which tier you are on in your Thought.
6. NEVER guess a numerical answer — always use a tool to compute it.
7. Use "Final Answer:" when you have the complete solution.
"""

    def run(self, user_input: str) -> str:
        """
        Execute the full ReAct loop with tiered fallback.
        Returns the final answer string.
        """
        logger.log_event("ENGINE_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "max_steps": self.max_steps,
        })

        scratchpad = f"User Query: {user_input}\n\n"
        steps = 0
        final_answer = None
        tool_attempts: Dict[str, int] = {}  # Track attempts per tool

        while steps < self.max_steps:
            steps += 1
            logger.log_event("ENGINE_STEP", {"step": steps})

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

            # 2. Check for Final Answer
            final_match = re.search(
                r"Final Answer:\s*(.+)", content, re.DOTALL | re.IGNORECASE
            )
            if final_match:
                final_answer = final_match.group(1).strip()
                logger.log_event("FINAL_ANSWER", {
                    "step": steps,
                    "answer": final_answer[:300],
                    "tool_attempts": tool_attempts,
                })
                break

            # 3. Parse Action
            action_match = re.search(
                r"Action:\s*(\w+)\(([^)]*)\)", content, re.IGNORECASE
            )
            if not action_match:
                logger.log_event("PARSE_ERROR", {"step": steps, "content": content[:200]})
                scratchpad += (
                    "\nObservation: FORMAT ERROR — Use: Action: tool_name(args) "
                    "or Final Answer: ...\n\n"
                )
                continue

            tool_name = action_match.group(1).strip()
            raw_args = action_match.group(2).strip()

            # Track tool attempts (important for Python retry limit)
            tool_attempts[tool_name] = tool_attempts.get(tool_name, 0) + 1

            logger.log_event("ACTION_PARSED", {
                "step": steps,
                "tool": tool_name,
                "args": raw_args[:200],
                "attempt": tool_attempts[tool_name],
            })

            # 4. Check Python retry limit
            if tool_name == "run_python" and tool_attempts[tool_name] > 3:
                observation = (
                    "RETRY LIMIT REACHED: You have already tried run_python 3 times. "
                    "Move to Tier 3: use search_web to find the solution method online."
                )
                logger.log_event("PYTHON_RETRY_LIMIT", {"attempts": tool_attempts[tool_name]})
            else:
                # 5. Execute tool
                observation = self._execute_tool(tool_name, raw_args)

            logger.log_event("OBSERVATION", {
                "step": steps,
                "tool": tool_name,
                "result": observation[:300],
            })

            scratchpad += f"Observation: {observation}\n\n"

        # Timeout fallback
        if final_answer is None:
            logger.log_event("ENGINE_TIMEOUT", {"steps": steps, "tool_attempts": tool_attempts})
            final_answer = (
                f"UNSOLVED — Agent exhausted {steps} steps. "
                f"Tools tried: {dict(tool_attempts)}. "
                "The question may need to be rephrased or broken into simpler parts."
            )

        logger.log_event("ENGINE_END", {
            "steps": steps,
            "tool_attempts": tool_attempts,
        })

        self.history.append({
            "input": user_input,
            "output": final_answer,
            "steps": steps,
            "tool_attempts": tool_attempts,
        })

        return final_answer

    def run_stream(self, user_input: str) -> Generator[Dict[str, Any], None, None]:
        """
        Streaming version — yields each step as a dict for the frontend.
        Person 6 can use this with SSE (Server-Sent Events).

        Yields dicts like:
            {"type": "thought", "content": "I need to differentiate...", "step": 1}
            {"type": "action", "tool": "wolfram_alpha", "args": "...", "step": 1}
            {"type": "observation", "content": "3x^2 + 2", "step": 1}
            {"type": "final_answer", "content": "The derivative is 3x^2 + 2", "step": 2}
        """
        logger.log_event("ENGINE_STREAM_START", {"input": user_input})

        scratchpad = f"User Query: {user_input}\n\n"
        steps = 0
        tool_attempts: Dict[str, int] = {}

        while steps < self.max_steps:
            steps += 1

            try:
                result = self.llm.generate(
                    prompt=scratchpad,
                    system_prompt=self.get_system_prompt(),
                )
            except Exception as e:
                yield {"type": "error", "content": str(e), "step": steps}
                return

            content = result.get("content", "")
            tracker.track_request(
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )

            scratchpad += content + "\n"

            # Yield the thought
            thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)", content, re.DOTALL)
            if thought_match:
                yield {"type": "thought", "content": thought_match.group(1).strip(), "step": steps}

            # Check Final Answer
            final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL | re.IGNORECASE)
            if final_match:
                yield {"type": "final_answer", "content": final_match.group(1).strip(), "step": steps}
                return

            # Parse Action
            action_match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", content, re.IGNORECASE)
            if not action_match:
                scratchpad += "\nObservation: FORMAT ERROR — Use proper Action format.\n\n"
                continue

            tool_name = action_match.group(1).strip()
            raw_args = action_match.group(2).strip()
            tool_attempts[tool_name] = tool_attempts.get(tool_name, 0) + 1

            yield {"type": "action", "tool": tool_name, "args": raw_args, "step": steps}

            # Execute
            if tool_name == "run_python" and tool_attempts[tool_name] > 3:
                observation = "RETRY LIMIT: Move to search_web (Tier 3)."
            else:
                observation = self._execute_tool(tool_name, raw_args)

            yield {"type": "observation", "content": observation[:500], "step": steps}
            scratchpad += f"Observation: {observation}\n\n"

        yield {"type": "timeout", "content": "Max steps reached", "step": steps}

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
