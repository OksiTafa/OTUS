from pydantic import BaseModel, SecretStr


class AppConfig(BaseModel):
    title: str = "Blog"
    secret_key: SecretStr
