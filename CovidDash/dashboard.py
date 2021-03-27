import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from itertools import cycle
import json
import datetime as dt
from app_config import COVID_URL, GITHUB_URL, env_config, LOG_FILE
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
data_file = env_config['output_file']
metadata_file = env_config['output_metadata']

if env == 's3':
    # the code below can be changed if there is no need to assume role
    if not env_config['s3_role']:
        raise ValueError('no S3_ROLE defined')
    elif not env_config['s3_bucket']:
        raise ValueError('no S3_BUCKET defined')
    s3 = S3Utils(env_config['s3_role'])
    logging.info('Dashboard - Successfully assumed role')
    bucket = env_config['s3_bucket']


AVG_TIME_WINDOW = 5


def get_last_modified(file) -> str:
    # if ENVIRONMENT=local then use local file system for inputs. If s3, use S3
    if env == 'local':
        with open(file, 'r') as f:
            info = json.load(f)
    else:
        f = BytesIO(s3.s3_obj_to_bytes(file, bucket))
        info = json.load(f)
    resources = info['resources']
    file_timestamps = []
    for rsc in resources:
        file_timestamps.append(rsc['last_modified'])
    max_timestamp = dt.datetime.strptime(max(file_timestamps), '%Y-%m-%dT%H:%M:%S.%f')
    max_timestamp_human = dt.datetime.strftime(max_timestamp, '%d %b %Y %H:%M:%S')
    return max_timestamp_human


def load_data(file) -> pd.DataFrame:
    # if ENVIRONMENT=local then use local file system for inputs. If s3, use S3
    if env == 'local':
        input_file = file
    else:
        input_file = BytesIO(s3.s3_obj_to_bytes(file, bucket))
    return pd.read_csv(input_file, sep='\t')


last_modified = get_last_modified(metadata_file)
data = load_data(data_file)
logging.info(f'loaded {data.shape[0]} records from {last_modified}')

# unique values to populate the filter
areas = data['judet'].sort_values().drop_duplicates().tolist()
vaccines = data['tip_vaccin'].sort_values().drop_duplicates().tolist()

# the time scope for rolling average
last_n_days = sorted(data['data_vaccinarii'].unique())[-AVG_TIME_WINDOW:]

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(
    children=[
        html.H1(children='Vaccinare Romania'),
        html.H3(children=f'Date actualizate la {last_modified}'),
        html.Div(
            html.A('Sursa date', href=COVID_URL, target='_blank')
        ),
        html.Div(children=[
            html.P('Judet'),
            dcc.Dropdown(
                id='area_filter',
                options=[
                    {'label': x, 'value': x} for x in areas
                ],
                value=['Bucuresti'],
                multi=True
            ),
        ],
            style={'width': '25%', 'display': 'inline-block'}
        ),
        html.Div(children=[
          html.P('Tip Vaccin'),
          dcc.Dropdown(
              id='vaccine_filter',
              options=[
                  {'label': x, 'value': x} for x in vaccines
              ],
              value=vaccines,
              multi=True,
              clearable=False
          )
        ],
            style={'width': '25%', 'display': 'inline-block'}
        ),
        html.Div(children=[
            html.P('Centru'),
            dcc.Dropdown(
                id='center_filter',
                clearable=True
            )
        ],
            style={'width': '25%', 'display': 'inline-block'}
        ),
        html.Div(children=[
            html.P('Breakdown'),
            dcc.Dropdown(
                id='breakdown',
                options=[
                    {'label': y, 'value': x}
                    for x, y in {'grupa_risc': 'Grupa risc',
                                 'tip_vaccin': 'Tip vaccin',
                                 'judet': 'Judet',
                                 'nume_centru': 'Nume Centru'
                                 }.items()
                ],
                value='tip_vaccin',
                clearable=False
            )
        ],
            style={'width': '25%', 'display': 'inline-block'},
        ),
        dcc.Graph(id='graph'),
        dcc.Graph(id='graph_avg'),
        html.Div(children=[
            html.H3('Open source code'),
            html.A('Github', href=GITHUB_URL, target='_blank')
            ]
        ),
    ]
)


