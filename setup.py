from setuptools import find_packages, setup

setup(
    name='tripscli',
    version='0.0.6',
    author="Rik Bose",
    author_email="rbose@cs.rochester.edu",
    description="Various command line tools for fetching and analysing trips parses",
    url="https://github.com/mrmechko/tripscli",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'click_config_file',
        'pandas',
        'tqdm',
        'spacy',
        'supwsd',
        'pytrips'
    ],
    dependency_links = [
      "git+git://github.com/mrmechko/soul.git#egg=soul"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
    ],
    entry_points = {
        "console_scripts": ["trips-cli=tripscli.cmd:cli"]
    },
)
