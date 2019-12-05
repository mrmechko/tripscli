from setuptools import setup, find_packages

setup(
        name='tripscli',
        version='0.0.2',
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            'Click',
            'click_config_file',
            ],
        entry_points = {
            "console_scripts": ["trips-cli=tripscli.cmd:cli"]
            },
        )
