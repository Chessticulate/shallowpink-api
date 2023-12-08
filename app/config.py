import os
from dotenv import load_dotenv
load_dotenv()

class CONFIG:
    app_name: str = os.environ.get('APP_NAME', 'chessticulate-api-dev')
    log_level: str = os.environ.get('LOG_LEVEL', 'INFO')
    sql_echo: bool = True if os.environ.get('SQL_ECHO') == 'TRUE' else False
    conn_str: str = os.environ.get('SQL_CONN_STR', 'sqlite+pysqlite:///:memory:')
    
    # DEFAULT SECRET FOR TESTING PURPOSES ONLY, DO NOT USE
    secret: str = os.environ.get("APP_SECRET", None)
    algorithm: str = os.environ.get("APP_JWT_ALGO", "HS256")
