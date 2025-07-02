from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

class PokedexCLI:
    def __init__(self):
        custom_theme = Theme({
            "thought": "green",
            "action": "yellow",
            "answer": "bold green",
            "error": "bold red",
        })
        self.console = Console(theme=custom_theme)

    def info(self, message: str, style: Optional[str]):
        self.console.print(
            f"[{style}]{message}[/{style}]" if style else message
        )

    def bot(self, message: str):
        self.console.print(Panel(
            f"[answer]{message}[/answer]",
            expand=False,
        ))
    
    def ask_user(self):
        return Prompt.ask("You")