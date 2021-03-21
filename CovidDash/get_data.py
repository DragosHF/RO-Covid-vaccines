import pandas as pd
import requests
from vaccines_columns import columns
import json
from app_config import TEMP_IN, TEMP_OUT_FILE, TEMP_OUT_JSON, COVID_API_URL


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
    return data


def download_files(url: str) -> list:
    response = requests.get(url)
    file_name = url.split('/')[-1]
    file = TEMP_IN / file_name
    with open(file, 'wb') as output:
        output.write(response.content)
    return file


def union_files(files: list) -> pd.DataFrame:
    df = pd.DataFrame()
    for file in files:
        df_temp = pd.read_excel(file)
        df = df.append(df_temp)
    return df


def transform_vaccines(df: pd.DataFrame):
    df.dropna(how='all', inplace=True)
    df = df[columns.keys()]
    df.rename(columns=columns, inplace=True)
    df[['grupa_risc_1', 'grupa_risc_2']] = df['grupa_risc_detail'].str.extract(r'(I+)\s*-*([abc]){0,1}')
    df['grupa_risc_2'].fillna('n/a', inplace=True)
    df['grupa_risc_int'] = df['grupa_risc_1'] + '-' + df['grupa_risc_2']
    df['grupa_risc'] = df['grupa_risc_int'] + ' ' + df['grupa_risc_int'].map({
        'I-n/a': 'personal medical',
        'II-a': '65+, risc ridicat',
        'II-b': 'domenii cheie',
        'III-a': 'populatia generala',
        'III-c': 'populatia pediatrica',
        'III-b': 'alte categorii'
    })
    df.drop(columns=['grupa_risc_1', 'grupa_risc_2', 'grupa_risc_int'], inplace=True)
    df['data_vaccinarii'] = pd.to_datetime(df['data_vaccinarii'], errors='coerce', format='%Y-%m-%d')
    df.to_csv(TEMP_OUT_FILE, sep='\t', index=False)


def refresh_data():
    vaccine_info = get_vaccine_resources(COVID_API_URL)
    vaccine_resources = vaccine_info['resources']
    temp_out_files = []
    for rsc in vaccine_resources:
        url = rsc['url']
        temp_out_file = download_files(url)
        temp_out_files.append(temp_out_file)
    df = union_files(temp_out_files)
    transform_vaccines(df)
    with open(TEMP_OUT_JSON, 'w') as f:
        json.dump(vaccine_info, f)


if __name__ == '__main__':
    refresh_data()

