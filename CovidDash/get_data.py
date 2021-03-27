import pandas as pd
import requests
from columns_mappings import columns, categories
import json
from app_config import COVID_API_URL, env_config, LOG_FILE
from s3_utils import S3Utils
from io import BytesIO
import logging

logging.basicConfig(
    format='%(levelname)s %(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    filename=LOG_FILE
)

env = env_config['env']
inputs_path = env_config['inputs_path']
output_file = env_config['output_file']
output_metadata = env_config['output_metadata']


def get_vaccine_resources(url: str) -> dict:
    response = requests.get(url=url)
    body = response.json()
    resources = body['result']['resources']
    data = {'resources': []}
    for resource in resources:
        if 'vaccinare' in resource['name']:
            data['resources'].append(
                dict(
                    url=resource['datagovro_download_url'],
                    name=resource['name'],
                    last_modified=resource['last_modified']
                )
            )
    logging.info('Received resources')
    return data


def download_save_inputs(url: str):
    response = requests.get(url)
    file_name = url.split('/')[-1]
    if env == 'local':
        file = env_config['inputs_path'] / file_name
        with open(file, 'wb') as output:
            output.write(response.content)
        logging.info(f'Saved {file_name} to {env}')
    else:
        file = env_config['inputs_path'] + file_name
        s3.file_obj_to_s3(file_obj=BytesIO(response.content), bucket=bucket, s3_file=file)
        logging.info(f'Saved {file_name} to {env}')
    return file


def union_inputs(files: list) -> pd.DataFrame:
    df = pd.DataFrame()
    for file in files:
        if env == 'local':
            input_file = file
        else:
            input_file = BytesIO(s3.s3_obj_to_bytes(file, bucket))
        df_temp = pd.read_excel(input_file, engine='openpyxl')
        df = df.append(df_temp)
    logging.info(f'Loaded {df.shape[0]} records from {env}')
    return df


def transform_vaccines(df: pd.DataFrame) -> pd.DataFrame:
    df.dropna(how='all', inplace=True)
    df = df[columns.keys()]
    df.rename(columns=columns, inplace=True)
    df[['grupa_risc_1', 'grupa_risc_2']] = df['grupa_risc_detail'].str.extract(r'(I+)\s*-*([abc]){0,1}')
    df['grupa_risc_2'].fillna('n/a', inplace=True)
    df['grupa_risc_int'] = df['grupa_risc_1'] + '-' + df['grupa_risc_2']
    df['grupa_risc'] = df['grupa_risc_int'] + ' ' + df['grupa_risc_int'].map(categories)
    df.drop(columns=['grupa_risc_1', 'grupa_risc_2', 'grupa_risc_int'], inplace=True)
    df['data_vaccinarii'] = pd.to_datetime(df['data_vaccinarii'], errors='coerce', format='%Y-%m-%d')
    logging.info('Data processed')
    return df


def export_outputs(df: pd.DataFrame, metadata: dict):
    export_format = dict(index=False, sep='\t')
    if env == 'local':
        df.to_csv(output_file, **export_format)
        logging.info(f'Saved {output_file.name} to {env}')
        with open(output_metadata, 'w') as f:
            json.dump(metadata, f)
    else:
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, **export_format)
        csv_buffer.seek(0)
        s3.file_obj_to_s3(file_obj=csv_buffer, bucket=bucket, s3_file=output_file)
        logging.info(f'Saved {output_file} to {env}')
        metadata_buffer = BytesIO()
        metadata_buffer.write(json.dumps(metadata).encode())
        metadata_buffer.seek(0)
        s3.file_obj_to_s3(file_obj=metadata_buffer, bucket=bucket, s3_file=output_metadata)


def get_data():
    vaccine_data_info = get_vaccine_resources(COVID_API_URL)
    vaccine_resources = vaccine_data_info['resources']
    input_files = []
    for rsc in vaccine_resources:
        url = rsc['url']
        input_file = download_save_inputs(url)
        input_files.append(input_file)
    vaccine_data_raw = union_inputs(input_files)
    vaccine_data_proc = transform_vaccines(vaccine_data_raw)
    export_outputs(vaccine_data_proc, vaccine_data_info)


if __name__ == '__main__':
    if env == 'aws':
        # the code below can be changed if there is no need to assume role
        if not env_config['s3_role']:
            raise ValueError('no S3_ROLE defined')
        elif not env_config['s3_bucket']:
            raise ValueError('no S3_BUCKET defined')
        s3 = S3Utils(env_config['s3_role'])
        logging.info('Get data - Successfully assumed role')
        bucket = env_config['s3_bucket']
    get_data()

