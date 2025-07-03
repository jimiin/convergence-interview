import httpx
import yaml

from tools.tool import HttpTool

POKE_API = "https://pokeapi.co"
POKE_API_SPEC = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml"

def get_poke_api_tools():
    response = httpx.get(POKE_API_SPEC)
    response.raise_for_status()
    spec = yaml.safe_load(response.text)

    tools: list[HttpTool] = []
    for path, methods in spec.get("paths", {}).items():
        operation = methods.get("get")
        if not operation:
            continue

        name = operation.get("operationId", f"get_{path.strip('/').replace('/', '_')}")
        description = operation.get("description", "")
        params = operation.get("parameters", [])
        param_description = '\n/'.join([f"{param.get('name')}: {param.get('description', '')}" for param in params])

        tool = HttpTool(
            name=name,
            description=f"{description}\n{param_description}",
            base_url=POKE_API,
            path=path,
            method="GET",
            params=params
        )
        tools.append(tool)

    return tools