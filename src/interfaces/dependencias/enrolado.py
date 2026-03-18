from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.api_sunat.get_sunat import APIService
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.postgresql.connection_sunat import get_db
from src.infrastructure.postgresql.repositories_sunat.sunat import ScriptRepository
from src.application.enrolados.get_enrolados import GetEnrolado


def dp_get_enrolado(db: Session = Depends(get_db)) -> GetEnrolado:
    repository = ScriptRepository(db)
    return GetEnrolado(repository)


def get_api_service() -> APIService:
    sunat_client = APISUNAT()
    return APIService(repository=sunat_client)
