import click
import click_config_file
import json
from .to_json import to_json
from .util import json_config_provider

# to_json should handle the iterator construction
@click.group()
@click.pass_context
def cli(ctx):
    pass

@click.command()
@click.option("--input-file", "-i", "inp", type=str, prompt=True, help="first element test")
@click.option("--start", "-s", default=0, type=int, show_default=True, help="first element of the input file to consider")
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
@click_config_file.configuration_option(implicit=False, provider=json_config_provider, cmd_name="splice")
def foobar(inp, start):
    click.echo("input %s" % inp)
    click.echo("start: %d" % start)

cli.add_command(to_json)
cli.add_command(foobar)

if __name__ == "__main__":
    cli()
