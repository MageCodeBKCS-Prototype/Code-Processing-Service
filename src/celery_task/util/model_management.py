from .machine_detection_model import get_model_tokenizer


class ModelInfo:
    def __init__(self, model_name: str, model_path: str, languages: list[str], device: str = "cpu"):
        self.model_name = model_name
        self.model_path = model_path
        self.languages = languages
        self.device = device
        self.tokenizer = None
        self.model = None

    def load(self):
        if self.tokenizer is None and self.model is None:
            self.tokenizer, self.model = get_model_tokenizer(self.device, self.model_name, self.model_path)


class ModelManager:
    def __init__(self, models_info_list: list[ModelInfo]):
        self.model_info_list = models_info_list
        self.loaded = False

    def load(self):
        if not self.loaded:
            for model_info in self.model_info_list:
                model_info.load()
                print("Model ready")
            self.loaded = True

    def get_model_by_language(self, language: str) -> ModelInfo | None:
        for model_info in self.model_info_list:
            if language in model_info.languages:
                return model_info

        return None
