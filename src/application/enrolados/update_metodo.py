from src.domain.interfaces import ScriptInterface

class UpdateMetodoEnrolado:
    def __init__(self, repository: ScriptInterface):
        self.repository = repository

    def execute(self, ruc: str, metodo: str):
        self.repository.update_metodo(ruc, metodo)