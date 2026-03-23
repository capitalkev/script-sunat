from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.interfaces import ScriptInterface


class ScriptRepository(ScriptInterface):
    def __init__(self, db: Session):
        self.db = db

    # Querys para Automático
    def get_enrolado(self, limite: int) -> Any:
        query_str = "SELECT ruc, usuario_sol, clave_sol, client_id, client_secret FROM enrolados"

        if limite is not None:
            query_str += f" LIMIT {limite}"

        query = text(query_str)
        result = self.db.execute(query)
        return [dict(row) for row in result.mappings()]
    
    
    # Querys para manual

    def get_enrolado_by_ruc(self, ruc: str) -> Any:
        query = text(
            "SELECT ruc, usuario_sol, clave_sol, client_id, client_secret FROM enrolados WHERE ruc = :ruc"
        )
        result = self.db.execute(query, {"ruc": ruc}).fetchone()
        return dict(result._mapping) if result else None

    def save_enrolado(self, datos: dict) -> None:
        check_query = text("SELECT id FROM enrolados WHERE ruc = :ruc")
        existe = self.db.execute(check_query, {"ruc": datos["ruc"]}).fetchone()

        if existe:
            update_query = text(
                """
                UPDATE enrolados 
                SET usuario_sol = :usuario_sol, clave_sol = :clave_sol, 
                    client_id = :client_id, client_secret = :client_secret
                WHERE ruc = :ruc
            """
            )
            self.db.execute(update_query, datos)
        else:
            insert_query = text(
                """
                INSERT INTO enrolados (ruc, usuario_sol, clave_sol, client_id, client_secret, estado) 
                VALUES (:ruc, :usuario_sol, :clave_sol, :client_id, :client_secret, 'pendiente')
            """
            )
            self.db.execute(insert_query, datos)

        self.db.commit()

    def update_metodo(self, ruc: str, metodo: str) -> None:
        query = text("UPDATE enrolados SET metodo = :metodo WHERE ruc = :ruc")
        self.db.execute(query, {"metodo": metodo, "ruc": ruc})
        self.db.commit()