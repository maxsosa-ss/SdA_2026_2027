from mstrio.connection import Connection
from dotenv import load_dotenv
import os

load_dotenv()

# Load environment variables from .env file
user = os.getenv('MSTR_USER')
password = os.getenv('MSTR_PASSWORD')

base_url = "https://tablerosancorsalud.cloud.microstrategy.com/MicroStrategyLibrary/api"
mstr_username = user
mstr_password = password
project_id = "DAE6DF9811D67BD9500010A51D1D2ADA"

conn = Connection(base_url, mstr_username, mstr_password, project_id=project_id)