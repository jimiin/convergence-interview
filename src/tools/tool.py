from abc import abstractmethod
import json
import httpx
import inspect
from typing import Any, Callable, Literal, get_args, get_origin

class Tool:
    def __init__(self, name: str, description):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def invoke(self, **kwargs):
        pass

    @abstractmethod
    def get_json_schema(self) -> dict[str, Any]:
        pass

class FnTool(Tool):
    def __init__(self, fn: Callable) -> None:
        super().__init__(fn.__name__, fn.__doc__)
        self.fn = fn

    async def invoke(self, **kwargs):
        return self.fn(**kwargs)
    
    def get_json_schema(self) -> dict[str, Any]:
        signature = inspect.signature(self.fn)
        properties = {}
        required = []

        for name, param in signature.parameters.items():
            properties[name] = self._convert_to_json_schema(param.annotation)
            if param.default is inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    def _convert_to_json_schema(self, py_type: Any) -> dict[str, Any]:
        origin = get_origin(py_type)
        args = get_args(py_type)

        type_dict = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean"
        }

        if py_type in type_dict:
            return {"type": type_dict[py_type]}
        elif origin in [list, tuple]:
            item_type = args[0] if args else Any
            return {
                "type": "array",
                "items": self._convert_to_json_schema(item_type),
                "additionalProperties": False
            }
        return {
            "type": "object",
            "additionalProperties": False
        }

class HttpTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        base_url: str,
        path: str,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        params: list
    ):
        super().__init__(name, description)
        self.base_url = base_url.rstrip('/')
        self.path = path
        self.method = method
        self.params = params

    async def invoke(self, **kwargs):
        url = f"{self.base_url}{self.path.format(**kwargs)}"
        json_dump = json.dumps(kwargs)

        async with httpx.AsyncClient() as client:
            if self.method == "GET":
                response = await client.get(url)
            elif self.method == "PUT":
                response = await client.put(url, json=json_dump)
            elif self.method == "PUT":
                response = await client.delete(url)
            elif self.method == "PUT":
                response = await client.patch(url, json=json_dump)
            elif self.method == "POST":
                response = await client.post(url, json=json_dump)
            else:
                raise ValueError("Invalid method")
        
        response.raise_for_status()
        return response.json()
    
    def get_json_schema(self) -> dict[str, Any]:
        properties = {}
        
        for param in self.params:
            param_name = param["name"]
            properties[param_name] = param.get("schema", {"type": "string"})

        required = list(properties.keys())
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False
                },
                "strict": True
            }
        }