from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.application.api_sunat.get_sunat import APIService
from src.interfaces.dependencias.enrolado import get_operaciones_repo, get_api_service
from src.infrastructure.postgresql.repositories_sunat.sunat import OperacionesRepository

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
    datos: CredencialesManuales, action: APIService = Depends(get_api_service)
):
    """
    Este endpoint recibe TODAS las credenciales en el body de la petición.
    Ideal para usuarios que aún no están en la base de datos.
    """
    try:
        resultado = action.execute(
            ruc=datos.ruc,
            usuario_sol=datos.usuario_sol,
            clave_sol=datos.clave_sol,
            id=datos.client_id,
            clave=datos.client_secret,
            periodo=datos.periodo,
        )
        return {"status": "success", "tipo": "manual", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automatico/{ruc}/{periodo}")
def descargar_automatico(
    ruc: str,
    periodo: str,
    action: APIService = Depends(get_api_service),
    repo: OperacionesRepository = Depends(get_operaciones_repo),
):
    """
    Este endpoint solo recibe el RUC y el Periodo.
    Busca las credenciales en la base de datos y ejecuta el proceso.
    """
    enrolados = repo.get_enrolado(ruc=ruc)

    if not enrolados or len(enrolados) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"El RUC {ruc} no está registrado en la base de datos.",
        )

    usuario_db = enrolados[0]

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
