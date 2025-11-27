"""Tests para el proxy de admin."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from gateway.app import create_app
from gateway.services.admin_client import AdminClientError


def test_admin_organizations_proxy_forwards_request():
    """Debe reenviar peticiones al admin service."""
    app = create_app()
    app.config.update(
        TESTING=True,
        ADMIN_SERVICE_URL="http://localhost:5002",
        GATEWAY_SERVICE_TIMEOUT=10,
    )

    with patch("gateway.routes.admin_proxy.AdminClient") as MockClient:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<response><organizations></organizations></response>'
        mock_response.headers = {"Content-Type": "application/xml"}
        mock_client.proxy_request.return_value = mock_response
        MockClient.return_value = mock_client

        with app.test_client() as client:
            response = client.get(
                "/admin/organizations/",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        assert mock_client.proxy_request.called
        call_kwargs = mock_client.proxy_request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["path"] == "/organizations/"


def test_admin_proxy_forwards_authorization_header():
    """Debe reenviar el header Authorization."""
    app = create_app()
    app.config.update(
        TESTING=True,
        ADMIN_SERVICE_URL="http://localhost:5002",
        GATEWAY_SERVICE_TIMEOUT=10,
    )

    with patch("gateway.routes.admin_proxy.AdminClient") as MockClient:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<response></response>'
        mock_response.headers = {}
        mock_client.proxy_request.return_value = mock_response
        MockClient.return_value = mock_client

        with app.test_client() as client:
            client.get(
                "/admin/organizations/",
                headers={"Authorization": "Bearer my-token-123"},
            )

        call_kwargs = mock_client.proxy_request.call_args[1]
        assert "headers" in call_kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer my-token-123"


def test_admin_proxy_handles_timeout():
    """Debe manejar timeouts del servicio."""
    app = create_app()
    app.config.update(
        TESTING=True,
        ADMIN_SERVICE_URL="http://localhost:5002",
        GATEWAY_SERVICE_TIMEOUT=10,
    )

    with patch("gateway.routes.admin_proxy.AdminClient") as MockClient:
        mock_client = MagicMock()
        mock_client.proxy_request.side_effect = AdminClientError(
            error="timeout",
            message="Timeout",
            status_code=504,
        )
        MockClient.return_value = mock_client

        with app.test_client() as client:
            response = client.get("/admin/organizations/")

        assert response.status_code == 504  # Gateway Timeout
        assert b"timeout" in response.data


def test_admin_proxy_handles_connection_error():
    """Debe manejar errores de conexión."""
    app = create_app()
    app.config.update(
        TESTING=True,
        ADMIN_SERVICE_URL="http://localhost:5002",
        GATEWAY_SERVICE_TIMEOUT=10,
    )

    with patch("gateway.routes.admin_proxy.AdminClient") as MockClient:
        mock_client = MagicMock()
        mock_client.proxy_request.side_effect = AdminClientError(
            error="service_unavailable",
            message="Service unavailable",
            status_code=503,
        )
        MockClient.return_value = mock_client

        with app.test_client() as client:
            response = client.get("/admin/organizations/")

        assert response.status_code == 503  # Service Unavailable
        assert b"service_unavailable" in response.data


def test_admin_proxy_forwards_post_json():
    """Debe reenviar POST requests con JSON."""
    app = create_app()
    app.config.update(
        TESTING=True,
        ADMIN_SERVICE_URL="http://localhost:5002",
        GATEWAY_SERVICE_TIMEOUT=10,
    )

    with patch("gateway.routes.admin_proxy.AdminClient") as MockClient:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.content = b'<response><id>123</id></response>'
        mock_response.headers = {"Content-Type": "application/xml"}
        mock_client.proxy_request.return_value = mock_response
        MockClient.return_value = mock_client

        with app.test_client() as client:
            response = client.post(
                "/admin/organizations/org-123/patients/",
                json={"name": "Test Patient"},
                headers={"Authorization": "Bearer token"},
            )

        assert response.status_code == 201
        call_kwargs = mock_client.proxy_request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["json"] == {"name": "Test Patient"}
