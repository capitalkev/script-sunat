from fastapi import APIRouter, Depends

from src.application.api_sunat.get_sunat import APIService

router = APIRouter(prefix="/api-sunat", tags=["api-sunat"])

@router.get("/{ruc_deudor}")
def extraer_deudores(
    action: APIService = Depends()

):
    ruc = '20612400688'
    usuario_sol = 'altrysjr'
    clave_sol = 'Misolitario2'
    id = 'c334ecef-9d30-4fb3-833f-b4249e909516'
    clave = 'X9ODzGi7/FOYZ44/T55h/g=='
    periodo = '202501'
    return action.execute(ruc=ruc, usuario_sol=usuario_sol, clave_sol=clave_sol, id=id, clave=clave, periodo=periodo)