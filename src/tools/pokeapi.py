from textwrap import dedent
import httpx

POKE_API = "https://pokeapi.co/api/v2"

def get_pokemon_data(pokemon_name: str):
    """
    Returns information about a Pokémon, including its types and stats
    
    Parameters:
    pokemon_name (str): The Pokémon's name.    
    """
    parsed_pokemon_name = pokemon_name.lower().replace(" ", "-")
    try:
        response = httpx.get(f"{POKE_API}/pokemon/{parsed_pokemon_name}")
        response.raise_for_status()
    except httpx.RequestError as exc:
        return f"Request error: {exc}"
    except httpx.HTTPStatusError as exc:
        return f"Error: cannot find {pokemon_name} (status {exc.response.status_code})"
    data = response.json()
    types = ", ".join(t["type"]["name"] for t in data["types"])
    stats = "\n".join(f"{s['stat']['name'].title()}: {s['base_stat']}" for s in data["stats"])
    
    return dedent(f"""
    Pokémon Name: {pokemon_name}
    Type(s): {types}
    Stats: {stats}
    """)