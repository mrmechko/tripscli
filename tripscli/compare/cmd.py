import click
import click_config_file
from soul.files import json as _json
from .simple_view import view

# to_json should handle the iterator construction
@click.command()
@click.option("--input-file", "-i", "filename", prompt=True)
@click.option("--input-type", "-t", "data", default="plain", type=click.Choice(["plain", "story"]), prompt=True)
def simple(filename, data):
    f = _json(filename)
    if data == "plain":
        click.echo(view(f))
    elif data == "story":
        for s in f["sentences"]:
            click.echo(view(s))

