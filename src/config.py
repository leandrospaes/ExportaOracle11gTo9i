from dataclasses import dataclass
import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class OracleConfig:
    dsn: str
    user: str
    password: str
    schema: Optional[str] = None
    client_path: Optional[str] = None

    @staticmethod
    def from_env(prefix: str) -> "OracleConfig":
        env = prefix.upper()
        dsn = os.environ.get(f"{env}_DSN")
        user = os.environ.get(f"{env}_USER")
        password = os.environ.get(f"{env}_PASSWORD")
        # Path espec├¡fico para este banco, ou fallback para path global
        client_path = os.environ.get(f"{env}_CLIENT_PATH") or os.environ.get("ORACLE_CLIENT_PATH")

        if not all([dsn, user, password]):
            missing = ", ".join(
                name for name, value in [
                    (f"{env}_DSN", dsn),
                    (f"{env}_USER", user),
                    (f"{env}_PASSWORD", password),
                ]
                if not value
            )
            raise ValueError(f"Vari├íveis ausentes para {env}: {missing}")

        return OracleConfig(
            dsn=dsn,
            user=user,
            password=password,
            schema=os.environ.get(f"{env}_SCHEMA"),
            client_path=client_path,
        )


@dataclass(frozen=True)
class ProjectConfig:
    source: OracleConfig
    target: OracleConfig
    schemas: list[str]

    @staticmethod
    def load(schemas: Optional[str]) -> "ProjectConfig":
        schema_list = []
        if schemas:
            schema_list = [part.strip().upper() for part in schemas.split(",") if part.strip()]

        return ProjectConfig(
            source=OracleConfig.from_env("ORACLE_11G"),
            target=OracleConfig.from_env("ORACLE_9I"),
            schemas=schema_list,
        )

