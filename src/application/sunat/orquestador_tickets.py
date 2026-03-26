from src.application.sunat.create_ticket import CreateTicket
from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.application.sunat.save_ticket import SaveTicket
from src.infrastructure.api_sunat.get_sunat import APISUNAT
from src.infrastructure.playwright_sunat.scraper import PlaywrightTokenScraper


class OrquestadorTickets:
    def __init__(self, guardar_ticket: SaveTicket):
        self.token_api = GetTokenAPI(APISUNAT())
        self.token_scraper = GetTokenScraping(PlaywrightTokenScraper())
        self.generar_ticket = CreateTicket(APISUNAT())
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

        tickets = self.generar_ticket.execute(periodos, token_acceso)

        if tickets:
            for periodo, numero_ticket in tickets.items():
                if numero_ticket:
                    try:
                        self.guardar_ticket.execute(ruc, periodo, numero_ticket)
                        print(
                            f"[{ruc}] Ticket {numero_ticket} guardado en BD (Periodo: {periodo})"
                        )
                    except Exception as e:
                        print(
                            f"[{ruc}] Error al guardar ticket {numero_ticket} en BD: {e}"
                        )

        resultados["ruc"] = ruc
        resultados["tickets"] = tickets

        return {"resultados": resultados}
