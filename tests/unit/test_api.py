"""
Unit tests for API endpoints.

Run with: pytest tests/unit/test_api.py -v

Tests:
- Health endpoint
- API routes import correctly
- FastAPI app configuration
"""
import pytest
from fastapi.testclient import TestClient


class TestAPIImports:
    """Test API module imports."""

    def test_import_main_app(self):
        """
        TEST: Main FastAPI app imports successfully
        
        Expected: No import errors
        """
        print("\n🌐 Testing API app import...")
        from src.api.main import app
        
        assert app is not None
        print("✅ FastAPI app imported successfully")

    def test_import_routes(self):
        """
        TEST: All route modules import successfully
        
        Expected: No import errors
        """
        print("\n🌐 Testing route imports...")
        
        from src.api.routes.health import router as health_router
        from src.api.routes.voice import router as voice_router
        from src.api.routes.webhooks import router as webhooks_router
        
        assert health_router is not None
        assert voice_router is not None
        assert webhooks_router is not None
        
        print("   health router: ✓")
        print("   voice router: ✓")
        print("   webhooks router: ✓")
        print("✅ All routes imported successfully")


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.main import app
        return TestClient(app)

    def test_health_endpoint_exists(self, client):
        """
        TEST: Health endpoint responds
        
        Expected: 200 OK response
        """
        print("\n🌐 Testing health endpoint...")
        
        response = client.get("/health")
        
        assert response.status_code == 200
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("✅ Health endpoint working")

    def test_health_response_format(self, client):
        """
        TEST: Health response has correct format
        
        Expected: JSON with status field
        """
        print("\n🌐 Testing health response format...")
        
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        
        print(f"   Response data: {data}")
        print("✅ Health response format correct")


class TestAPIConfiguration:
    """Test API configuration."""

    def test_app_title(self):
        """
        TEST: App has correct title
        
        Expected: Title matches config
        """
        print("\n🌐 Testing app configuration...")
        from src.api.main import app
        
        assert app.title is not None
        print(f"   App title: {app.title}")
        print("✅ App title configured")

    def test_routes_registered(self):
        """
        TEST: All routes are registered
        
        Expected: Multiple routes in app
        """
        print("\n🌐 Testing route registration...")
        from src.api.main import app
        
        routes = [route.path for route in app.routes]
        
        assert len(routes) > 0
        assert "/health" in routes
        
        print(f"   Registered routes: {routes}")
        print("✅ Routes registered correctly")


class TestVoiceEndpoints:
    """Test voice API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.main import app
        return TestClient(app)

    def test_voice_routes_exist(self):
        """
        TEST: Voice routes are defined
        
        Expected: Voice router has routes
        """
        print("\n🌐 Testing voice routes...")
        from src.api.routes.voice import router
        
        routes = [route.path for route in router.routes]
        
        assert len(routes) > 0
        print(f"   Voice routes: {routes}")
        print("✅ Voice routes defined")


class TestWebhookEndpoints:
    """Test Twilio webhook endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.main import app
        return TestClient(app)

    def test_webhook_routes_exist(self):
        """
        TEST: Webhook routes are defined
        
        Expected: Webhook router has routes
        """
        print("\n🌐 Testing webhook routes...")
        from src.api.routes.webhooks import router
        
        routes = [route.path for route in router.routes]
        
        assert len(routes) > 0
        print(f"   Webhook routes: {routes}")
        print("✅ Webhook routes defined")


class TestOpenAPISchema:
    """Test OpenAPI schema generation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.api.main import app
        return TestClient(app)

    def test_openapi_schema(self, client):
        """
        TEST: OpenAPI schema is generated
        
        Expected: Valid OpenAPI JSON
        """
        print("\n🌐 Testing OpenAPI schema...")
        
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "openapi" in schema
        assert "paths" in schema
        
        print(f"   OpenAPI version: {schema.get('openapi')}")
        print(f"   Number of paths: {len(schema.get('paths', {}))}")
        print("✅ OpenAPI schema generated correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

