from src.domain.interfaces import APIClientInterface


class APIRobotService:
    def __init__(self, repository: APIClientInterface):
        self.sunat = repository
        
    def execute(self, claves_enrolados):
        
        # Generar token de acceso
        token_acceso = self.sunat.get_token(
            claves_enrolados["ruc"],
            claves_enrolados["usuario_sol"],
            claves_enrolados["clave_sol"],
            claves_enrolados["id"],
            claves_enrolados["clave"],
        )
        
        for periodo in range(202601, 202603):

            numero_ticket = self.sunat.solicitar_descarga(periodo, token_acceso)

            datos_archivo = self.sunat.verificar_estado(
                numero_ticket, token_acceso, periodo
            )
            print(f"Estado de descarga: {datos_archivo}")

            if datos_archivo and isinstance(datos_archivo, dict):
                self.sunat.descargar_archivo(
                    datos_archivo, token_acceso, periodo, numero_ticket
                )

                return {
                    "status": "success",
                    "mensaje": f"Archivo {datos_archivo.get('nomArchivoReporte')} descargado con éxito.",
                    "ticket": numero_ticket,
                }
            else:
                return {
                    "status": "error",
                    "mensaje": "No se obtuvieron datos válidos para descargar.",
                }