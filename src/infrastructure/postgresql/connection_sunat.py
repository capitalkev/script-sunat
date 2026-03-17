import os

from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_NAME_SUNAT = os.getenv("DB_NAME_SUNAT")
DB_USER_SUNAT = os.getenv("DB_USER_SUNAT")
DB_PASSWORD_SUNAT = os.getenv("DB_PASSWORD_SUNAT")
INSTANCE_CONNECTION_NAME_SUNAT = os.getenv("CONNECTION_NAME_SUNAT")

if INSTANCE_CONNECTION_NAME_SUNAT:
    connector = Connector()

    def getconn():
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME_SUNAT,
            "pg8000",
            user=DB_USER_SUNAT,
            password=DB_PASSWORD_SUNAT,
            db=DB_NAME_SUNAT,
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    print(f"Usando Cloud SQL Connector: {INSTANCE_CONNECTION_NAME_SUNAT}")

else:
    raise ValueError(
        "Configuración de base de datos incompleta. Define  USE_CLOUD_SQL_CONNECTOR=true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
