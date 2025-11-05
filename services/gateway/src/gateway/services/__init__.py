"""Clientes para interactuar con microservicios internos."""

from .admin_client import AdminClient, AdminClientError
from .auth_client import AuthClient, AuthClientError
from .patient_client import PatientClient, PatientClientError

__all__ = [
	"AdminClient",
	"AdminClientError",
	"AuthClient",
	"AuthClientError",
	"PatientClient",
	"PatientClientError",
]
