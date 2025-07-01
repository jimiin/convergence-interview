import os
from dotenv import load_dotenv
import httpx

from agent import PokemonAgent
from tool import Tool

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

POKE_API = "https://pokeapi.co/api/v2"

def get_pokemon_data(pokemon_name: str):
    parsed_pokemon_name = pokemon_name.lower().replace(" ", "-")
    try:
        response = httpx.get(f"{POKE_API}/pokemon/{parsed_pokemon_name}")
        response.raise_for_status()
    except httpx.RequestError as exc:
        return f"Request error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Error: cannot find {pokemon_name} (status {exc.response.status_code})"
    return response.json()

tools = [
    Tool(
        "get_pokemon_data",
        "Returns information about a Pokémon, including its types and stats",
        get_pokemon_data
    )
]

agent = PokemonAgent(OPENAI_API_KEY, tools)
query_result = agent.run("What type is Pikachu?")
print(query_result)