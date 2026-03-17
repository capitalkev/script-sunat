from src.domain.interfaces import APIClientInterface


class APIService:
    def __init__(self, repository: APIClientInterface):
        self.sunat = repository

    def execute(self, ruc, usuario_sol, clave_sol, id, clave, periodo):
        # Generar token de acceso - Retorna un ticket de descarga
        token_acceso = self.sunat.get_token(ruc, usuario_sol, clave_sol, id, clave)
        # Solicitar descarga - Retorna un número de ticket
        numero_ticket = self.sunat.solicitar_descarga(periodo, token_acceso)
        # Verificar estado de descarga 
        estado_descarga = self.sunat.verificar_estado(numero_ticket, token_acceso, periodo)
        print(f"Estado de descarga: {estado_descarga}")
        
        if estado_descarga == "COMPLETED":
            datos_archivo = {}
            self.sunat.descargar_archivo(datos_archivo, token_acceso, periodo, numero_ticket)