from typing import Any, Sequence, Mapping, Optional
import os
import psycopg

from .base_code_block import BaseCodeBlock


class SQL(BaseCodeBlock):
    """
    The SQLCodeBlock provides basic access to the Bismuth SQL service.
    """
    conn: psycopg.Connection

    def __init__(self, pg_uri: Optional[str] = None):
        if pg_uri:
            self.conn = psycopg.connect(pg_uri)
        else:
            self.conn = psycopg.connect(
                host="169.254.169.254",
                user="bismuth",
                password=os.environ['BISMUTH_AUTH'],
                dbname="bismuth",
            )

    def execute(self, sql: str, params: Sequence[Any]|Mapping[str, Any] = {}):
        """
        Run the given SQL, returning no results.
        """
        with self.conn.cursor() as cur:
            with self.conn.transaction():
                cur.execute(sql, params)

    def fetchone(self, sql: str, params: Sequence[Any]|Mapping[str, Any] = {}) -> Optional[tuple[Any, ...]]:
        """
        Run the given SQL, returning a single row.
        """
        with self.conn.cursor() as cur:
            with self.conn.transaction():
                cur.execute(sql, params)
                return cur.fetchone()

    def fetchall(self, sql: str, params: Sequence[Any]|Mapping[str, Any] = {}) -> list[tuple[Any, ...]]:
        """
        Run the given SQL, returning all rows.
        """
        with self.conn.cursor() as cur:
            with self.conn.transaction():
                cur.execute(sql, params)
                return cur.fetchall()

    def getconn(self) -> psycopg.Connection:
        """
        Get the underlying psycopg connection.
        """
        return self.conn
