from typing import Any, Protocol
import io
from typing import Optional


class ScriptInterface(Protocol):
    def get_enrolado(self) -> Any: ...
    
    def get_only_enrolado(self, ruc:str) -> Any: ...

    def save_enrolado(self, datos: dict) -> None: ...


class APIClientInterface(Protocol):
    def get_token(
        self, ruc: str, usuario_sol: str, clave_sol: str, id: str, clave: str
    ) -> str: ...

    def _get_headers(self, token_acceso: str) -> dict: ...

    def generar_ticket(self, periodo: str, token_acceso: str) -> str: ...

    def verificar_estado(
        self, numero_ticket: str, token_acceso: str, periodo: str
    ) -> dict: ...

    def descargar_archivo(
        self,
        datos_archivo,
        token_acceso: str,
        periodo: str,
        numero_ticket: str,
        ruc: str,
    ) -> io.BytesIO: ...


class TokenScraperInterface(Protocol):
    def obtener_token_bearer(
        self, ruc: str, usuario_sol: str, clave_sol: str
    ) -> str: ...

class VentasSunatInterface(Protocol):
    def obtener_ventas(self, ruc: str, periodo: str, token_acceso: str) -> dict: ...
    
    def save_ticket(self, ruc: str, periodo: str, ticket: str) -> None: ...
    
class TicketsInterface(Protocol):
    def guardar_ticket(self, ticket: str, ruc: str, periodo: str) -> None: ...
    
    def traer_ticket(self, ruc: str, periodo: str) -> Optional[str]: ...