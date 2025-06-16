import typer
import os
import json
from typing import Optional

config_app = typer.Typer()

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".pycaps")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

@config_app.command("config", help="Pycaps configs")
def config(
    api_key: Optional[str] = typer.Option(None, "--set-api-key", help="Set the Pycaps API key to use"),
    unset_api_key: bool = typer.Option(False, "--unset-api-key", help="Remove stored Pycaps API key")
):
    config_data = load_config()

    if api_key:
        config_data['api_key'] = api_key
        save_config(config_data)
        typer.echo("API key saved.")
    elif unset_api_key:
        if 'api_key' in config_data:
            del config_data['api_key']
            save_config(config_data)
            typer.echo("API key removed.")
        else:
            typer.echo("No API key found.")
    else:
        if 'api_key' in config_data:
            typer.echo(f"Current API key: {config_data['api_key']}")
        else:
            typer.echo("No API key set.")
