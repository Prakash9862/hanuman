from hanuman.core.config import settings

if __name__ == "__main__":
    for key, value in settings.model_dump().items():
        if hasattr(value, "get_secret_value"):
            value = value.get_secret_value()
        print(f"{key}: {value}")
