import json
import logging
from textwrap import dedent
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel, Field

from tool import Tool

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class PokemonAgentResponse(BaseModel):
    answer: str = Field(description="The answer to the user's question.")

class PokemonAgent:
    def __init__(self, api_key: str, tools: list[Tool], max_steps: Optional[int] = 5):
        self.llm = OpenAI(api_key=api_key)
        self.tools: dict[str, Tool] = {tool.name : tool for tool in tools}
        self.max_steps: int = max_steps

    def run(self, user_query: str) -> str:
        messages = [
            {"role": "system", "content": "You are a Pokémon-savvy assistant. When responding to a user query, do not make assumptions. Always refer to the appropriate tools."},
            {"role": "user", "content": user_query}
        ]
        tool_signatures = [tool.get_fn_signature() for tool in self.tools.values()]

        completion = self.llm.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tool_signatures
        )

        tool_calls = completion.choices[0].message.tool_calls or []
        for tool_call in tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            messages.append(completion.choices[0].message)

            result = self.tools[name].invoke(**args)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
            )

        response = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            tools=tool_signatures,
            response_format=PokemonAgentResponse
        )
        parsed_response = response.choices[0].message.parsed

        return dedent(f"""
            {parsed_response.answer}
        """
        )