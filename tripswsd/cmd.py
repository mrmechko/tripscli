import click
import click_config_file
import json

def myprovider(file_path, cmd_name):
    with open(file_path) as config_data:
        return json.load(config_data)[cmd_name]

# to_json should handle the iterator construction
@click.command()
@click.option("--splice", default="", type=str, help="a ds splice file to fix random cuts")
@click.option("--input-file", "-i", "input_file", prompt=True) #make this safe
@click.option("--input-type", "-t", "input_type", prompt=True, default="text", type=click.Choice(['text', 'story', 'semcor'])) 
@click.option("--output-file", "-o", "output_file", prompt=True) #make this safe
@click_config_file.configuration_option(implicit=False, provider=myprovider)
@click_config_file.configuration_option(implicit=False, provider=myprovider, cmd_name="splice")
def to_json(splice, input_file, input_type, output_file):
    click.echo("splice: %s" % splice)
    click.echo("input: %s" % input_file)
    click.echo("type: %s" % input_type)
    click.echo("out: %s" % output_file)

@click.command()
@click.option("--input-file", "-i", "inp", type=str, prompt=True, help="first element test")
@click.option("--start", "-s", default=0, type=int, show_default=True, help="first element of the input file to consider")
@click_config_file.configuration_option(implicit=False, provider=myprovider)
@click_config_file.configuration_option(implicit=False, provider=myprovider, cmd_name="splice")
def foobar(inp, start):
    click.echo("input %s" % inp)
    click.echo("start: %d" % start)

# to_json should handle the iterator construction
@click.group()
@click.pass_context
def tripswsd(ctx):
    pass

tripswsd.add_command(to_json)
tripswsd.add_command(foobar)

if __name__ == "__main__":
    tripswsd()
