from src.application.sunat.create_ticket import CreateTicket
from src.application.sunat.get_token import GetTocken
from src.application.sunat.save_ticket import SaveTicket
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository


class OrquestadorTickets:
    def __init__(
        self,
        generar_ticket: CreateTicket,
        get_token: GetTocken,
        guardar_ticket: SaveTicket,
        ventas_repo: VentasRepository
    ):
        self.generar_ticket = generar_ticket
        self.get_token = get_token
        self.guardar_ticket = guardar_ticket
        self.ventas_repo = ventas_repo

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados = {}

        token_acceso = self.get_token.execute(ruc, usuario_sol, clave_sol, client_id, client_secret)

        for periodo in periodos:
            if self.ventas_repo.existe_periodo(ruc, periodo):
                print(f"[{ruc}] Ventas del periodo {periodo} ya existen en BD. Omitiendo generación de ticket.")
                resultados[periodo] = {"estado": "VENTAS_YA_EXISTEN_EN_BD"}
                continue
            try:
                numero_ticket = self.generar_ticket.execute(periodo, token_acceso)

                if numero_ticket:
                    self.guardar_ticket.execute(ruc, periodo, numero_ticket)
                    print(
                        f"[{ruc}] Ticket {numero_ticket} guardado en BD (Periodo: {periodo})"
                    )
                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": "GUARDADO",
                    }

            except Exception as e:
                print(f"[{ruc}] Error en periodo {periodo}: {e}")
                resultados[periodo] = {"error": str(e)}

        return {"ruc": ruc, "resultados": resultados}
