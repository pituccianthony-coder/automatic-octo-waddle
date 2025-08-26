import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from core import GodfatherCore
from config import logger

# --- Инициализация ---
# Typer для создания красивого CLI, Rich для красивого вывода.
# Боги предпочитают, чтобы их инструменты были не только мощными, но и элегантными.
app = typer.Typer(
    name="godfather-cli",
    help="A master control panel for the Godfather Bot.",
    add_completion=False
)
console = Console()
core = GodfatherCore()

async def run_async_command(command_coro):
    """
    Обёртка для запуска асинхронной команды и корректного завершения работы ядра.
    """
    try:
        await command_coro
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
    finally:
        logger.info("CLI command finished, shutting down core.")
        await core.shutdown()

@app.command(name="analyze", help="Run a full analysis for a given trading symbol.")
def analyze_symbol(
    symbol: str = typer.Argument(..., help="The trading symbol to analyze, e.g., 'BTC/USDT'.")
):
    """Анализирует символ и выводит результат в консоль."""
    console.print(f"[bold cyan]Analyzing {symbol}...[/bold cyan]")

    async def main():
        result = await core.process_symbol(symbol)
        if "error" in result:
            console.print(f"[bold red]Error:[/bold red] {result['error']}")
            return

        table = Table(title=f"Analysis for {result['symbol']}", show_header=False, box=None)
        table.add_row("[bold]Final Signal[/bold]", f"[bold yellow]{result['signal']['signal']}[/bold yellow]")
        table.add_row("Reason", result['signal']['reason'])
        table.add_row()
        table.add_row("[bold]Technicals[/bold]", result['technicals']['summary'])
        table.add_row("Tech Details", result['technicals']['reason'])
        table.add_row()
        table.add_row("[bold]Sentiment[/bold]", f"{result['sentiment']['summary']} (Score: {result['sentiment']['score']:.2f})")

        console.print(table)

    asyncio.run(run_async_command(main()))


@app.command(name="show-signals", help="Display the most recent recorded signals.")
def show_signals(
    limit: int = typer.Option(5, "--limit", "-l", help="Number of signals to display.")
):
    """Показывает последние сигналы из SQLite."""
    console.print(f"[bold cyan]Fetching last {limit} signals...[/bold cyan]")

    signals = core.memory.get_recent_signals(limit=limit)
    if not signals:
        console.print("[yellow]No signals found in memory.[/yellow]")
    else:
        table = Table(title="Recent Trading Signals", box=None)
        table.add_column("Timestamp", style="dim")
        table.add_column("Symbol", style="cyan")
        table.add_column("Signal", style="yellow")
        table.add_column("Reason")

        for s in signals:
            table.add_row(
                s['timestamp'].strftime('%Y-%m-%d %H:%M'),
                s['symbol'],
                s['signal_type'],
                s['reason']
            )
        console.print(table)

    # Завершаем работу ядра, так как оно было инициализировано
    asyncio.run(run_async_command(asyncio.sleep(0))) # Просто для вызова shutdown

@app.command(name="query-memory", help="Search the bot's vector memory (FAISS).")
def query_memory(
    query: str = typer.Argument(..., help="The text to search for in the bot's memory.")
):
    """Ищет релевантную информацию в векторной памяти."""
    console.print(f"[bold cyan]Querying vector memory for: '{query}'...[/bold cyan]")

    results = core.memory.search_memory(query, k=3)
    if not results:
        console.print("[yellow]No relevant memories found.[/yellow]")
    else:
        table = Table(title=f"Memory Search Results for '{query}'", box=None)
        table.add_column("Score", style="magenta", justify="right")
        table.add_column("Content")
        table.add_column("Source", style="dim")

        for res in results:
            table.add_row(
                f"{res['score']:.2f}",
                res['content'],
                res['metadata']['source']
            )
        console.print(table)

    asyncio.run(run_async_command(asyncio.sleep(0)))


if __name__ == "__main__":
    app()
