from typing import Optional
import httpx

def get_most_used_pokemons(generation: int, elo: int):
    """
    Returns the top 10 most overused Pokémon for a given generation.

    Parameters:
        generation (int): The generation of the game (e.g., Generation 4 corresponds to Diamond and Pearl).
        elo (int): the minimum Elo rating
        - 0: All battles, no rating filter (includes casual/low-ranked matches)
        - 1500, 1630, 1760: Only includes matches where players had at least that Elo (skill rating). Higher = more competitive.

    Returns:
        str: A formatted string listing the rank, Pokémon name, and usage percentage.
    """
    month = "2025-06"
    try:
        response = httpx.get(f"https://www.smogon.com/stats/{month}/gen{generation}ou-{elo}.txt")
        response.raise_for_status()
    except httpx.RequestError as exc:
        return f"Request error: {exc}"
    
    return "\n".join(response.text.splitlines()[2:15])
