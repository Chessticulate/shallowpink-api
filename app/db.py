"""app.db

SQL engine definition.

Variables:
    engine
"""

from sqlalchemy import create_engine

from app.config import CONFIG

engine = create_engine(CONFIG.conn_str, echo=CONFIG.sql_echo)
