# llenado_inicial_paralelo.py
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.infrastructure.postgresql.connection_sunat import SessionLocal
from src.interfaces.dependencias.enrolado import get_api_service, get_token_scraper
from src.application.api_sunat.orquestador_descargas import OrquestadorDescargas
from src.infrastructure.postgresql.repositories_sunat.sunat import ScriptRepository
from src.infrastructure.postgresql.repositories_sunat.ventas import VentasRepository
from src.application.etl.procesar_ventas import ProcesarVentasETL
from src.interfaces.routers.sunat import generar_periodos


def procesar_un_cliente(cliente: dict, periodos: list) -> tuple:
    """
    Esta función será ejecutada por cada hilo de forma independiente.
    Abre y cierra su propia sesión de base de datos para evitar colisiones.
    """
    ruc = cliente['ruc']
    
    with SessionLocal() as db_hilo:
        # 1. Instanciamos servicios FRESCOS para este hilo
        api = get_api_service()
        scraper = get_token_scraper()
        repo_ventas = VentasRepository(db_hilo)
        etl = ProcesarVentasETL(repo_ventas)
        orquestador = OrquestadorDescargas(api_service=api, token_scraper=scraper, etl_service=etl)

        try:
            resultado = orquestador.execute(
                ruc=ruc,
                usuario_sol=cliente["usuario_sol"],
                clave_sol=cliente["clave_sol"],
                client_id=cliente["client_id"],
                client_secret=cliente["client_secret"],
                periodos=periodos,
            )
            
            # Devolvemos una tupla (RUC, Éxito (Booleano), Mensaje de Error)
            if resultado.get("valido"):
                errores_meses = []
                filas_totales = 0
                
                # REVISAR LA VERDADERA DATA DEL ETL
                for detalle in resultado.get("detalle", []):
                    if detalle["status"] == "error":
                        errores_meses.append(f"Mes {detalle['periodo']}: {detalle.get('mensaje')}")
                    elif "data" in detalle and "etl_stats" in detalle["data"]:
                        filas_totales += detalle["data"]["etl_stats"].get("procesados_ok", 0)

                # Si hubo errores en los meses, lo reportamos como fallo parcial o total
                if errores_meses:
                    return (ruc, False, f"Errores en BD: { ' | '.join(errores_meses) }")
                else:
                    return (ruc, True, f"{filas_totales} filas insertadas")
            else:
                return (ruc, False, "Credenciales inválidas")
                
        except Exception as e:
            return (ruc, False, str(e))


def correr_llenado_paralelo():
    # 1. Obtenemos la lista de clientes (esto lo hacemos secuencialmente en el hilo principal)
    with SessionLocal() as db_principal:
        repo_enrolados = ScriptRepository(db_principal)
        clientes = repo_enrolados.get_enrolado(limite=500)
    
    periodos = generar_periodos(15, incluir_mes_actual=True)
    
    print(f"🚀 Iniciando descarga en PARALELO para {len(clientes)} clientes...\n")

    clientes_exitosos = 0
    clientes_fallidos = []

    # 2. Configuramos el Pool de Hilos
    # MAX_WORKERS = 3 significa que procesará de 3 en 3. 
    # NO lo subas a más de 5 por las restricciones de tu BD y para no ser baneado por SUNAT.
    MAX_WORKERS = 3 

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Enviamos todas las tareas al executor
        futuros = {
            executor.submit(procesar_un_cliente, cliente, periodos): cliente 
            for cliente in clientes
        }

        # as_completed nos permite atrapar los resultados conforme van terminando, 
        # sin importar el orden en que empezaron
        for futuro in as_completed(futuros):
            ruc, exito, mensaje = futuro.result()
            
            if exito:
                print(f"✓ Cliente {ruc} procesado correctamente. ({mensaje})") # <- Te dirá cuántas filas guardó
                clientes_exitosos += 1
            else:
                print(f"❌ Fallo {ruc}: {mensaje}")
                clientes_fallidos.append(ruc)

    # 3. Resumen Final
    print("\n" + "="*50)
    print("RESUMEN DE DESCARGA PARALELA")
    print("="*50)
    print(f"Total procesados: {len(clientes)}")
    print(f"Exitosos: {clientes_exitosos}")
    print(f"Fallidos: {len(clientes_fallidos)}")
    if clientes_fallidos:
        print("RUCs con problemas que debes revisar:")
        for ruc_malo in clientes_fallidos:
            print(f" - {ruc_malo}")
    print("="*50)


if __name__ == "__main__":
    correr_llenado_paralelo()