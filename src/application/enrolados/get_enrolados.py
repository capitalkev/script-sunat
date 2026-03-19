from src.domain.interfaces import ScriptInterface


class GetEnrolado:
    def __init__(self, repository: ScriptInterface):
        self.repository = repository

    def execute(self, limite: int):
        return self.repository.get_enrolado(limite=limite)
