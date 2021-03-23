from pathlib import Path

APP_ROOT = Path(__file__).parent.resolve()
TEMP_IN = APP_ROOT / 'temp_in'
TEMP_OUT = APP_ROOT / 'temp_out'
TEMP_OUT_FILE = TEMP_OUT / 'vaccines_covid.txt'
TEMP_OUT_JSON = TEMP_OUT / 'data.json'
COVID_API_URL = 'https://data.gov.ro/api/3/action/package_show?id=transparenta-covid'
COVID_URL = 'https://data.gov.ro/dataset/transparenta-covid'
GITHUB_URL = 'https://github.com/DragosHF/RO-Covid-vaccines'
