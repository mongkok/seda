from pydantic import BaseSettings


class Settings(BaseSettings):
    ROOT_PATH: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
