"""Clientes para interactuar con microservicios internos."""

from .auth_client import AuthClient, AuthClientError

__all__ = ["AuthClient", "AuthClientError"]
