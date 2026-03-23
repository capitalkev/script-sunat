# Archivo: src/application/api_sunat/scraping_service.py
from src.domain.interfaces import ScraperClientInterface

class ScrapingService:
    def __init__(self, repository: ScraperClientInterface):
        self.scraper = repository

    def execute(self, ruc: str, usuario_sol: str, clave_sol: str, cantidad_meses: int = 15):
        return self.scraper.descargar_reportes_historicos(
            ruc=ruc, 
            usuario_sol=usuario_sol, 
            clave_sol=clave_sol, 
            cantidad_meses=cantidad_meses
        )