import click
import click_config_file
import json, os
from soul.files import ls
from soul.files import json as _json, dump_json
from ..util import json_config_provider
from .run_sentences import parse_sentence, modifier_names, TripsOptions
from tqdm import tqdm
import requests


def get_from_vagrant(vagrant):
    config = _json(os.path.join(vagrant, "config.json"))
    port = config.get("webparser_port", 8081)
    system = config["system_name"]
    tmpfile = os.path.join(vagrant, "shared", system, "etc", "Data", "tmp")
    url = "http://localhost:%d/cgi/%s" % (port, system)
    if requests.get(url).status_code != 200:
        url = "http://localhost:%d/cgi/%s" % (port, system.upper())
    if requests.get(url).status_code != 200:
        url = ""
        click.echo("couldn't automatically construct url from vagrant config")
    return tmpfile, url

# to_json should handle the iterator construction
@click.command()
@click.option("--input-file", "-i", "input_file", prompt=True) #make this safe
@click.option("--input-type", "-t", "input_type", prompt=True, default="plain", type=click.Choice(['plain', 'story'])) 
@click.option("--output-dir", "-o", "output_file", prompt=True) #make this safe
@click.option("--hinting", "-h", "hinting", default="both", type=click.Choice(["none", "pre", "prog", "both"]), prompt=True) 
@click.option("--sense-tags", "-g", "tags", default="wordnet", type=click.Choice(["wordnet", "gold"]))
@click.option("--sense-pruning", "-p", "pruning", default="nbest", prompt=True, type=click.Choice(modifier_names))
@click.option("--pos-include", "-x", "pos_include", default="", prompt=True, help="comma separated pos tags to include.  Leave empty to allow all tags")
@click.option("--vagrant-home", "-v", "vagrant", default="", prompt=True)
@click.option("--tempfile", "-e", "temp", default="")
@click.option("--trips-url", "-u", "url", default="http://localhost:8081/cgi/STEP")
@click.option("--debug", "-d", "debug", default=False)
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
def parse(input_file, input_type, output_file, hinting, tags, pruning, pos_include, vagrant, temp, url, debug):
    output_to_dir = os.path.isdir(output_file)
    if not output_to_dir:
        raise click.BadArgumentUsage("--output-dir expected a directory")
    files = sorted(ls(input_file)) # order is important
    if not files:
        raise click.FileError(input_file, "Provide a single input file or a directory containing multiple files.")
    multiple_inputs = len(files) > 1
    if multiple_inputs:
        files = tqdm(files)
    temp_, url_ = "", ""
    if vagrant:
        temp_, url_ = get_from_vagrant(vagrant)
    if temp:
        temp_ = temp
    if url:
        url_ = url
    if not url_:
        raise click.BadOptionUsage("Wasn't given a url and couldn't figure one out from a vagrant config")

    options = TripsOptions(temp_, url_, tags, hinting, pruning, pos_include.split(","))
    click.echo(str(options))

    if input_type == "story":
        out = lambda x: x.replace(input_file, output_file)
        for f in files:
            if not os.path.isfile(out(f)):
                data = _json(f)
                data["sentences"] = [parse_sentence(d, options, debug) for d in data["sentences"]]
                data["configuration"] = options
                dump_json(data, out(f))
    else:
        ctr = 0
        for i, f in enumerate(files):
            data = _json(f)
            for d in data:
                outp = output_file, "sentence_{:>03d}.json".format(ctr)
                if os.path.join(outp):
                    continue
                parse = parse_sentence(d, options, debug)
                parse["configuration"] = options
                dump_json(parse, outp)


