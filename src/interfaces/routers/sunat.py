from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

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


@router.post("/automatico/{ruc}/{periodo}")
def descargar_automatico(
    ruc: str,
    periodo: str,
    action: APIService = Depends(get_api_service),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    usuario_db = repo.execute(ruc=ruc)

    if not usuario_db:
        raise HTTPException(
            status_code=404,
            detail=f"El RUC {ruc} no está registrado en la base de datos.",
        )

    try:
        resultado = action.execute(
            ruc=usuario_db["ruc"],
            usuario_sol=usuario_db["usuario_sol"],
            clave_sol=usuario_db["clave_sol"],
            id=usuario_db["client_id"],
            clave=usuario_db["client_secret"],
            periodo=periodo,
        )
        return {"status": "success", "tipo": "automatico", "data": resultado}

    except KeyError as e:
        raise HTTPException(
            status_code=500, detail=f"Falta la columna {str(e)} en la tabla enrolado."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
