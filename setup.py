from setuptools import setup, find_packages

setup(
    name='tripscli',
    version='0.0.3',
    author="Rik Bose",
    author_email="rbose@cs.rochester.edu",
    description="Various command line tools for fetching and analysing trips parses",
    url="https://github.com/mrmechko/tripscli",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'click_config_file',
        'pytrips'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
    ]
    entry_points = {
        "console_scripts": ["trips-cli=tripscli.cmd:cli"]
    },
)
