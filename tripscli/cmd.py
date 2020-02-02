import click
import click_config_file
import json
from .to_json import to_json
from .util import json_config_provider
from .tag_wsd import tag_wsd, tag_raw_text
from .parse import parse, query
from .compare import simple as simple_view
from .compare import compare, compare_parse
from .semcor2csv import semcor2csv

from pytrips.ontology import get_ontology

# to_json should handle the iterator construction
@click.group()
@click.option("--gloss/--no-gloss", default=False)
def cli(gloss):
    get_ontology(use_gloss=gloss, single=True)
    pass

cli.add_command(to_json)
cli.add_command(tag_wsd)

cli.add_command(parse)
cli.add_command(query)

cli.add_command(simple_view)
cli.add_command(compare)
cli.add_command(tag_raw_text)
cli.add_command(semcor2csv)
cli.add_command(compare_parse)

if __name__ == "__main__":
    cli()
