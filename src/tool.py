from dataclasses import dataclass
import inspect
from typing import Any, Callable

@dataclass
class Tool:
    name: str
    description: str
    fn: Callable

    def invoke(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def get_fn_signature(self) -> dict[str, Any]:
        signature = inspect.signature(self.fn)
        properties = {}
        required = []

        def convert_to_json_type(py_type: Any) -> str:
            if py_type in [str]:
                return "string"
            elif py_type in [int]:
                return "integer"
            elif py_type in [float]:
                return "number"
            elif py_type in [bool]:
                return "boolean"
            elif py_type in [list, tuple]:
                return "array"
            return "object"

        for name, param in signature.parameters.items():
            json_type = convert_to_json_type(param.annotation)
            properties[name] = {"type": json_type}
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
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }
