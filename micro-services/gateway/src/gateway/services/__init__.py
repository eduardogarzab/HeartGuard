"""Clientes para interactuar con microservicios internos."""

from .admin_client import AdminClient, AdminClientError
from .auth_client import AuthClient, AuthClientError
from .media_client import MediaClient, MediaClientError
from .patient_client import PatientClient, PatientClientError
from .user_client import UserClient, UserClientError

__all__ = [
	"AdminClient",
	"AdminClientError",
	"AuthClient",
	"AuthClientError",
	"MediaClient",
	"MediaClientError",
	"PatientClient",
	"PatientClientError",
	"UserClient",
	"UserClientError",
]
