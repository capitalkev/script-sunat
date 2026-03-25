from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.api_sunat.get_sunat import APIService
from src.application.api_sunat.orquestador_descargas import OrquestadorDescargas
from src.application.etl.procesar_ventas import ProcesarVentasETL
from src.domain.interfaces import TokenScraperInterface
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.playwright_sunat.scraper import (
    PlaywrightTokenScraper,
)
from src.infrastructure.postgresql.connection_sunat import get_db
from src.infrastructure.postgresql.repositories_sunat.sunat import ScriptRepository
from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository


def dp_get_enrolado(db: Session = Depends(get_db)) -> GetEnrolado:
    repository = ScriptRepository(db)
    return GetEnrolado(repository)


def dp_save_enrolado(db: Session = Depends(get_db)) -> SaveEnrolado:
    repository = ScriptRepository(db)
    return SaveEnrolado(repository)


def get_api_service() -> APIService:
    sunat_client = APISUNAT()
    return APIService(repository=sunat_client)


def get_token_scraper() -> TokenScraperInterface:
    return PlaywrightTokenScraper()


def get_etl_service(db: Session = Depends(get_db)) -> ProcesarVentasETL:
    repository = VentasRepository(db)
    return ProcesarVentasETL(repository)


def get_orquestador_service(
    api: APIService = Depends(get_api_service),
    scraper: TokenScraperInterface = Depends(get_token_scraper),
    etl: ProcesarVentasETL = Depends(get_etl_service),
) -> OrquestadorDescargas:
    return OrquestadorDescargas(api_service=api, token_scraper=scraper, etl_service=etl)
