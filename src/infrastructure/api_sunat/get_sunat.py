import requests
import time
import os
import zipfile

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

            if response.status_code != 200:
                raise ValueError(
                    f"SUNAT rechazó las credenciales: {response.status_code} - {response.text}"
                )

            response.raise_for_status()
            datos = response.json()
            return datos.get("access_token")

        except Exception as e:
            # Aquí detenemos el script inmediatamente, evitando el falso "401" después
            raise ValueError(f"Fallo crítico en autenticación: {e}")

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
                raise ValueError("No se recibió un número de ticket de SUNAT.")

            print(f"✓ Ticket generado: {numero_ticket}\n")
            return numero_ticket

        except requests.exceptions.HTTPError as e:
            # Si SUNAT arroja 500, sabemos que es porque la propuesta está vacía según su manual
            if e.response.status_code == 500:
                raise RuntimeError(
                    "SUNAT Error 500: La propuesta está vacía (sin comprobantes) para este periodo."
                )
            else:
                raise RuntimeError(
                    f"Error HTTP de SUNAT: {e.response.status_code} - {e.response.text}"
                )

    def _get_headers(self, token_acceso) -> dict:
        headers_sire = {
            "Authorization": f"Bearer {token_acceso}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        return headers_sire

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
                                "nomArchivoReporte": archivos[0].get(
                                    "nomArchivoReporte"
                                ),
                                "codTipoArchivoReporte": archivos[0].get(
                                    "codTipoAchivoReporte", ""
                                ),
                                "codProceso": registro_actual.get("codProceso"),
                            }
                            print("✓ El archivo está listo.\n")

                            return datos_archivo
                        else:
                            raise ValueError(
                                "El ticket terminó, pero no se encontró el archivo."
                            )

                    elif estado == "03":
                        raise RuntimeError(
                            "El proceso terminó con errores según SUNAT."
                        )
                    else:
                        time.sleep(3)
                else:
                    time.sleep(3)

            except Exception as e:
                raise RuntimeError(f"Error al consultar estado: {e}")

    def descargar_archivo(
        self, datos_archivo, token_acceso, periodo, numero_ticket
    ) -> str:
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

            # 1. Crear carpeta de descargas si no existe
            directorio_descargas = "descargas_sire"
            os.makedirs(directorio_descargas, exist_ok=True)

            # 2. Nombre único para el ZIP usando el número de ticket
            nombre_original = datos_archivo["nomArchivoReporte"]
            ruta_zip = os.path.join(
                directorio_descargas, f"{numero_ticket}_{nombre_original}"
            )

            # Guardar el ZIP
            with open(ruta_zip, "wb") as f:
                f.write(res_descarga.content)

            # 3. Extraer el archivo
            ruta_extraccion = os.path.join(
                directorio_descargas, f"extraido_{numero_ticket}"
            )
            os.makedirs(ruta_extraccion, exist_ok=True)

            ruta_archivo_final = ""
            with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
                zip_ref.extractall(ruta_extraccion)
                archivos_extraidos = zip_ref.namelist()

                if archivos_extraidos:
                    # Obtenemos la ruta del primer archivo extraído (el Excel/CSV)
                    ruta_archivo_final = os.path.join(
                        ruta_extraccion, archivos_extraidos[0]
                    )

            print(f"✓ Archivo extraído listo para procesar en: '{ruta_archivo_final}'")

            os.remove(ruta_zip)

            return ruta_archivo_final

        except Exception as e:
            print(f"✗ Error al descargar o extraer el archivo: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalle: {e.response.text}")
            raise RuntimeError(f"Fallo en la descarga: {e}")
