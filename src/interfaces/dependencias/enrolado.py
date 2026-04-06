from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.enrolados.get_only_enrolados import GetOnlyEnrolado
from src.application.sunat.create_ticket import CreateTicket
from src.application.sunat.get_sunat import APIService
from src.application.etl.procesar_ventas import ProcesarVentasETL
from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado
from src.application.sunat.get_ticket import GetTicket
from src.application.sunat.get_token import GetTocken
from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.application.sunat.orquestador_descargas import OrquestadorDescargas
from src.application.sunat.orquestador_tickets import OrquestadorTickets
from src.application.sunat.save_ticket import SaveTicket

# Infraestructura
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.playwright_sunat.scraper import PlaywrightTokenScraper
from src.infrastructure.postgresql.connection_sunat import get_db
from src.infrastructure.postgresql.repositories_sunat.sunat import ScriptRepository
from src.infrastructure.postgresql.repositories_sunat.tickets import TicketsRepository
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository


def dp_get_enrolado(db: Session = Depends(get_db)) -> GetEnrolado:
    repository = ScriptRepository(db)
    return GetEnrolado(repository)


def dp_get_only_enrolado(db: Session = Depends(get_db)) -> GetOnlyEnrolado:
    repository = ScriptRepository(db)
    return GetOnlyEnrolado(repository)


def dp_save_enrolado(db: Session = Depends(get_db)) -> SaveEnrolado:
    repository = ScriptRepository(db)
    return SaveEnrolado(repository)


def get_tickets_repo(db: Session = Depends(get_db)) -> TicketsRepository:
    return TicketsRepository(db)


def get_etl_service(db: Session = Depends(get_db)) -> ProcesarVentasETL:
    repository = VentasRepository(db)
    return ProcesarVentasETL(repository)


def get_api_service() -> APIService:
    sunat_client = APISUNAT()
    return APIService(repository=sunat_client)


def dp_save_ticket(db: Session = Depends(get_db)) -> SaveTicket:
    """Inyecta la sesión de BD al repositorio de tickets, y el repo al caso de uso."""
    repository = TicketsRepository(db)
    return SaveTicket(repository)


def dp_orquestador_tickets(db: Session = Depends(get_db)) -> OrquestadorTickets:
    """Ensambla el orquestador inyectando todas sus dependencias"""

    api_sunat = APISUNAT()
    tickets_repo = TicketsRepository(db)
    ventas_repo = VentasRepository(db)
    create_ticket = CreateTicket(api_sunat)
    save_ticket = SaveTicket(tickets_repo)
    token_api = GetTokenAPI(api_sunat)
    token_scraper = GetTokenScraping(PlaywrightTokenScraper())

    return OrquestadorTickets(
        generar_ticket=create_ticket,
        guardar_ticket=save_ticket,
        ventas_repo=ventas_repo,
        get_token=GetTocken(token_api, token_scraper),
    )


def dp_orquestador_descargas(db: Session = Depends(get_db)) -> OrquestadorDescargas:
    """Ensambla el orquestador de descargas inyectando todas sus dependencias"""

    api_sunat = APISUNAT()
    tickets_repo = TicketsRepository(db)
    ventas_repo = VentasRepository(db)
    get_ticket = GetTicket(tickets_repo)
    etl_ventas = ProcesarVentasETL(ventas_repo)
    token_api = GetTokenAPI(api_sunat)
    token_scraper = GetTokenScraping(PlaywrightTokenScraper())

    return OrquestadorDescargas(
        get_ticket=get_ticket,
        sunat_api=api_sunat,
        etl_ventas=etl_ventas,
        ventas_repo=ventas_repo,
        get_token=GetTocken(token_api, token_scraper),
    )
