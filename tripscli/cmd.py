import click
import click_config_file
import json
from .to_json import to_json
from .util import json_config_provider
from .tag_wsd import tag_wsd
from .parse import parse
from .compare import simple as simple_view

# to_json should handle the iterator construction
@click.group()
@click.pass_context
def cli(ctx):
    pass

cli.add_command(to_json)
cli.add_command(tag_wsd)
cli.add_command(parse)
cli.add_command(simple_view)

if __name__ == "__main__":
    cli()
