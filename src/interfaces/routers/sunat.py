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
    periodo: str


@router.post("/manual")
def descargar_manual(
    datos: CredencialesManuales,
    action: APIService = Depends(get_api_service),
    save_repo: SaveEnrolado = Depends(dp_save_enrolado),
):
    try:
        # 1. Ejecutamos el proceso de SUNAT
        resultado = action.execute(
            ruc=datos.ruc,
            usuario_sol=datos.usuario_sol,
            clave_sol=datos.clave_sol,
            id=datos.client_id,
            clave=datos.client_secret,
            periodo=datos.periodo,
        )

        datos_bd = {
            "ruc": datos.ruc,
            "usuario_sol": datos.usuario_sol,
            "clave_sol": datos.clave_sol,
            "client_id": datos.client_id,
            "client_secret": datos.client_secret,
        }
        save_repo.execute(datos_bd)

        return {
            "status": "success",
            "tipo": "manual",
            "data": resultado,
            "mensaje": "Descarga exitosa y enrolado guardado en BD.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    return {
        "status": "success",
        "tipo": "automatico_lote",
        "periodo_procesado": periodo_automatico,
        "total_procesados": len(resultados),
        "detalle": resultados
    }