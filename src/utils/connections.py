# utils/connections.py
from google.oauth2 import service_account
from dotenv import load_dotenv
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'

load_dotenv()


def get_google_creds():
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )


def get_mstr_conn():
    from mstrio.connection import Connection
    base_url = "https://tablerosancorsalud.cloud.microstrategy.com/MicroStrategyLibrary/api"
    project_id = "DAE6DF9811D67BD9500010A51D1D2ADA"
    return Connection(base_url, os.getenv('MSTR_USER'), os.getenv('MSTR_PASSWORD'), project_id=project_id)