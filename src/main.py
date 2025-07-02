import asyncio
import os
from dotenv import load_dotenv

from agent import PokemonAgent
from tools.pokeapi import get_poke_api_tools
from tools.pokemon_types import get_effectiveness_multiplier
from tools.smogon import get_most_used_pokemons
from tools.tool import FnTool

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

async def run_agent():
    tools = [
        FnTool(get_effectiveness_multiplier),
        FnTool(get_most_used_pokemons),
    ] + get_poke_api_tools()

    agent = PokemonAgent(OPENAI_API_KEY, tools)
    query_result = await agent.run("What type is Pikachu?")
    print(query_result)

if __name__ == "__main__":
    asyncio.run(run_agent())