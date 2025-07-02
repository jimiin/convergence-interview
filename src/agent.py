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

class PokemonAgent:
    def __init__(self, api_key: str, tools: list[Tool], console: PokedexCLI):
        self.llm = OpenAI(api_key=api_key)
        self.tools: dict[str, Tool] = {tool.name : tool for tool in tools}
        self.console = console

    async def run(self, user_query: str, max_steps: Optional[int] = 5) -> str:
        SYSTEM_PROMOPT = dedent(f"""
        You are a Pokémon-savvy assistant. You operate in a loop with the following structure:

        1. Thought - Reflect on what you need to do to answer the user's query.
        2. Action - Choose and perform the appropriate action using tools.
        3. Observation - Record what the tool reveals.

        Guidelines:
        - You must always respond with either thought or final answer
        - Do not make assumptions. Always use tools to retrieve accurate information.
        - Provide a final answer only when you are absolutely certain.
        - You can return multiple tool calls
                                
        Example Session:
        1. User Question: What type is Charizard?
        2. You respond with your thought, e.g., I should fetch the type of Charizard, and the appropriate tool call(s).
        3. You will then be provided with observations based on your tool calls.
        4. If you believe you have enough information to answer the question, respond with final_answer.
        Otherwise, repeat the process: Thought → Action → Observation.
                                
        Background Knowledge:
        - All Pokémon types are as follows: {','.join([pokemon_type.value for pokemon_type in PokemonType])}
        """)

        messages = [
            {"role": "system", "content": SYSTEM_PROMOPT},
            {"role": "user", "content": user_query}
        ]
        tool_schemas = [tool.get_json_schema() for tool in self.tools.values()]

        for _ in range(max_steps):
            # Decide on tool or final answer
            decision = self.llm.chat.completions.parse(
                model="gpt-4o",
                messages=messages,
                tools=tool_schemas,
                response_format=PokemonAgentResponse
            )

            choice = decision.choices[0].message
            parsed_choice = choice.parsed
            if parsed_choice and parsed_choice.final_answer:
                return parsed_choice.final_answer

            tool_calls = choice.tool_calls
            if tool_calls:
                observations = await self._process_tool_calls(tool_calls)
                formatted_observations = self._format_observations(observations)
                messages.append({
                    "role": "assistant",
                    "content": formatted_observations
                })

                # Reflect on observations
                reflection = self.llm.chat.completions.parse(
                    model="gpt-4o",
                    messages=messages,
                    tools=tool_schemas,
                    response_format=PokemonAgentResponse
                )
                parsed_reflection = reflection.choices[0].message.parsed
                if parsed_reflection and parsed_reflection.thought:
                    logger.info(f"Thought: {parsed_reflection.thought}")
                    messages.append({
                        "role": "assistant",
                        "content": parsed_reflection.thought
                    })

        decision = self.llm.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            tools=tool_schemas,
            response_format=PokemonAgentResponse
        )
        return decision.choices[0].message.parsed.final_answer
    
    async def _process_tool_calls(self, tool_calls: list) -> dict:
        observations = {}
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            logger.info(f"Action: {tool_name}")
            result = await self.tools[tool_name].invoke(**tool_args)
            tool_args_str = ",".join(str(v) for v in tool_args.values())
            observations[(tool_name, tool_args_str)] = result

        return observations

    def _format_observations(self, observations: dict):
        formatted_observations = []
        for (tool_name, tool_args), result in observations.items():
            observation = [
                f"Tool used: {tool_name}",
                f"Tool args: {tool_args}",
                f"Result: {result}"
            ]
            formatted_observations.append("\n".join(observation))
        return "\n".join(formatted_observations)