@app.callback(
    Output('graph', 'figure'),
    Input('breakdown', 'value'),
    Input('area_filter', 'value'),
    Input('vaccine_filter', 'value'),
    Input('center_filter', 'value')
)
def chart(split_by: str, area_filter: list, vaccine_filter: list, center_filter) -> px.bar:
    df = data.copy(deep=True)
    # apply the area, vaccine type filters, if existing
    if vaccine_filter:
        df = df[df['tip_vaccin'].isin(vaccine_filter)]
    if area_filter:
        df = df[df['judet'].isin(area_filter)]
    if isinstance(center_filter, str):
        # When filter is cleared, value is a list. We use the type to determine if there's any filter to be applied
        df = df[df['nume_centru'] == center_filter]
    # use the sorted dim values and cycle the color palette. Ensures consistent color legend across charts
    dim_values = sorted(df[split_by].unique())
    color_map = dict(zip(dim_values, cycle(px.colors.qualitative.Prism)))
    # aggregate, pass data to the chart
    df_out = df.groupby(['data_vaccinarii', split_by])['doze_administrate_total'].sum().reset_index()
    df_out_2 = df.groupby(['data_vaccinarii'])['doze_administrate_total'].sum().reset_index()
    df_out_2['n_days_avg'] = df_out_2.rolling(window=AVG_TIME_WINDOW)['doze_administrate_total'].mean()
    df_out_3 = df_out.groupby(['data_vaccinarii'])['doze_administrate_total'].sum().reset_index()

    fig = px.bar(
        df_out,
        x='data_vaccinarii',
        y='doze_administrate_total',
        color=split_by,
        template='simple_white',
        color_discrete_map=color_map,
        opacity=0.6,
        labels={
            'data_vaccinarii': 'Data vaccinarii',
            'doze_administrate_total': 'Total doze',
            'nume_centru': 'Centru',
            'judet': 'Judet',
            'grupa_risc': 'Grupa risc',
            'tip_vaccin': 'Tip vaccin'
        },
        title=f'Doze administrate zilnic si media pe {AVG_TIME_WINDOW} zile'
    )
    fig.add_scatter(
        x=df_out_2['data_vaccinarii'],
        y=df_out_2['n_days_avg'],
        name=f'{AVG_TIME_WINDOW} Days Avg',
        mode='markers+lines',
        line=dict(
            dash='dash',
            color='crimson',
            width=3,
        ),
        marker=dict(
            size=8
        )
    )
    fig.add_scatter(
        x=df_out_3['data_vaccinarii'],
        y=df_out_3['doze_administrate_total'],
        name='Total zilnic',
        mode='text',
        text=df_out_3['doze_administrate_total'],
        textposition='top center'
    )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_layout(showlegend=False)

    return fig


@app.callback(
    Output('graph_avg', 'figure'),
    Input('breakdown', 'value'),
    Input('area_filter', 'value'),
    Input('vaccine_filter', 'value'),
    Input('center_filter', 'value')
)
def chart_2(split_by: str, area_filter: list, vaccine_filter: list, center_filter) -> px.bar:
    df = data.copy(deep=True)
    # apply the area, vaccine type filters, if existing
    if vaccine_filter:
        df = df[df['tip_vaccin'].isin(vaccine_filter)]
    if area_filter:
        df = df[df['judet'].isin(area_filter)]
    if isinstance(center_filter, str):
        # When filter is cleared, value is a list. We use the type to determine if there's any filter to be applied
        df = df[df['nume_centru'] == center_filter]
    # truncate the center names to keep the layout clean
    df['nume_centru'] = df['nume_centru'].str[:40] + '...'
    dim_values = sorted(df[split_by].unique())
    df = df[df['data_vaccinarii'].isin(last_n_days)]
    if not df.empty:  # depending on the filters combination, the df can be empty
        df_out = df.groupby([split_by])['doze_administrate_total'].sum()/AVG_TIME_WINDOW
        df_out = df_out.reset_index()
        color_map = dict(zip(dim_values, cycle(px.colors.qualitative.Prism)))
        df_out = df_out.sort_values(['doze_administrate_total'], ascending=False).head(15)
        fig = px.bar(
            df_out,
            x='doze_administrate_total',
            y=split_by,
            orientation='h',
            template='simple_white',
            color=split_by,
            text='doze_administrate_total',
            color_discrete_map=color_map,
            # color_discrete_sequence=px.colors.qualitative.Prism,
            opacity=0.6,
            labels={
                'doze_administrate_total': f'Doze/zi',
                'nume_centru': 'Centru (Top 15)',
                'judet': 'Judet (Top 15)',
                'grupa_risc': 'Grupa risc',
                'tip_vaccin': 'Tip vaccin'
            },
            title=f'Numar mediu de doze zilnice in ultimele {AVG_TIME_WINDOW} zile'
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_layout(showlegend=False)
        return fig
    else:
        return {}  # return blank chart if df is empty


# callback to filter the Centers based on the other filter values (dependent filtering)
@app.callback(
    Output('center_filter', 'options'),
    Input('area_filter', 'value'),
    Input('vaccine_filter', 'value')
)
def get_filtered_centers_options(area_filter: list, vaccine_filter: list):
    df = data.copy(deep=True)
    if vaccine_filter:
        df = df[df['tip_vaccin'].isin(vaccine_filter)]
    if area_filter:
        df = df[df['judet'].isin(area_filter)]
    filtered_centers = df['nume_centru'].sort_values().drop_duplicates().tolist()
    return [{'label': i, 'value': i} for i in filtered_centers]


if __name__ == '__main__':
    logging.info('Starting server')
    if env == 'local':
        app.run_server(debug=True)
    else:
        app.run_server(host='0.0.0.0', port=8050)
