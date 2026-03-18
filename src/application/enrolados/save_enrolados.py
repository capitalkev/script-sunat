from src.domain.interfaces import ScriptInterface

class SaveEnrolado:
    def __init__(self, repository: ScriptInterface):
        self.repository = repository

    def execute(self, datos: dict):
        self.repository.save_enrolado(datos)