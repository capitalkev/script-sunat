from src.domain.interfaces import ScriptInterface

class GetEnrolado:
    def __init__(self, repository: ScriptInterface):
        self.repository = repository

    def execute(self, ruc: str):
        if ruc:
            return self.repository.get_enrolado_by_ruc(ruc)
        return self.repository.get_enrolado()