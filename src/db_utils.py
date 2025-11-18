from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Sequence

import cx_Oracle

from .config import OracleConfig


@contextmanager
def oracle_connection(config: OracleConfig) -> Iterator[cx_Oracle.Connection]:
    connection = cx_Oracle.connect(
        user=config.user,
        password=config.password,
        dsn=config.dsn,
        encoding="UTF-8",
    )
    try:
        yield connection
    finally:
        connection.close()


def execute_query(connection: cx_Oracle.Connection, sql: str, params: Sequence[Any] | None = None) -> list[Dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor]


def execute_non_query(connection: cx_Oracle.Connection, sql: str, params: Sequence[Any] | None = None) -> None:
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
    connection.commit()


def chunked(iterable: Iterable[Any], size: int) -> Iterator[list[Any]]:
    bucket: list[Any] = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) == size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket

