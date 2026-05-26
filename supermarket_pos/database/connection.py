# ============================================================
# database/connection.py — Singleton de conexión MySQL
# ============================================================
"""
Patrón Singleton garantiza una única instancia de conexión
durante toda la vida de la aplicación.
"""

from __future__ import annotations
import threading
import mysql.connector
from mysql.connector import Error, pooling
from config import DB_CONFIG


class DatabaseConnection:
    """
    Singleton thread-safe para la conexión a MySQL.
    Usa un pool de conexiones para mayor rendimiento.
    """
    _instance: DatabaseConnection | None = None
    _lock = threading.Lock()
    _pool: pooling.MySQLConnectionPool | None = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize_pool()
        return cls._instance

    # ----------------------------------------------------------
    def _initialize_pool(self) -> None:
        """Inicializa el pool de conexiones MySQL."""
        try:
            pool_config = {**DB_CONFIG, "pool_name": "dto2_pool", "pool_size": 5}
            self._pool = pooling.MySQLConnectionPool(**pool_config)
            print("[DB] Pool de conexiones MySQL inicializado correctamente.")
        except Error as e:
            print(f"[DB] ERROR al inicializar pool: {e}")
            self._pool = None

    # ----------------------------------------------------------
    def get_connection(self) -> mysql.connector.MySQLConnection:
        """Obtiene una conexión del pool."""
        if self._pool is None:
            raise RuntimeError(
                "No se pudo conectar a MySQL. Verifica config.py y que el servidor esté activo."
            )
        return self._pool.get_connection()

    # ----------------------------------------------------------
    def execute_query(
        self,
        query: str,
        params: tuple | None = None,
        fetch: bool = False,
        fetch_one: bool = False,
        commit: bool = False,
    ):
        """
        Ejecuta una consulta SQL de forma segura.

        Args:
            query     : Sentencia SQL con placeholders %s
            params    : Tupla de parámetros
            fetch     : True → fetchall()
            fetch_one : True → fetchone()
            commit    : True → confirma la transacción

        Returns:
            Lista de dicts, dict, lastrowid o None según el caso.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = None
            if fetch:
                result = cursor.fetchall()
            elif fetch_one:
                result = cursor.fetchone()
            elif commit:
                conn.commit()
                result = cursor.lastrowid
            return result
        except Error as e:
            conn.rollback()
            raise RuntimeError(f"Error en base de datos: {e}") from e
        finally:
            cursor.close()
            conn.close()

    # ----------------------------------------------------------
    def execute_transaction(self, operations: list[tuple]) -> bool:
        """
        Ejecuta múltiples operaciones en una sola transacción atómica.

        Args:
            operations: Lista de (query, params)

        Returns:
            True si todo fue exitoso.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            last_id = None
            for query, params in operations:
                cursor.execute(query, params or ())
                last_id = cursor.lastrowid
            conn.commit()
            return last_id
        except Error as e:
            conn.rollback()
            raise RuntimeError(f"Transacción fallida: {e}") from e
        finally:
            cursor.close()
            conn.close()

    # ----------------------------------------------------------
    def test_connection(self) -> bool:
        """Verifica si la conexión está activa."""
        try:
            conn = self.get_connection()
            conn.ping(reconnect=True)
            conn.close()
            return True
        except Exception:
            return False


# Acceso global
db = DatabaseConnection()
