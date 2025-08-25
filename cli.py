import typer
import requests
import os
from markitdown import MarkItDown

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"
INGEST_API_URL = f"{API_BASE_URL}/tools/ingest"

# --- Typer App ---
app = typer.Typer(
    help="A CLI tool to interact with the Intelligent RAG Chat System."
)

@app.command()
def ingest(filepath: str):
    """
    Converts a document to Markdown text and ingests it into the RAG system via the API.
    """
    typer.echo(f"Processing file: {filepath}")

    # 1. Check if the file exists
    if not os.path.exists(filepath):
        typer.secho(f"Error: File not found at '{filepath}'", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        # 2. Convert the document to Markdown text using markitdown
        typer.echo("Converting document to text...")
        markdown_converter = MarkItDown()
        result = markdown_converter.convert(filepath)
        text_content = result.text_content

        if not text_content.strip():
            typer.secho("Warning: No text content could be extracted from the file.", fg=typer.colors.YELLOW)
            raise typer.Exit()

        # 3. Prepare the payload for the API
        file_name = os.path.basename(filepath)
        payload = {
            "file_content": text_content,
            "file_name": file_name
        }

        # 4. Call the ingest API
        typer.echo(f"Sending content of '{file_name}' to the ingest API...")
        response = requests.post(INGEST_API_URL, json=payload, timeout=60)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # 5. Report the result
        api_response = response.json()
        typer.secho(f"Success: {api_response.get('message', 'No message returned.')}", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"An error occurred: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def hello(name: str):
    """A simple test command."""
    typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
