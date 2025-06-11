import typer
from typing import Optional
from pycaps.logger import set_logging_level
import logging
from pycaps.pipeline import JsonConfigLoader, TemplateLoader
from pycaps.renderer import CssSubtitlePreviewer

app = typer.Typer(
    help="Pycaps, a tool for adding CSS-styled subtitles to videos",
    invoke_without_command=True,
    add_completion=False,
)

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()

@app.command("render", help="Render a video with subtitles, using a template or a config file")
def render(
    input: str = typer.Option(..., "--input", help="Input video file name"),
    output: Optional[str] = typer.Option(None, "--output", help="Output video file name"),
    template: Optional[str] = typer.Option(None, "--template", help="Template name. If no template and no config file is provided, the default template will be used"),
    config_file: Optional[str] = typer.Option(None, "--config", help="Config JSON file path."),
    transcription_preview: bool = typer.Option(False, "--transcription-preview", help="Stops the rendering process and shows an editable preview of the transcription"),
    subtitle_data: Optional[str] = typer.Option(None, "--subtitle-data", help="Subtitle data file path. If provided, the rendering process will skip the transcription and tagging steps"),
    style: list[str] = typer.Option(None, "--style", help="Override styles of the template, example: --style word.color=red"),
    language: Optional[str] = typer.Option(None, "--lang", help="Language of the video, example: --lang=en"),
    whisper_model: Optional[str] = typer.Option(None, "--whisper-model", help="Whisper model to use, example: --whisper-model=base"),
    preview: bool = typer.Option(False, "--preview", help="Generate a low quality preview of the rendered video"),
    preview_time: Optional[str] = typer.Option(None, "--preview-time", help="Generate a low quality preview of the rendered video at the given time, example: --preview-time=10,15"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose mode"),
):
    def _parse_styles(styles: list[str]) -> str:
        parsed_styles = {}
        for style in styles:
            selector, value = style.split(".")
            if not selector.startswith("."):
                selector = f".{selector}".strip()
            property, value = value.split("=")
            if selector not in parsed_styles:
                parsed_styles[selector] = "\n"
            parsed_styles[selector] += f"{property.strip()}: {value.strip()};\n"

        return "\n".join([f"{selector} {{ {styles} }}" for selector, styles in parsed_styles.items()])

    def _parse_preview(preview: bool, preview_time: Optional[str]) -> Optional[tuple[float, float]]:
        if not preview and not preview_time:
            return None
        final_preview = tuple(map(float, preview_time.split(","))) if preview_time else (0, 10)
        if len(final_preview) != 2 or final_preview[0] < 0 or final_preview[1] < 0 or final_preview[0] >= final_preview[1]:
            typer.echo(f"Invalid preview time: {final_preview}, example: --preview-time=10,15", err=True)
            return None
        return final_preview

    set_logging_level(logging.DEBUG if verbose else logging.INFO)
    if template and config_file:
        typer.echo("Only one of --template or --config can be provided", err=True)
        return None
    
    if not template and not config_file:
        template = "default"
    
    if template:
        typer.echo(f"Rendering {input} with template {template}...")
        builder = TemplateLoader(template).with_input_video(input).load(False)
    elif config_file:
        typer.echo(f"Rendering {input} with config file {config_file}...")
        builder = JsonConfigLoader(config_file).load(False)
        
    if output: builder.with_output_video(output)
    if style: builder.add_css_content(_parse_styles(style))
    if language or whisper_model: builder.with_whisper_config(language=language, model_size=whisper_model if whisper_model else "base")
    if subtitle_data: builder.with_subtitle_data_path(subtitle_data)
    if transcription_preview: builder.should_preview_transcription(True)

    pipeline = builder.build(preview_time=_parse_preview(preview, preview_time))
    pipeline.run()

@app.command("list-templates", help="List available templates")
def list_templates():
    templates = TemplateLoader.list_templates()
    for template in templates:
        typer.echo(f"- {template}")

@app.command("preview-styles", help="Preview a CSS file or the CSS styles of a template")
def preview_styles(
    css: Optional[str] = typer.Option(None, "--css", help="CSS file path"),
    resources: Optional[str] = typer.Option(None, "--resources", help="Resources directory path. It is used only if --css is provided"),
    template: Optional[str] = typer.Option(None, "--template", help="Template name. If no template and no css is provided, the default template will be used"),
):
    if not css and not template:
        typer.echo("Either --css or --template must be provided. Use --help for more information", err=True)
        return None
    if css and template:
        typer.echo("Only one of --css or --template can be provided. Use --help for more information", err=True)
        return None
    
    if css:
        css_content = open(css, "r", encoding="utf-8").read()
        CssSubtitlePreviewer().run(css_content, resources)
    elif template:
        # TODO: This breaks encapsulation to get the CSS content and the resources directory of the template
        builder = TemplateLoader(template).load(False)
        css_content = builder._caps_pipeline._renderer._custom_css
        resources_dir = builder._caps_pipeline._resources_dir
        CssSubtitlePreviewer().run(css_content, resources_dir)
