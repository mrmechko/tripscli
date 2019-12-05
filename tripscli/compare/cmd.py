import click
import click_config_file
from ..util import json_config_provider
from soul.files import json as _json, dump_json
from .simple_view import view, compare_taggings
from .align_parse import compare_parses, OutputConfig, AlignConfig, ScoreConfig

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

@click.command()
@click.option("--file1", "-u", "file1", prompt=True)
@click.option("--file2", "-v", "file2", prompt=True)
@click.option("--sup", "-s", "sup", count=True)
@click.option("--input-type", "-t", "data", default="plain", type=click.Choice(["plain", "story"]), prompt=True)
@click.option("--output-file", "-o", "output", default="", prompt=True)
def compare(file1, file2, sup, data, output):
    file1 = _json(file1)
    file2 = _json(file2)
    if data == "story":
        file1, file2 = file1["sentences"], file2["sentences"]
        result = [compare_taggings(a, b, sup>0) for a, b in zip(file1, file2)]
    elif data == "plain":
        result = compare_taggings(file1, file2)
    dump_json(result, output)


@click.command()
@click.option("--reference", "-r", "reference", prompt=True, help="Reference json file")
@click.option("--input-file", "-i", "input_file", prompt=True, help="directory to find parses in")
@click.option("--verbose", "-v", "verbose", count=True)
@click.option("--as-json", "-j", "as_json", count=True)
@click.option("--trace", "-t", "trace", count=True)
@click.option("--word", "-w", "word", count=True)
@click.option("--multi", "-m", "multi", count=True)
@click.option("--exact", "-e", "exact", count=True)
@click.option("--significant", "-s", "significant", count=True)
@click.option("--hierarchy", "-h", "hierarchy", default=-1, type=int)
@click.option("--down", "-d", "down", default=0, type=int)
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
def compare_parse(reference, input_file, verbose, as_json, trace, word, multi, exact, significant, hierarchy, down):
    outputc = OutputConfig(trace, verbose, as_json)
    alignc = AlignConfig(word, multi, exact)
    scorec = ScoreConfig(hierarchy, down, significant)
    compare_parses(reference, input_file, alignc, scorec, outputc)
