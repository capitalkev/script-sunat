from src.application.sunat.get_token_api import GetTokenAPI
from src.application.sunat.get_token_scraping import GetTokenScraping
from src.application.sunat.get_ticket import GetTicket
from src.domain.interfaces import APIClientInterface


class OrquestadorDescargas:
    def __init__(
        self,
        token_api: GetTokenAPI,
        token_scraper: GetTokenScraping,
        get_ticket: GetTicket,
        sunat_api: APIClientInterface,
    ):
        self.token_api = token_api
        self.token_scraper = token_scraper
        self.get_ticket = get_ticket
        self.sunat_api = sunat_api

    def execute(
        self, ruc, usuario_sol, clave_sol, client_id, client_secret, periodos: list
    ):
        resultados = {}

        def obtener_token():
            try:
                print(f"[{ruc}] 1. Intentando Token API...")
                token1 = self.token_api.execute(
                    ruc, usuario_sol, clave_sol, client_id, client_secret
                )
                if token1:
                    return token1
            except Exception:
                print(f"[{ruc}] Falló Token API. Intentando Playwright...")

            try:
                print(f"[{ruc}] 2. Intentando Token Playwright...")
                token2 = self.token_scraper.execute(ruc, usuario_sol, clave_sol)
                if token2:
                    return token2
            except Exception:
                print(f"[{ruc}] Fallo Crítico en Playwright.")
                return None

        token_acceso = obtener_token()

        for periodo in periodos:
            numero_ticket = self.get_ticket.execute(ruc, periodo)

            try:
                # 2. Verificar estado en SUNAT
                estado_info = self.sunat_api.verificar_estado(
                    numero_ticket, token_acceso, periodo
                )
                estado_codigo = estado_info.get("estado")

                # 3. Descargar si terminó con éxito (06)
                if estado_codigo == "06":
                    datos_archivo = estado_info.get("datos_archivo")
                    archivo_csv_en_memoria = self.sunat_api.descargar_archivo(
                        datos_archivo, token_acceso, periodo, numero_ticket, ruc
                    )

                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": "DESCARGADO_EXITOSAMENTE",
                    }
                else:
                    resultados[periodo] = {
                        "ticket": numero_ticket,
                        "estado": estado_codigo,
                        "mensaje": estado_info.get("mensaje"),
                    }

            except Exception as e:
                print(
                    f"[{ruc}] Error al procesar ticket {numero_ticket} (Periodo: {periodo}): {e}"
                )
                resultados[periodo] = {"estado": "ERROR_PROCESO", "error": str(e)}

        return {"ruc": ruc, "resultados": resultados}
