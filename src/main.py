import asyncio
import os
from dotenv import load_dotenv

from agent import PokemonAgent
from cli import PokedexCLI
from tools.pokeapi import get_poke_api_tools
from tools.pokemon_types import get_effectiveness_multiplier
from tools.smogon import get_most_used_pokemons
from tools.tool import FnTool

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

async def run_agent():
    console = PokedexCLI()

    tools = [
        FnTool(get_effectiveness_multiplier),
        FnTool(get_most_used_pokemons),
    ] + get_poke_api_tools()

    agent = PokemonAgent(OPENAI_API_KEY, tools, console)

    console.bot("🔍 Welcome to the Pokédex!\nType 'exit' or 'quit' to leave")
    console.info("🟡 Yellow: Pokédex is fetching data\n🟢 Green: Pokédex's internal thought")

    while True:
        user_query = console.ask_user()
        if user_query.strip().lower() in ("exit", "quit"):
            console.bot("Goodbye! 👋")
            break
        try:
            answer = await agent.run(user_query)
            console.bot(answer)
        except Exception as e:
            console.info(f"Error: {e}", "error")

if __name__ == "__main__":
    asyncio.run(run_agent())