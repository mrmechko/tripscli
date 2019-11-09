import json 

def json_config_provider(file_path, cmd_name):
    with open(file_path) as config_data:
        return json.load(config_data)[cmd_name]

