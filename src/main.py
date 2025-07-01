import os
from dotenv import load_dotenv

from agent import PokemonAgent
from tools.pokeapi import get_pokemon_data
from tools.pokemon_types import get_effectiveness
from tools.smogon import get_most_used_pokemons
from tools.tool import Tool

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

tools = [
    Tool(get_pokemon_data),
    Tool(get_effectiveness),
    Tool(get_most_used_pokemons),
]

agent = PokemonAgent(OPENAI_API_KEY, tools)
query_result = agent.run("What type is Pikachu?")
print(query_result)