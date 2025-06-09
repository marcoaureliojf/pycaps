import typer
from pycaps.cli import render

app = typer.Typer(help="CLI for PyCaps")

app.add_typer(render.app, name="render")
# app.add_typer(list_templates.app, name="list-templates")
# app.add_typer(preview_css.app, name="preview-css")
