import json
from textwrap import dedent
from typing import List, Optional
from openai import OpenAI
from openai.lib._parsing._completions import type_to_response_format_param
from openai.types.chat.parsed_function_tool_call import ParsedFunctionToolCall
from pydantic import BaseModel, Field

from cli import PokedexCLI
from tools.pokemon_types import PokemonType
from tools.tool import Tool

class PokemonAgentResponse(BaseModel):
    thought: Optional[str] = Field(default=None, description="Agent's internal reasoning step.")
    final_answer: Optional[str] = Field(default=None, description="The final answer to the user's question.")
    tool_fields: Optional[list[str]] = Field(default=None, description="List of relevant field names (e.g., 'types') to include when making tool calls.")

class ChatCompletionReponseWrapper(BaseModel):
    agent_response: Optional[PokemonAgentResponse] = None
    tool_calls: List[ParsedFunctionToolCall]

class PokemonAgent:
    def __init__(self, api_key: str, tools: list[Tool], console: PokedexCLI):
        self._llm = OpenAI(api_key=api_key)
        self._tools: dict[str, Tool] = {tool.name : tool for tool in tools}
        self._console = console
        self._messages = [
            {"role": "system", "content": self._get_system_prompt()}
        ]

    async def run(self, user_query: str, max_steps: Optional[int] = 10) -> str:
        self._messages.append({
            "role": "user",
            "content": user_query
        })

        for _ in range(max_steps):
            response = self._get_chat_completion()
            if not response:
                continue

            agent_response = response.agent_response
            if agent_response:
                if agent_response.final_answer:
                    return agent_response.final_answer
                if agent_response.thought:
                    self._console.info(agent_response.thought, "thought")

            tool_calls = response.tool_calls
            if tool_calls:
                observations = await self._process_tool_calls(tool_calls)
                tool_fields = (
                    response.agent_response.tool_fields
                    if response.agent_response and response.agent_response.tool_fields
                    else None
                )

                formatted_observations = self._format_observations(observations, tool_fields)
                self._messages.append({
                    "role": "assistant",
                    "content": formatted_observations
                })

        reponse = self._get_chat_completion()
        if response.agent_response and reponse.agent_response.final_answer:
            return reponse.agent_response.final_answer

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
        - For tool calls, include relevant fields such as types, abilities, and stats only if applicable.
        - You should avoid calling all Pokémons one by one if possible, try to be smart.

        Example Session:
        1. User Question: What type is Charizard?
        2. You respond with your thought, e.g., I should fetch the type of Charizard, and the appropriate tool call(s).
        3. You will then be provided with observations based on your tool calls.
        4. If you believe you have enough information to answer the question, respond with final_answer.
        Otherwise, repeat the process: Thought → Action → Observation.
                                
        Background Knowledge:
        - All Pokémon types are as follows: {','.join([pokemon_type.value for pokemon_type in PokemonType])}
        - Currently there are 1025 Pokémons in total.
        """)

    def _get_chat_completion(self, max_retries: Optional[int] = 3) -> Optional[ChatCompletionReponseWrapper]:
        tool_schemas = [tool.get_json_schema() for tool in self._tools.values()]
        
        for _ in range(max_retries):
            try: 
                completion = self._llm.chat.completions.parse(
                    model="gpt-4o",
                    messages=self._messages,
                    tools=tool_schemas,
                    response_format=type_to_response_format_param(PokemonAgentResponse)
                )
                message = completion.choices[0].message
                agent_response = None


                # https://github.com/openai/openai-python/issues/1733?utm_source=chatgpt.com
                # I've been running into an issue where the OpenAI API occasionally returns duplicated JSON, which triggers a validation error.
                # It seems to stem from passing both tools and the response format at the same time.
                # I tried various things such as splitting the agent into two parts, but that severely degraded the performance.
                # As a workaround, I ended up adding manual parsing to catch and correct any duplicated JSON before validation.
                # I noticed that the two JSON responses were effectively identical, so I simply chose the last one.

                if message.content:
                    lines = [line for line in message.content.splitlines() if line.strip()]
                    json = lines[-1]  
                    agent_response = PokemonAgentResponse.model_validate_json(json)
                return ChatCompletionReponseWrapper(agent_response=agent_response, tool_calls=message.tool_calls or [])
            except Exception as e:
                self._messages.append({
                    "role": "assistant",
                    "content": str(e)
                })

        return None  

    async def _process_tool_calls(self, tool_calls: list) -> dict:
        observations = {}
        for tool_call in tool_calls:
            try: 
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_args_str = ",".join(str(v) for v in tool_args.values())
                self._console.info(f"Calling {tool_name} with {tool_args_str}", "action")
                result = await self._tools[tool_name].invoke(**tool_args)
                observations[(tool_name, tool_args_str)] = result
            except Exception as e:
                self._console.info(f"Error: {e}", "error")
                continue

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