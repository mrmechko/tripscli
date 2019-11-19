import pandas as pd
import click
import click_config_file
from .util import json_config_provider
import sys, os
from collections import Counter
from tqdm import tqdm

nota = "__nota__"
vocab = Counter()


substitutions = {
        '``': '"',
        }

def get_nth(line, n):
    return line.split()[n].split('"')[1]

def get_text(line):
    return line.split(">")[1].split("<")[0]

def get_tag(line, tag):
    if tag == "lemma":
        return get_text(line)
    tag = tag+"="
    for entry in line.split():
        if entry.startswith(tag):
            return entry.split('"')[1]
    return "__none__"

def get_wf(line):
    vocab[get_tag(line, "lemma")] += 1
    return [
            nota,
            get_tag(line, "lemma"),
            get_tag(line, "pos"),
            nota
    ]

def get_instance(line, goldkey):
    vocab[get_tag(line, "lemma")] += 1
    id = get_tag(line, "id")
    return [
            id,
            get_tag(line, "lemma"),
            get_tag(line, "pos"),
            goldkey[id]
    ]

def write_semcor_csv(semcor_file, input_dir=".", output_dir="output"):
    goldkey = {}
    infile = os.path.join(input_dir, semcor_file)
    with open(infile+".gold.key.txt") as data:
        for line in data:
            line = line.strip().split()
            goldkey[line[0]] = " ".join(line[1:])
    
    all_results = []
    result = []
    count = 0
    start = ["__start__"] * 4 
    end = ["__end__"] * 4 
    max_len = 0
    with open(infile+".data.xml") as data:
        sentence_len = 0
        for line in tqdm(data, desc="reading"):
            line = line.lower()
            sentence_len += 1
            if line.startswith("<sentence"):
                result.append(start)
            elif line.startswith("<wf"):
                result.append(get_wf(line))
            elif line.startswith("<instance"):
                result.append(get_instance(line, goldkey))
            elif line.startswith("</sentence"):
                if sentence_len < 32:
                    result.append(end)
                    max_len = max(max_len, sentence_len - 1)
                    count += 1
                sentence_len = 0
                if count == 1000:
                    all_results.append(result)
                    result = []
                    count = 0
        all_results.append(result)
    
    for i in tqdm(range(len(all_results)), desc="writing"):
        results = all_results[i]
        output = pd.DataFrame(results, columns=["sid", "word", "pos", "tag"])
        with open("{}/{}.{}.csv".format(output_dir, semcor_file, str(i)), "w") as fl:
            output.to_csv(fl)
    most_common = [x[0] for x in vocab.most_common(3000)]
    with open(os.path.join(output_dir, "most_common_vocab"), 'w') as fl:
        fl.write("\n".join(list(most_common)))
    print("Max_len is {}".format(str(max_len)))

@click.command()
@click.option("--input-dir", "-i", "input_dir", prompt=True, default="")
@click.option("--output-dir", "-o", "output_dir", prompt=True, default="")
@click.option("--dataset", "-d", "dataset", prompt=True, default="")
@click_config_file.configuration_option(implicit=False, provider=json_config_provider)
def semcor2csv(input_dir, output_dir, dataset):
    if os.path.exists(output_dir):
        raise FileExistsError("The output file specified exists.  Please specify a folder that doesn't exist yet")
    os.mkdir(output_dir)
    if not dataset:
        dataset = input_dir.split("/")[0]
    
    write_semcor_csv(dataset, input_dir, output_dir)

