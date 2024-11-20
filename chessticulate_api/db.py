"""chessticulate_api.db"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from chessticulate_api.config import CONFIG

async_engine = create_async_engine(
    CONFIG.sql_conn_str, pool_pre_ping=True, echo=CONFIG.sql_echo
)

async_session = async_sessionmaker(async_engine, expire_on_commit=False)
