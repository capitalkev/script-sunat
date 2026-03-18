import requests
import sys
import time

from src.domain.interfaces import APIClientInterface


class APISUNAT(APIClientInterface):

    def get_token(self, ruc, usuario_sol, clave_sol, id, clave) -> str:
        url_seguridad = (
            f"https://api-seguridad.sunat.gob.pe/v1/clientessol/{id}/oauth2/token/"
        )

        payload = {
            "grant_type": "password",
            "scope": "https://api-sire.sunat.gob.pe",
            "client_id": id,
            "client_secret": clave,
            "username": f"{ruc}{usuario_sol.upper()}",
            "password": clave_sol,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(url_seguridad, data=payload, headers=headers)
            response.raise_for_status()
            datos = response.json()
            token_acceso = datos.get("access_token")

        except requests.exceptions.RequestException as e:
            print(f"Error al obtener el token: {e}")
            if response is not None and response.text:
                print(f"Detalle de SUNAT: {response.text}")
            token_acceso = None

        return token_acceso

    def _get_headers(self, token_acceso) -> dict:
        headers_sire = {
            "Authorization": f"Bearer {token_acceso}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        return headers_sire

    def solicitar_descarga(self, periodo, token_acceso) -> str:
        url_exportar = f"https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvie/propuesta/web/propuesta/{periodo}/exportapropuesta"
        params_exportar = {"codTipoArchivo": "1"}
        try:
            res_exportar = requests.get(
                url_exportar,
                params=params_exportar,
                headers=self._get_headers(token_acceso),
            )
            res_exportar.raise_for_status()
            numero_ticket = res_exportar.json().get("numTicket")

            if not numero_ticket:
                # ¡AQUÍ! Cambiamos sys.exit por raise
                raise ValueError("No se recibió un número de ticket de SUNAT.")

            print(f"✓ Ticket generado: {numero_ticket}\n")
            
            # ¡AQUÍ! Retornamos el valor prometido (str)
            return numero_ticket 

        except Exception as e:
            # ¡AQUÍ! Cambiamos sys.exit por raise
            raise RuntimeError(f"Error al solicitar reporte: {e}")


    def verificar_estado(self, numero_ticket, token_acceso, periodo) -> dict:
        url_estado = "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
        params_estado = {
            "perIni": periodo, "perFin": periodo, "page": 1, "perPage": 20,
            "numTicket": numero_ticket, "codLibro": "140000", "codOrigenEnvio": "2",
        }
        
        while True:
            try:
                res_estado = requests.get(
                    url_estado,
                    params=params_estado,
                    headers=self._get_headers(token_acceso),
                )
                res_estado.raise_for_status()
                registros = res_estado.json().get("registros", [])

                if registros:
                    registro_actual = registros[0]
                    estado = registro_actual.get("codEstadoProceso")
                    desc_estado = registro_actual.get("desEstadoProceso")

                    print(f" -> Estado actual: {desc_estado} (Código: {estado})")

                    if estado == "06":
                        archivos = registro_actual.get("archivoReporte", [])

                        if archivos:
                            datos_archivo = {
                                "nomArchivoReporte": archivos[0].get("nomArchivoReporte"),
                                "codTipoArchivoReporte": archivos[0].get("codTipoAchivoReporte", ""),
                                "codProceso": registro_actual.get("codProceso"),
                            }
                            print("✓ El archivo está listo.\n")
                            
                            return datos_archivo 
                        else:
                            raise ValueError("El ticket terminó, pero no se encontró el archivo.")

                    elif estado == "03":
                        raise RuntimeError("El proceso terminó con errores según SUNAT.")
                    else:
                        time.sleep(3)
                else:
                    time.sleep(3)

            except Exception as e:
                raise RuntimeError(f"Error al consultar estado: {e}")

    def descargar_archivo(
        self, datos_archivo, token_acceso, periodo, numero_ticket
    ) -> None:
        url_descarga = "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/archivoreporte"
        params_descarga = {
            "nomArchivoReporte": datos_archivo["nomArchivoReporte"],
            "codTipoArchivoReporte": datos_archivo["codTipoArchivoReporte"],
            "codLibro": "140000",
            "perTributario": periodo,
            "codProceso": datos_archivo["codProceso"],
            "numTicket": numero_ticket,
        }
        try:
            res_descarga = requests.get(
                url_descarga,
                params=params_descarga,
                headers=self._get_headers(token_acceso),
            )
            res_descarga.raise_for_status()

            # Escribimos los bytes directamente a un archivo local
            nombre_local = f"propuesta_sire_{periodo}.zip"
            with open(nombre_local, "wb") as f:
                f.write(res_descarga.content)

            print(f"✓ ¡Proceso completado! Archivo guardado como '{nombre_local}'.")
        except Exception as e:
            print(f"✗ Error al descargar el archivo: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalle: {e.response.text}")
