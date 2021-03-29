# RO-Covid-vaccines
Web app to display Romanian vaccination data

### Important! Requires Python 3.8.1 or higher

Uses Plotly and Dash, includes module to fetch updated data


data source: https://data.gov.ro/dataset/transparenta-covid

usage:

The code can use either local or S3 storage. For S3 the prerequisites are: S3 bucket, access keys, permissions to S3 granted directly or through an "assume role" policy. Edit the get_data.py and dashboard.py if the permissions are granted directly.

build the project (creates venv and folder structure: inputs, outputs, logs)
`bash build.sh`

execute using local storage
`bash run.sh local`

execute using S3 storage: edit the `run.sh` file, then
`bash run.sh s3`

change the app.run_server() in dashboard.py depending on the environment
