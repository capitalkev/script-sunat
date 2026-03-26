from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.sunat.get_sunat import APIService
from src.application.etl.procesar_ventas import ProcesarVentasETL
from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado

from src.application.sunat.orquestador_tickets import OrquestadorTickets
from src.application.sunat.save_ticket import SaveTicket
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.postgresql.connection_sunat import get_db
from src.infrastructure.postgresql.repositories_sunat.sunat import ScriptRepository
from src.infrastructure.postgresql.repositories_sunat.tickets import TicketsRepository
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository


def dp_get_enrolado(db: Session = Depends(get_db)) -> GetEnrolado:
    repository = ScriptRepository(db)
    return GetEnrolado(repository)


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

def dp_orquestador(guardar_ticket: SaveTicket = Depends(dp_save_ticket)) -> OrquestadorTickets:
    """Inyecta el caso de uso SaveTicket dentro del Orquestador."""
    return OrquestadorTickets(guardar_ticket=guardar_ticket)