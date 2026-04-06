from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import ScriptInterface


class ScriptRepository(ScriptInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_enrolado(self) -> Any:
        query_str = "SELECT ruc, usuario_sol, clave_sol, client_id, client_secret FROM enrolados"
        query = text(query_str)
        result = self.db.execute(query)
        return [dict(row) for row in result.mappings()]

    def get_only_enrolado(self, ruc: str) -> Any:
        query_str = "SELECT ruc, usuario_sol, clave_sol, client_id, client_secret FROM enrolados where ruc = :ruc"
        query = text(query_str)
        result = self.db.execute(query, {"ruc": ruc}).mappings().fetchone()

        return dict(result) if result else None

    def save_enrolado(self, datos: dict) -> None:
        check_query = text("SELECT id FROM enrolados WHERE ruc = :ruc")
        existe = self.db.execute(check_query, {"ruc": datos["ruc"]}).fetchone()

        if existe:
            update_query = text(
                """
                UPDATE enrolados 
                SET usuario_sol = :usuario_sol, clave_sol = :clave_sol, 
                    client_id = :client_id, client_secret = :client_secret, email = :email
                WHERE ruc = :ruc
            """
            )
            self.db.execute(update_query, datos)
        else:
            insert_query = text(
                """
                INSERT INTO enrolados (ruc, usuario_sol, clave_sol, client_id, client_secret, email) 
                VALUES (:ruc, :usuario_sol, :clave_sol, :client_id, :client_secret, :email)
            """
            )
            self.db.execute(insert_query, datos)

        self.db.commit()
