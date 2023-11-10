import os
from dotenv import load_dotenv
load_dotenv()

class CONFIG:
    app_name: str = os.environ.get('APP_NAME', 'chessticulate-api-dev')
    log_level: str = os.environ.get('LOG_LEVEL', 'INFO')
    sql_echo: bool = True if os.environ.get('SQL_ECHO') == 'TRUE' else False
    conn_str: str = os.environ.get('SQL_CONN_STR', 'sqlite+pysqlite:///:memory:')

