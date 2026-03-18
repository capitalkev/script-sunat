from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import ScriptInterface


class ScriptRepository(ScriptInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_enrolado(self) -> Any:
        query = text(
            "SELECT ruc, usuario_sol, clave_sol, client_id, client_secret FROM enrolado limit 2"
        )
        result = self.db.execute(query)
        return [dict(row) for row in result.mappings()]

    # asignar enrolado a ejecutivo
    # agregar enrolados
    # descargar un mes
    # descargar los ultimos meses
    # revisar casos fallidos
    # retornar un enrolado
    # revisar si ese mes ya fue sacado
