from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.api_sunat.get_sunat import APIService
from src.application.api_sunat.orquestador_descargas import OrquestadorDescargas
from src.application.api_sunat.scraping_service import ScrapingService
from src.application.enrolados.update_metodo import UpdateMetodoEnrolado
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.playwright_sunat.scraper import PlaywrightSUNAT
from src.infrastructure.postgresql.connection_sunat import get_db
from src.infrastructure.postgresql.repositories_sunat.sunat import ScriptRepository
from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado


def dp_get_enrolado(db: Session = Depends(get_db)) -> GetEnrolado:
    repository = ScriptRepository(db)
    return GetEnrolado(repository)


def dp_save_enrolado(db: Session = Depends(get_db)) -> SaveEnrolado:
    repository = ScriptRepository(db)
    return SaveEnrolado(repository)


def get_api_service() -> APIService:
    sunat_client = APISUNAT()
    return APIService(repository=sunat_client)


def get_scraper_service() -> ScrapingService:
    scraper_client = PlaywrightSUNAT()
    return ScrapingService(repository=scraper_client)


def dp_update_metodo(db: Session = Depends(get_db)) -> UpdateMetodoEnrolado:
    repository = ScriptRepository(db)
    return UpdateMetodoEnrolado(repository)


def get_orquestador_service(
    api: APIService = Depends(get_api_service),
    scraper: ScrapingService = Depends(get_scraper_service),
    update_repo: UpdateMetodoEnrolado = Depends(dp_update_metodo),
) -> OrquestadorDescargas:
    return OrquestadorDescargas(
        api_service=api, scraper_service=scraper, update_metodo_repo=update_repo
    )
