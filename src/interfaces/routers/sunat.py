from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.application.api_sunat.get_sunat import APIService
from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado
from src.interfaces.dependencias.enrolado import (
    dp_get_enrolado,
    get_api_service,
    dp_save_enrolado,
)

router = APIRouter(prefix="/api-sunat", tags=["api-sunat"])


class CredencialesManuales(BaseModel):
    ruc: str
    usuario_sol: str
    clave_sol: str
    client_id: str
    client_secret: str


@router.post("/manual")
def descargar_manual(
    datos: CredencialesManuales,
    action: APIService = Depends(get_api_service),
    save_repo: SaveEnrolado = Depends(dp_save_enrolado),
):
    # 1. Guardar o actualizar las credenciales en BD
    try:
        datos_bd = {
            "ruc": datos.ruc,
            "usuario_sol": datos.usuario_sol,
            "clave_sol": datos.clave_sol,
            "client_id": datos.client_id,
            "client_secret": datos.client_secret,
        }
        save_repo.execute(datos_bd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar credenciales en BD: {e}")

    try:
        token_maestro = action.sunat.get_token(
            datos.ruc, datos.usuario_sol, datos.clave_sol, datos.client_id, datos.client_secret
        )
    except Exception as e:
        return {
            "status": "error",
            "mensaje": f"No se pudo iniciar sesión en SUNAT: {str(e)}"
        }

    hoy = datetime.now()
    anio_actual = hoy.year
    mes_actual = hoy.month
    periodos_a_procesar = []
    
    for _ in range(15):
        periodos_a_procesar.append(f"{anio_actual}{mes_actual:02d}")
        mes_actual -= 1
        if mes_actual == 0:
            mes_actual = 12
            anio_actual -= 1

    # 4. Procesar cada periodo usando el token maestro
    resultados = []
    for periodo in periodos_a_procesar:
        try:
            resultado_mes = action.execute(
                ruc=datos.ruc,
                usuario_sol=datos.usuario_sol,
                clave_sol=datos.clave_sol,
                id=datos.client_id,
                clave=datos.client_secret,
                periodo=periodo,
                token_acceso=token_maestro
            )
            resultados.append({
                "periodo": periodo,
                "status": "success",
                "data": resultado_mes
            })
        except Exception as e:
            resultados.append({
                "periodo": periodo,
                "status": "error",
                "mensaje": str(e)
            })

    return {
        "status": "success",
        "tipo": "manual_historico",
        "total_procesados": len(resultados),
        "mensaje": f"Se procesaron {len(periodos_a_procesar)} meses históricos con un solo token.",
        "detalle": resultados
    }


@router.post("/procesar-lote-automatico")
def procesar_lote_automatico(
    limit: int = 2,
    action: APIService = Depends(get_api_service),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    """
    Este endpoint se ejecuta (por ejemplo) cada madrugada por un CronJob.
    Calcula el mes anterior, extrae los clientes y los procesa uno por uno.
    """
    
    # 1. Calcular automáticamente el Periodo (Mes anterior)
    hoy = datetime.now()
    mes_anterior = hoy.month - 1
    anio = hoy.year
    if mes_anterior == 0:
        mes_anterior = 12
        anio -= 1
    periodo_automatico = f"{anio}{mes_anterior:02d}"
    
    enrolados = repo.execute(limite=limit)

    if not enrolados:
        raise HTTPException(status_code=404, detail="No hay enrolados en la base de datos.")

    resultados = []
    
    for usuario_db in enrolados:
        ruc_actual = usuario_db.get("ruc")
        try:
            # Ejecutamos el caso de uso que interactúa con SUNAT
            resultado = action.execute(
                ruc=ruc_actual,
                usuario_sol=usuario_db["usuario_sol"],
                clave_sol=usuario_db["clave_sol"],
                id=usuario_db["client_id"],
                clave=usuario_db["client_secret"],
                periodo=periodo_automatico,
            )
            # Guardamos el éxito
            resultados.append({
                "ruc": ruc_actual, 
                "status": "success", 
                "ticket": resultado.get("ticket")
            })
            
        except Exception as e:
            resultados.append({
                "ruc": ruc_actual, 
                "status": "error", 
                "mensaje": str(e)
            })
    print(f"Periodo procesado: {periodo_automatico}, Total enrolados: {len(enrolados)}, Resultados: {resultados}")
    return {
        "status": "success",
        "tipo": "automatico_lote",
        "periodo_procesado": periodo_automatico,
        "total_procesados": len(resultados),
        "detalle": resultados
    }