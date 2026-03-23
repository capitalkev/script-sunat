from src.application.api_sunat.get_sunat import APIService
from src.application.api_sunat.scraping_service import ScrapingService
from src.application.enrolados.update_metodo import UpdateMetodoEnrolado

class OrquestadorDescargas:
    def __init__(
        self, 
        api_service: APIService, 
        scraper_service: ScrapingService, 
        update_metodo_repo: UpdateMetodoEnrolado
    ):
        self.api = api_service
        self.scraper = scraper_service
        self.update_metodo = update_metodo_repo

    def execute(self, ruc, usuario_sol, clave_sol, client_id, client_secret, metodo, periodos: list):
        resultados = []

        if metodo == "scraper":
            print(f"[{ruc}] Método en BD es 'scraper'. Usando Playwright directamente...")
            try:
                # El scraper usa cantidad_meses, que equivale al tamaño de la lista de periodos
                res_scraping = self.scraper.execute(ruc, usuario_sol, clave_sol, cantidad_meses=len(periodos))
                return {"via": "scraper_directo", "detalle": res_scraping}
            except Exception as e:
                return {"via": "scraper_directo", "detalle": [{"ruc": ruc, "status": "error", "mensaje": str(e)}]}

        else:
            print(f"[{ruc}] Método es 'api'. Intentando SUNAT API...")
            try:
                # 1. Intentamos obtener el token maestro
                token = self.api.sunat.get_token(ruc, usuario_sol, clave_sol, client_id, client_secret)
                
                # 2. Si hay token, procesamos todos los periodos
                for periodo in periodos:
                    try:
                        res_api = self.api.execute(
                            ruc=ruc, usuario_sol=usuario_sol, clave_sol=clave_sol,
                            id=client_id, clave=client_secret, periodo=periodo, token_acceso=token
                        )
                        resultados.append({"periodo": periodo, "status": "success", "data": res_api})
                    except Exception as err_api:
                        resultados.append({"periodo": periodo, "status": "error", "mensaje": str(err_api)})
                        
                return {"via": "api_oficial", "detalle": resultados}

            except Exception as e_token:
                # 3. FALLBACK: Si el token falla, activamos Scraper y actualizamos BD
                print(f"[{ruc}] Falló la API: {e_token}. Activando Scraper y actualizando BD...")
                try:
                    self.update_metodo.execute(ruc, "scraper") # Actualiza PostgreSQL
                    
                    res_scraping = self.scraper.execute(ruc, usuario_sol, clave_sol, cantidad_meses=len(periodos))
                    return {"via": "scraper_fallback", "detalle": res_scraping}
                except Exception as e_scraper:
                    return {"via": "colapso_total", "detalle": [{"ruc": ruc, "status": "error", "mensaje": f"API: {e_token} | Scraper: {e_scraper}"}]}