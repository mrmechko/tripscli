import pandas as pd
from .entry_iterator import simple_it
from .text import story_to_json

def read_csv_stories(fname, nlp, entries=simple_it):
    stories = pd.read_csv(fname)
    return (story_to_json(story.storyid, story.storytitle, story[-5:], nlp) for story in entries(stories.itertuples()))

