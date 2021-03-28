from pathlib import Path
import os

# STORAGE can be 'local' or 's3'
# when 'local' the code will use the local temp folder structure to store and retrieve the data
# when 's3' the code will use S3 to store and retrieve the data
# 's3' requires the following env variables: S3_ROLE, S3_BUCKET,  AWS_SECRET_ACCESS_KEY,  AWS_ACCESS_KEY_ID
# the S3_ROLE is the role to assume by the current user when interacting with S3

APP_ROOT = Path(__file__).parent.resolve()
COVID_API_URL = 'https://data.gov.ro/api/3/action/package_show?id=transparenta-covid'
COVID_URL = 'https://data.gov.ro/dataset/transparenta-covid'
GITHUB_URL = 'https://github.com/DragosHF/RO-Covid-vaccines'
LOG_FILE = APP_ROOT / 'logs' / 'covid_dash.log'


def set_env():
    storage = os.getenv('STORAGE')
    if storage not in ['local', 's3']:
        raise ValueError('STORAGE must be one of: local, s3')
    else:
        output_file_name = 'vaccines_covid.txt'
        output_metadata_name = 'vaccines_covid_metadata.json'
        config = {'storage': storage}
        if storage == 'local':
            # if local, return Path objects
            inputs_path = APP_ROOT / 'inputs'
            outputs_path = APP_ROOT / 'outputs'
            config['output_file'] = outputs_path / output_file_name
            config['output_metadata'] = outputs_path / output_metadata_name
        else:
            # if s3, return strings to be used as S3 prefixes
            inputs_path = 'covid_vaccines_inputs/'
            outputs_path = 'covid_vaccines_outputs/'
            config['output_file'] = outputs_path + output_file_name
            config['output_metadata'] = outputs_path + output_metadata_name
            # additional AWS related env variables
            config['s3_role'] = os.getenv('S3_ROLE')
            config['s3_bucket'] = os.getenv('S3_BUCKET')
        config['inputs_path'] = inputs_path
    return config


env_config = set_env()
