import requests
import io
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
            raise ValueError(f"Fallo crítico en autenticación: {e}")

    # Generar Ticket
    def generar_ticket(self, periodo, token_acceso) -> str:
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

            print(f"Ticket generado: {numero_ticket}")
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

                print(f" -> Ticket {numero_ticket} | Estado actual: {desc_estado} (Código: {estado})")

                if estado == "06":
                    archivos = registro_actual.get("archivoReporte", [])
                    if archivos:
                        datos_archivo = {
                            "nomArchivoReporte": archivos[0].get("nomArchivoReporte"),
                            "codTipoArchivoReporte": archivos[0].get("codTipoAchivoReporte", ""),
                            "codProceso": registro_actual.get("codProceso"),
                        }
                        return {"estado": "06", "datos_archivo": datos_archivo}
                    else:
                        return {"estado": "ERROR", "mensaje": "Ticket en 06 pero sin archivo"}

                elif estado == "03":
                    return {"estado": "03", "mensaje": "Proceso terminó con errores según SUNAT"}
                
                else:
                    return {"estado": estado, "mensaje": desc_estado}
            else:
                return {"estado": "DESCONOCIDO", "mensaje": "No se encontraron registros"}

        except Exception as e:
            raise RuntimeError(f"Error al consultar estado: {e}")

    def descargar_archivo(
        self, datos_archivo, token_acceso, periodo, numero_ticket, ruc
    ) -> io.BytesIO:
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

            zip_in_memory = io.BytesIO(res_descarga.content)

            with zipfile.ZipFile(zip_in_memory, "r") as zip_ref:
                archivos_extraidos = zip_ref.namelist()

                if archivos_extraidos:
                    nombre_interno = archivos_extraidos[0]
                    csv_bytes = zip_ref.read(nombre_interno)
                    csv_in_memory = io.BytesIO(csv_bytes)
                    
                    return csv_in_memory
                else:
                    raise ValueError("El archivo ZIP de SUNAT está vacío.")

        except Exception as e:
            raise RuntimeError(f"Fallo en la descarga o extracción en memoria: {e}")
