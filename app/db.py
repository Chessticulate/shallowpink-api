from app.config import CONFIG
from sqlalchemy import create_engine, String, select
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, Mapped

engine = create_engine(CONFIG.conn_str, echo=CONFIG.sql_echo)

