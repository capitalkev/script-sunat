from src.domain.interfaces import APIClientInterface


class CreateTicket:
    def __init__(self, sunat_client: APIClientInterface):
        self.sunat = sunat_client

    def execute(self, periodo, token_acceso):
        return self.sunat.generar_ticket(periodo, token_acceso)
