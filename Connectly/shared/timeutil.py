"""Fechas: la base de datos trabaja en UTC y el navegador las muestra en la zona horaria de cada persona."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Ahora en UTC, sin tzinfo (coincide con las columnas DATETIME de MySQL, que guardan UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso_utc(value) -> str:
    """datetime naive en UTC -> '2026-11-03T22:10:00Z' (el 'Z' hace que JS lo convierta a hora local)."""
    if value is None:
        return ''
    return value.isoformat() + 'Z'
