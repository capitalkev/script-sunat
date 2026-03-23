# Archivo: src/infrastructure/playwright_sunat/scraper.py
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from src.domain.interfaces import ScraperClientInterface

class PlaywrightSUNAT(ScraperClientInterface):
    def __init__(self):
        self.meses_sunat = {
            1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN",
            7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC",
        }
        self.login_url = "https://api-seguridad.sunat.gob.pe/v1/clientessol/4f3b88b3-d9d6-402a-b85d-6a0bc857746a/oauth2/loginMenuSol?lang=es-PE&showDni=true&showLanguages=false&originalUrl=https://e-menu.sunat.gob.pe/cl-ti-itmenu/AutenticaMenuInternet.htm&state=rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAAx3CAAAABAAAAADdAAEZXhlY3B0AAZwYXJhbXN0AEsqJiomL2NsLXRpLWl0bWVudS9NZW51SW50ZXJuZXQuaHRtJmI2NGQyNmE4YjVhZjA5MTkyM2IyM2I2NDA3YTFjMWRiNDFlNzMzYTZ0AANleGVweA=="

    def descargar_reportes_historicos(self, ruc: str, usuario_sol: str, clave_sol: str, cantidad_meses: int = 15) -> list:
        resultados = []
        periodos = self._obtener_meses_historicos(cantidad_meses)
        os.makedirs("descargas_sire_scraping", exist_ok=True)

        with sync_playwright() as p:
            # En producción backend cambiar headless=True
            browser = p.chromium.launch(channel="msedge", headless=False)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            try:
                page.goto(self.login_url)
                self._login(page, ruc, usuario_sol, clave_sol)
                self._navegar_a_sire(page)
                
                frame = page.frame_locator("iframe[name='iframeApplication']")
                try:
                    frame.locator("//button[text()='Aceptar']").click(timeout=3000)
                except:
                    pass

                for periodo in periodos:
                    anio_str = periodo["anio"]
                    mes_str = periodo["mes"]
                    mes_num = periodo["mes_num"]
                    periodo_formato_api = f"{anio_str}{mes_num:02d}" # Formato 202603

                    try:
                        # 1. Seleccionar Año
                        frame.locator("ng-select[formcontrolname='anio']").click()
                        frame.locator(f"//div[@role='option' and contains(., '{anio_str}')]").click()

                        # 2. Seleccionar Mes
                        frame.locator("ng-select[formcontrolname='mes']").click()
                        frame.locator(f"//div[@role='option' and contains(., '{mes_str}')]").click()

                        # 3. Aceptar para cargar la tabla
                        frame.locator("#btn-aceptar").click()
                        page.wait_for_timeout(3000)

                        # Verificar si existe el boton de exportar
                        try:
                            frame.locator("button-export .dropdown-toggle").click(timeout=3000)
                            with page.expect_download() as download_info:
                                frame.locator("//button[@class='dropdown-item' and text()='CSV']").click()
                            
                            download = download_info.value
                            nombre_archivo = f"{anio_str}_{mes_str}_{download.suggested_filename}"
                            ruta_final = os.path.join("descargas_sire_scraping", nombre_archivo)
                            download.save_as(ruta_final)
                            
                            frame.get_by_role("button", name="Aceptar").click()

                            resultados.append({
                                "periodo": periodo_formato_api,
                                "status": "success",
                                "ruta_archivo": ruta_final,
                                "mensaje": "Descargado vía Scraping"
                            })
                        except Exception as e:
                            resultados.append({
                                "periodo": periodo_formato_api,
                                "status": "error",
                                "mensaje": f"No hay datos para exportar: {str(e)}"
                            })
                    except Exception as e:
                        resultados.append({
                            "periodo": periodo_formato_api,
                            "status": "error",
                            "mensaje": f"Error UI Scraping: {str(e)}"
                        })
            except Exception as e:
                raise RuntimeError(f"Fallo crítico en Scraping: {e}")
            finally:
                context.close()
                browser.close()
                
        return resultados

    def _obtener_meses_historicos(self, cantidad_meses):
        hoy = datetime.now()
        mes_actual, anio_actual = hoy.month, hoy.year
        periodos = []
        for _ in range(cantidad_meses):
            periodos.append({"anio": str(anio_actual), "mes": self.meses_sunat[mes_actual], "mes_num": mes_actual})
            mes_actual -= 1
            if mes_actual == 0:
                mes_actual, anio_actual = 12, anio_actual - 1
        return periodos

    def _login(self, page, ruc, usuario, clave):
        page.locator("#txtRuc").fill(ruc)
        page.locator("#txtUsuario").fill(usuario)
        page.locator("#txtContrasena").fill(clave)
        page.locator("#btnAceptar").click()

    def _navegar_a_sire(self, page):
        page.locator("#divOpcionServicio2 > h4").first.click()
        page.locator("#nivel1_60 > span.spanNivelDescripcion").first.click()
        page.locator("#nivel2_60_2 > span.spanNivelDescripcion").first.click()
        page.locator("#nivel3_60_2_1 > span.spanNivelDescripcion").first.click()
        page.locator("#nivel4_60_2_1_1_1 > span").first.click()