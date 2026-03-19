from src.domain.interfaces import APIClientInterface

class APIService:
    def __init__(self, repository: APIClientInterface):
        self.sunat = repository

    def execute(self, ruc, usuario_sol, clave_sol, id, clave, periodo, token_acceso=None):
        if not token_acceso:
            token_acceso = self.sunat.get_token(ruc, usuario_sol, clave_sol, id, clave)
            
        numero_ticket = self.sunat.solicitar_descarga(periodo, token_acceso)
        datos_archivo = self.sunat.verificar_estado(numero_ticket, token_acceso, periodo)
        
        if datos_archivo and isinstance(datos_archivo, dict):
            ruta_archivo = self.sunat.descargar_archivo(datos_archivo, token_acceso, periodo, numero_ticket)
            
            return {
                "mensaje": "Archivo descargado y extraído exitosamente",
                "ticket": numero_ticket,
                "ruta_archivo": ruta_archivo
            }
        else:
            raise ValueError("No se obtuvieron datos válidos para descargar el archivo.")