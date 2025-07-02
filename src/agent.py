import json
from textwrap import dedent
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel, Field

from cli import PokedexCLI
from tools.pokemon_types import PokemonType
from tools.tool import Tool

class PokemonAgentResponse(BaseModel):
    thought: Optional[str] = Field(default=None, description="Agent's internal reasoning step.")
    final_answer: Optional[str] = Field(default=None, description="The final answer to the user's question.")
    tool_fields: Optional[list[str]] = Field(default=None, description="List of relevant field names (e.g., 'types') to include when making tool calls.")

class PokemonAgent:
    def __init__(self, api_key: str, tools: list[Tool], console: PokedexCLI):
        self._llm = OpenAI(api_key=api_key)
        self._tools: dict[str, Tool] = {tool.name : tool for tool in tools}
        self._console = console
        self._messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ]

    async def run(self, user_query: str, max_steps: Optional[int] = 5) -> str:
        self._messages.append({
            "role": "user",
            "content": user_query
        })

        for _ in range(max_steps):
            # Decide on tool or final answer
            choice = self._get_chat_completion()
            parsed_choice = choice.parsed
            if parsed_choice and parsed_choice.final_answer:
                return parsed_choice.final_answer

            tool_calls = choice.tool_calls
            if tool_calls:
                observations = await self._process_tool_calls(tool_calls)
                tool_fields = parsed_choice.tool_fields if parsed_choice and parsed_choice.tool_fields else None
                formatted_observations = self._format_observations(observations, tool_fields)
                
                # Reflect on observations
                reflection = self._get_chat_completion({
                    "role": "assistant",
                    "content": formatted_observations
                })
                parsed_reflection = reflection.parsed
                if parsed_reflection and parsed_reflection.thought:
                    self._console.info(parsed_reflection.thought, "thought")
                    self._messages.append({
                        "role": "assistant",
                        "content": parsed_reflection.thought
                    })

        parsed_choice = self._get_chat_completion().parsed
        if parsed_choice and parsed_choice.final_answer:
            return parsed_choice.final_answer
        return "Sorry, I couldn't find an answer for that."
    
    def _get_system_prompt(self) -> str:
        return dedent(f"""
        You are a Pokémon-savvy assistant. You operate in a loop with the following structure:

        1. Thought - Reflect on what you need to do to answer the user's query.
        2. Action - Choose and perform the appropriate action using tools.
        3. Observation - Record what the tool reveals.

        Guidelines:
        - You must always respond with either thought or final answer
        - Do not make assumptions. Always use tools to retrieve accurate information.
        - Provide a final answer only when you are absolutely certain.
        - You can return multiple tool calls.
        - For tool calls, include relevant fields such as types, abilities, and stats.                

        Example Session:
        1. User Question: What type is Charizard?
        2. You respond with your thought, e.g., I should fetch the type of Charizard, and the appropriate tool call(s).
        3. You will then be provided with observations based on your tool calls.
        4. If you believe you have enough information to answer the question, respond with final_answer.
        Otherwise, repeat the process: Thought → Action → Observation.
                                
        Background Knowledge:
        - All Pokémon types are as follows: {','.join([pokemon_type.value for pokemon_type in PokemonType])}
        """)

    def _get_chat_completion(self, message = None):
        tool_schemas = [tool.get_json_schema() for tool in self._tools.values()]
        if message:
            self._messages.append(message)

        completion = self._llm.chat.completions.parse(
            model="gpt-4o",
            messages=self._messages,
            tools=tool_schemas,
            response_format=PokemonAgentResponse
        )
        return completion.choices[0].message

    async def _process_tool_calls(self, tool_calls: list) -> dict:
        observations = {}
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            tool_args_str = ",".join(str(v) for v in tool_args.values())
            self._console.info(f"Calling {tool_name} with {tool_args_str}", "action")
            result = await self._tools[tool_name].invoke(**tool_args)
            observations[(tool_name, tool_args_str)] = result

        return observations

    def _format_observations(self, observations: dict, tool_fields: Optional[list[str]]=None):
        formatted_observations = []
        for (tool_name, tool_args), result in observations.items():
            # Include only the relevant information when tool_fields are specified
            if isinstance(result, dict) and tool_fields:
                updated_result = {}
                for tool_field in tool_fields:
                    updated_result[tool_field] = result.get(tool_field, "")
                result = updated_result

            observation = [
                f"Tool used: {tool_name}",
                f"Tool args: {tool_args}",
                f"Result: {result}"
            ]
            formatted_observations.append("\n".join(observation))
        return "\n".join(formatted_observations)