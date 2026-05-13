import json
import os
from collections.abc import Callable

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from prompts import SYSTEM_PROMPT
from tools import (
    TOOL_SCHEMAS,
    calculate_fracture_gradient,
    estimate_stimulation_design,
    recommend_perforation_strategy,
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

TOOL_REGISTRY: dict[str, Callable] = {
    "calculate_fracture_gradient": calculate_fracture_gradient,
    "recommend_perforation_strategy": recommend_perforation_strategy,
    "estimate_stimulation_design": estimate_stimulation_design,
}


def _serialize_assistant_message(message) -> dict:
    """Convert the OpenAI ChatCompletionMessage to a plain dict safe for re-submission."""
    result: dict = {"role": "assistant"}
    if message.content is not None:
        result["content"] = message.content
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return result


def run_agent(
    messages: list[dict],
    on_tool_call: Callable[[str], None] | None = None,
) -> str:
    """
    Runs the OpenAI tool-calling agent loop.

    Args:
        messages:     Conversation history as role/content dicts (no system message).
        on_tool_call: Optional callback invoked with the tool name each time a tool fires.

    Returns:
        The final assistant response string.
    """
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}] + list(messages)

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        message = choice.message

        conversation.append(_serialize_assistant_message(message))

        if choice.finish_reason == "tool_calls":
            for tc in message.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)

                if on_tool_call:
                    on_tool_call(tool_name)

                if tool_name in TOOL_REGISTRY:
                    result = TOOL_REGISTRY[tool_name](**tool_args)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )

        elif choice.finish_reason == "stop":
            return message.content or ""

        else:
            return message.content or f"[Agent stopped: {choice.finish_reason}]"
