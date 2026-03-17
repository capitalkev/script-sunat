from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import ScriptInterface


class OperacionesRepository(ScriptInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_enrolado(self, ruc: str) -> Any: # Retornar datos de un enrolado para hacer su extracción
        query = text("SELECT * FROM enrolado WHERE ruc = :ruc")
        result = self.db.execute(query, {"ruc": ruc})
        return [dict(row) for row in result.mappings()]

    def get_mes_extraido(self, ruc: str, mes: str) -> Any: # Retornar datos de un mes extraído para revisar si ya fue sacado
        query = text("SELECT * FROM mes_extraido WHERE ruc = :ruc AND mes = :mes")
        result = self.db.execute(query, {"ruc": ruc, "mes": mes})
        return [dict(row) for row in result.mappings()]

    
    # asignar enrolado a ejecutivo
    # agregar enrolados
    # descargar un mes
    # descargar los ultimos meses
    # revisar casos fallidos
    # retornar un enrolado
    # revisar si ese mes ya fue sacado
    