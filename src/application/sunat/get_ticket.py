from src.domain.interfaces import TicketsInterface


class GetTicket:
    def __init__(self, ticket_repo: TicketsInterface):
        self.ticket_repo = ticket_repo

    def execute(self, ruc, periodo):
        return self.ticket_repo.traer_ticket(ruc, periodo)
