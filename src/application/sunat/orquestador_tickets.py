from src.application.sunat.create_ticket import CreateTicket
from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.application.sunat.save_ticket import SaveTicket


class OrquestadorTickets:
    def __init__(
        self,
        token_api: GetTokenAPI,
        token_scraper: GetTokenScraping,
        generar_ticket: CreateTicket,
        guardar_ticket: SaveTicket
    ):
        self.token_api = token_api
        self.token_scraper = token_scraper
        self.generar_ticket = generar_ticket
        self.guardar_ticket = guardar_ticket

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados = {}

        def obtener_token():
            try:
                print(f"[{ruc}] 1. Intentando obtener Token vía API...")
                token1 = self.token_api.execute(
                    ruc, usuario_sol, clave_sol, client_id, client_secret
                )
                if token1:
                    return token1
            except Exception:
                print(f"[{ruc}] Falló Token API. Intentando Playwright...")

            try:
                print(f"[{ruc}] 2. Intentando obtener Token vía Playwright...")
                token2 = self.token_scraper.execute(ruc, usuario_sol, clave_sol)
                if token2:
                    return token2
            except Exception:
                print(f"[{ruc}] Fallo Crítico en Playwright.")
                return None

        token_acceso = obtener_token()

        for periodo in periodos:
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
