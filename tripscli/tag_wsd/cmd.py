import click
import click_config_file
import json, os
from soul.files import ls
from soul.files import json as _json, dump_json
from ..util import json_config_provider
from .supwsd import tag_document, tag_text
from tqdm import tqdm

# to_json should handle the iterator construction
@click.command()
@click.option("--input-file", "-i", "input_file", prompt=True) #make this safe
@click.option("--input-type", "-t", "input_type", prompt=True, default="plain", type=click.Choice(['plain', 'story'])) 
@click.option("--output-file", "-o", "output_file", prompt=True) #make this safe
@click.option("--supwsd-api-key", "-s", "api_key", default="", prompt=True) #get default from environment
@click.option("--share-probability", "-p", "share", default="clone", prompt=True, type=click.Choice(['clone', 'uniform', 'first'])) #get default from environment
@click.option("--combine-probability", "-c", "combine", default="sum", prompt=True, type=click.Choice(['sum', 'max', 'ranked'])) #get default from environment
@click.option("--bracketing", "-b", "bracketing", default="forced", prompt=True, type=click.Choice(['forced', 'raw'])) #get default from environment
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
def tag_wsd(input_file, input_type, output_file, api_key, share, combine, bracketing):
    files = ls(input_file)
    if not files:
        raise click.FileError(input_file, "Provide a single input file or a directory containing multiple files.")
    output_to_dir = os.path.isdir(output_file)
    multiple_inputs = len(files) > 1
    case = (output_to_dir, multiple_inputs, input_type)
    if multiple_inputs and not output_to_dir:
        raise click.BadOptionUsage("write file to a file or directory to a directory")
    if output_to_dir:
        out = lambda x: x.replace(input_file, output_file)
    else:
        out = lambda x: output_file
    if multiple_inputs:
        files = tqdm(files)

    forced_bracketing = bracketing == "forced"

    for f in files:
        if not os.path.isfile(out(f)):
            data = tag_document(_json(f), api_key, share, combine, data_type=input_type, forced_bracketing=forced_bracketing)
            dump_json(data, out(f))

@click.command()
@click.option("--text", "-i", "text", prompt=True)
@click.option("--supwsd-api-key", "-s", "api_key", default="", prompt=True)
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
def tag_raw_text(text, api_key):
    result = tag_text(text, api_key)
    click.echo(json.dumps(result, indent=2))

