import typer

app = typer.Typer()

@app.command()
def main() -> None:
    print("Hello from cov-badge!")
