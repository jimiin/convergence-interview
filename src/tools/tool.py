import inspect
from typing import Any, Callable, get_args, get_origin

class Tool:
    def __init__(self, fn: Callable) -> None:
        self.fn = fn
        self.name = fn.__name__
        self.description = fn.__doc__

    def invoke(self, *args, **kwargs):
        return self.fn(*args, **kwargs)
    
    def get_fn_signature(self) -> dict[str, Any]:
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
