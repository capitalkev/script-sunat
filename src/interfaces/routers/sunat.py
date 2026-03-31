# src/interfaces/routers/sunat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.application.enrolados.get_enrolados import GetEnrolado
from src.application.enrolados.get_only_enrolados import GetOnlyEnrolado
from src.application.enrolados.save_enrolados import SaveEnrolado
from src.application.sunat.orquestador_descargas import OrquestadorDescargas
from src.application.sunat.orquestador_tickets import OrquestadorTickets

from src.interfaces.dependencias.enrolado import (
    dp_get_enrolado,
    dp_get_only_enrolado,
    dp_orquestador_descargas,
    dp_orquestador_tickets,
    dp_save_enrolado,
)

router = APIRouter(prefix="/api-sunat", tags=["api-sunat"])


class CredencialesManuales(BaseModel):
    ruc: str
    usuario_sol: str
    clave_sol: str
    client_id: str
    client_secret: str


def generar_periodos(cantidad_meses: int) -> list:
    """
    Genera una lista de periodos en formato YYYYMM, comenzando desde el mes actual
    hacia atrás, según la cantidad de meses especificada.
    """
    hoy = datetime.now()
    periodos = []
    for i in range(cantidad_meses):
        mes = hoy.month - i
        año = hoy.year
        while mes <= 0:
            mes += 12
            año -= 1
        periodos.append(f"{año}{mes:02d}")
    return periodos


@router.post("/manual-generar-tickets")
def enrolar_y_generar_tickets_manual(
    datos: CredencialesManuales,
    orquestador_tickets: OrquestadorTickets = Depends(dp_orquestador_tickets),
    save_repo: SaveEnrolado = Depends(dp_save_enrolado),
):
    periodos = generar_periodos(13)

    try:
        save_repo.execute(datos.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al guardar enrolado en BD: {e}"
        )

    resultado = orquestador_tickets.execute(
        ruc=datos.ruc,
        usuario_sol=datos.usuario_sol.upper(),
        clave_sol=datos.clave_sol,
        client_id=datos.client_id,
        client_secret=datos.client_secret,
        periodos=periodos,
    )

    resultados_tickets = resultado.get("resultados", {})

    if not resultados_tickets:
        raise HTTPException(
            status_code=401,
            detail="No se pudo procesar ningún periodo. Verifica las credenciales SOL.",
        )

    return {
        "status": "success",
        "tipo": "manual_historico",
        "mensaje": "Cliente enrolado y tickets generados exitosamente. Listos para la descarga.",
        "total_procesados": len(resultados_tickets),
        "detalle": resultados_tickets,
    }


@router.post("/manual/descargar/{ruc}")
def descargar_manual_tickets(
    ruc: str,
    orquestador_descargas: OrquestadorDescargas = Depends(dp_orquestador_descargas),
    repo: GetOnlyEnrolado = Depends(dp_get_only_enrolado),
):
    enrolado = repo.execute(ruc=ruc)

    if not enrolado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron credenciales para el RUC {ruc}. Asegúrate de enrolarlo primero.",
        )
    periodos = generar_periodos(13)

    resultado = orquestador_descargas.execute(
        ruc=enrolado["ruc"],
        usuario_sol=enrolado["usuario_sol"],
        clave_sol=enrolado["clave_sol"],
        client_id=enrolado["client_id"],
        client_secret=enrolado["client_secret"],
        periodos=periodos,
    )

    return {
        "status": "success",
        "tipo": "descarga_manual_historico",
        "mensaje": "Revisión de tickets y descargas finalizada.",
        "detalle": resultado.get("resultados", {}),
    }


@router.post("/generar-tickets-automaticos")
def procesar_lote_automatico(
    limit: int = 2,
    orquestador: OrquestadorTickets = Depends(dp_orquestador_tickets),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    enrolados = repo.execute(limite=limit)  # enrolados
    periodos = generar_periodos(1)  # periodos

    resultados_lote = []

    for emp in enrolados:
        resultado = orquestador.execute(
            ruc=emp["ruc"],
            usuario_sol=emp["usuario_sol"],
            clave_sol=emp["clave_sol"],
            client_id=emp["client_id"],
            client_secret=emp["client_secret"],
            periodos=periodos,
        )
        resultados_lote.append(
            {
                "detalle": resultado,
            }
        )

    return {
        "status": "success",
        "resultados": resultados_lote,
    }


@router.get("/descargar-archivos")
def descargar_archivos(
    limit: int = 2,
    orquestador: OrquestadorDescargas = Depends(dp_orquestador_descargas),
    repo: GetEnrolado = Depends(dp_get_enrolado),
):
    enrolados = repo.execute(limite=limit)
    periodos = generar_periodos(1)

    resultados_lote = []

    for emp in enrolados:
        resultado = orquestador.execute(
            ruc=emp["ruc"],
            usuario_sol=emp["usuario_sol"],
            clave_sol=emp["clave_sol"],
            client_id=emp["client_id"],
            client_secret=emp["client_secret"],
            periodos=periodos,
        )
        resultados_lote.append(
            {
                "detalle": resultado,
            }
        )
    return {
        "status": "success",
        "resultados": resultados_lote,
    }
