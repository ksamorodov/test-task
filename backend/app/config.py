from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    x_csv: Path = Path(__file__).parent.parent.parent / "interview" / "interview.X.csv"
    y_csv: Path = Path(__file__).parent.parent.parent / "interview" / "interview.y.csv"


settings = Settings()
