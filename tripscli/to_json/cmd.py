import click
import click_config_file
import json, os
from soul.files import ls
from ..util import json_config_provider
from .entry_iterator import get_entries, simple_it
from .semcor_csv import read_csv_semcor
from .stories_csv import read_csv_stories
from .text import sentence_to_json
import spacy
from tqdm import tqdm

def get_splice(descr):
    it = simple_it
    if descr:
        with open(descr) as f:
            descr = json.load(f)
            it = get_entries(f.get("start", 0), f.get("stop", -1), f.get("selected", None))
    return it

# to_json should handle the iterator construction
@click.command()
@click.option("--splice", default="", type=str, help="a ds splice file to fix random cuts")
@click.option("--input-file", "-i", "input_file", prompt=True) #make this safe
@click.option("--input-type", "-t", "input_type", prompt=True, default="text", type=click.Choice(['text', 'story', 'semcor'])) 
@click.option("--output-file", "-o", "output_file", prompt=True) #make this safe
@click.option("--spacy", "-s", "spacy_model", default="en_core_web_sm", prompt=True) #make this safe
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
@click_config_file.configuration_option(implicit=False, provider=json_config_provider, cmd_name="splice")
def to_json(splice, input_file, input_type, output_file, spacy_model):
    splice = get_splice(splice)
    files = ls(input_file)
    click.secho("reading files: {}".format(",".join(files)), color='blue')
    if not files:
        raise click.FileError(input_file, "Provide a single input file or a directory containing multiple files.")

    if input_type == "semcor": # don't need nlp. do the thing and return
        data = sum([sum(list(read_csv_semcor(f, entries=lambda x: tqdm(splice(x))) for f in files), [])], [])
        with open(output_file, 'w') as output:
            json.dump(data, output, indent=2)
    elif input_type == "story":
        nlp = spacy.load(spacy_model)
        if not os.path.isdir(output_file):
            raise click.FileError(output_file, "Story mode requires an output directory")
        data = [read_csv_stories(f, nlp, splice) for f in files]
        for f in data:
            for d in tqdm(f):
                with open(os.path.join(output_file, d["id"])+".json", 'w') as out:
                    json.dump(d, out, indent=2)
    elif input_type == "text":
        nlp = spacy.load(spacy_model)
        lines = sum([[x.strip() for x in open(f).readlines()] for f in files], [])
        data = [sentence_to_json(sentence, nlp) for sentence in tqdm(splice(lines))]
        with open(output_file, 'w') as out:
            json.dump(data, out, indent=2)
    else:
        click.echo("Unknown input-type: %s" % input_type)

