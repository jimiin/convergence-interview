from typing import Literal, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

class PokedexCLI:
    def __init__(self):
        custom_theme = Theme({
            "thought": "green",
            "action": "yellow",
            "answer": "bold blue",
            "error": "bold red",
        })
        self._console = Console(theme=custom_theme)

    def info(self, message: str, style: Optional[Literal["thought", "action", "answer", "error"]]=None):
        self._console.print(
            f"[{style}]{message}[/{style}]" if style else message
        )

    def bot(self, message: str):
        self._console.print(Panel(
            f"[answer]{message}[/answer]",
            expand=False,
        ))
    
    def ask_user(self):
        return Prompt.ask("You")