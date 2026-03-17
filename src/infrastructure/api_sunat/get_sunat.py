import requests
import sys
import time

from src.domain.interfaces import APIClientInterface


class APISUNAT(APIClientInterface):
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

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
                print("✗ No se recibió un número de ticket.")
                sys.exit(1)

            print(f"✓ Ticket generado: {numero_ticket}\n")
        except Exception as e:
            print(f"✗ Error al solicitar reporte: {e}")
            sys.exit(1)

    def verificar_estado(self, numero_ticket, token_acceso, periodo) -> dict:
        url_estado = "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
        params_estado = {
            "perIni": periodo,
            "perFin": periodo,
            "page": 1,
            "perPage": 20,
            "numTicket": numero_ticket,
            "codLibro": "140000",
            "codOrigenEnvio": "2",
        }
        ticket_terminado = False
        datos_archivo = {}

        while not ticket_terminado:
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

                    # Código 06 significa "Terminado"
                    if estado == "06":
                        ticket_terminado = True
                        detalle = registro_actual.get("detalleTicket", {})
                        archivos = detalle.get("archivoReporte", [])

                        if archivos:
                            # Guardamos las variables extraídas dinámicamente para el Paso 3
                            datos_archivo = {
                                "nomArchivoReporte": archivos[0].get(
                                    "nomArchivoReporte"
                                ),
                                "codTipoArchivoReporte": archivos[0].get(
                                    "codTipoAchivoReporte"
                                ),
                                "codProceso": registro_actual.get("codProceso"),
                            }
                            print("✓ El archivo está listo.\n")

                            return datos_archivo
                        else:
                            print(
                                "✗ El ticket terminó, pero no se encontró el archivo en la respuesta."
                            )
                            sys.exit(1)

                    elif estado == "03":
                        print("✗ El proceso terminó con errores según SUNAT.")
                        sys.exit(1)
                    else:
                        time.sleep(3)
                else:
                    time.sleep(3)

            except Exception as e:
                print(f"✗ Error al consultar estado: {e}")
                sys.exit(1)

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
