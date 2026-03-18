from src.domain.interfaces import APIClientInterface

class APIService:
    def __init__(self, repository: APIClientInterface):
        self.sunat = repository

    def execute(self, ruc, usuario_sol, clave_sol, id, clave, periodo):
        # 1. Generar token de acceso
        token_acceso = self.sunat.get_token(ruc, usuario_sol, clave_sol, id, clave)
        
        # 2. Solicitar descarga - Retorna un número de ticket
        numero_ticket = self.sunat.solicitar_descarga(periodo, token_acceso)
        
        # 3. Verificar estado de descarga (Retorna diccionario con datos del archivo)
        datos_archivo = self.sunat.verificar_estado(numero_ticket, token_acceso, periodo)
        print(f"Datos del archivo a descargar: {datos_archivo}")
        
        # 4. Validar y descargar
        if datos_archivo and isinstance(datos_archivo, dict):
            self.sunat.descargar_archivo(datos_archivo, token_acceso, periodo, numero_ticket)
            
            return {
                "mensaje": "Archivo descargado exitosamente",
                "ticket": numero_ticket,
                "archivo_zip": datos_archivo.get("nomArchivoReporte")
            }
        else:
            raise ValueError("No se obtuvieron datos válidos para descargar el archivo.")