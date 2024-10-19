"""chessticulate_api.config"""

import os

from dotenv import load_dotenv

load_dotenv()


class CONFIG:  # pylint: disable=too-few-public-methods
    """Configuration class"""

    app_name: str = os.environ.get("APP_NAME", "chessticulate-api-dev")
    app_host: str = os.environ.get("APP_HOST", "localhost")
    app_port: int = int(os.environ.get("APP_PORT", 8000))
    log_level: str = os.environ.get("LOG_LEVEL", "info")

    # "postgresql+asyncpg://<uname>:<pswd>@<hostname>/<dbname>
    sql_conn_str: str = os.environ.get("SQL_CONN_STR", "sqlite+aiosqlite:///:memory:")
    sql_echo: bool = os.environ.get("SQL_ECHO") == "TRUE"

    jwt_ttl: int = int(os.environ.get("JWT_TTL", 7))
    jwt_secret: str = os.environ.get("JWT_SECRET", "secret")
    jwt_algo: str = os.environ.get("JWT_ALGO", "HS256")

    # chess workers service url
    workers_base_url: str = os.environ.get("WORKERS_URL", "localhost:8001")
