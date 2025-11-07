"""Utilidades para ejecutar operaciones en segundo plano y sincronizar con Tkinter."""

from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Optional

_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def get_executor(max_workers: int = 8) -> concurrent.futures.ThreadPoolExecutor:
    """Devuelve un ejecutor compartido para operaciones de red."""

    global _executor
    if _executor is None:
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="heartguard")
    return _executor


def run_in_executor(func: Callable[..., Any], *args: Any, **kwargs: Any) -> concurrent.futures.Future:
    """Ejecuta ``func`` en el ejecutor de background y retorna el ``Future``."""

    executor = get_executor()
    return executor.submit(func, *args, **kwargs)
