import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ==================== TESTS UNITARIOS ====================

def test_health_check():
    """Test unitario: health endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ==================== TESTS FUNCIONALES ====================

def test_register_user():
    """Test funcional: registro de usuario"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser123@example.com",
            "first_name": "Test",
            "last_name": "User",
            "organization": "Test Org",
            "password": "testpass123",
            "role_ids": []
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser123@example.com"
    assert "id" in data


def test_login_form():
    """Test funcional: login con form data (OAuth2)"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "first_name": "Login",
            "last_name": "Test",
            "organization": "Test",
            "password": "password123",
            "role_ids": []
        }
    )
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_json():
    """Test funcional: login con JSON"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginjson@example.com",
            "first_name": "Login",
            "last_name": "Json",
            "organization": "Test",
            "password": "password123",
            "role_ids": []
        }
    )
    response = client.post(
        "/api/v1/auth/login-json",
        json={
            "email": "loginjson@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_credentials():
    """Test funcional: login con credenciales incorrectas"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_list_categories_unauthorized():
    """Test funcional: acceso sin token devuelve 401"""
    response = client.get("/api/v1/categories")
    assert response.status_code == 401


def test_list_categories_authorized():
    """Test: listar categorías con token"""
    client.post("/api/v1/auth/register", json={
        "email": "cat@example.com",
        "first_name": "Cat", "last_name": "User",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/login",
        data={"username": "cat@example.com", "password": "pass123"})
    token = response.json()["access_token"]

    response = client.get("/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_users_authorized():
    """Test: listar usuarios con token"""
    client.post("/api/v1/auth/register", json={
        "email": "users@example.com",
        "first_name": "Users", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/login",
        data={"username": "users@example.com", "password": "pass123"})
    token = response.json()["access_token"]

    response = client.get("/api/v1/users",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_list_sources_authorized():
    """Test: listar fuentes con token"""
    client.post("/api/v1/auth/register", json={
        "email": "sources@example.com",
        "first_name": "Sources", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/login",
        data={"username": "sources@example.com", "password": "pass123"})
    token = response.json()["access_token"]

    response = client.get("/api/v1/information-sources",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_dashboard_stats():
    """Test: estadísticas del dashboard"""
    client.post("/api/v1/auth/register", json={
        "email": "dash@example.com",
        "first_name": "Dash", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/login",
        data={"username": "dash@example.com", "password": "pass123"})
    token = response.json()["access_token"]

    response = client.get("/api/v1/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_get_current_user():
    """Test: obtener usuario actual"""
    client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "first_name": "Me", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/login",
        data={"username": "me@example.com", "password": "pass123"})
    token = response.json()["access_token"]

    response = client.get("/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_list_news_authorized():
    """Test: listar noticias con token"""
    client.post("/api/v1/auth/register", json={
        "email": "news@example.com",
        "first_name": "News", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/login",
        data={"username": "news@example.com", "password": "pass123"})
    token = response.json()["access_token"]

    response = client.get("/api/v1/news",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_get_user_by_id():
    """Test: obtener usuario por id"""
    r = client.post("/api/v1/auth/register", json={
        "email": "getuser@example.com",
        "first_name": "Get", "last_name": "User",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    user_id = r.json()["id"]
    token = client.post("/api/v1/auth/login",
        data={"username": "getuser@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get(f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "getuser@example.com"


def test_get_user_not_found():
    """Test: usuario no encontrado"""
    client.post("/api/v1/auth/register", json={
        "email": "notfound@example.com",
        "first_name": "Not", "last_name": "Found",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "notfound@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/users/99999",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_list_roles():
    """Test: listar roles"""
    client.post("/api/v1/auth/register", json={
        "email": "roles@example.com",
        "first_name": "Roles", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "roles@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/roles",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_alerts_unauthorized():
    """Test: listar alertas sin token"""
    response = client.get("/api/v1/users/1/alerts")
    assert response.status_code == 401


def test_get_synonyms():
    """Test: obtener sinónimos"""
    client.post("/api/v1/auth/register", json={
        "email": "syn@example.com",
        "first_name": "Syn", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "syn@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/synonyms?keyword=tecnologia",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "synonyms" in response.json()


def test_get_category_not_found():
    """Test: categoría no encontrada"""
    client.post("/api/v1/auth/register", json={
        "email": "catnotfound@example.com",
        "first_name": "Cat", "last_name": "NF",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "catnotfound@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/categories/99999",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_get_news_not_found():
    """Test: noticia no encontrada"""
    client.post("/api/v1/auth/register", json={
        "email": "newsnotfound@example.com",
        "first_name": "News", "last_name": "NF",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "newsnotfound@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/news/99999",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_source_not_found():
    """Test: fuente no encontrada"""
    client.post("/api/v1/auth/register", json={
        "email": "srcnotfound@example.com",
        "first_name": "Src", "last_name": "NF",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "srcnotfound@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/information-sources/99999",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

def test_update_user():
    """Test: actualizar usuario"""
    r = client.post("/api/v1/auth/register", json={
        "email": "update@example.com",
        "first_name": "Update", "last_name": "User",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    user_id = r.json()["id"]
    token = client.post("/api/v1/auth/login",
        data={"username": "update@example.com", "password": "pass123"}).json()["access_token"]

    response = client.put(f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "Updated"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"


def test_list_rss_channels_source_not_found():
    """Test: listar canales RSS de fuente inexistente"""
    client.post("/api/v1/auth/register", json={
        "email": "rss@example.com",
        "first_name": "RSS", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "rss@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/information-sources/99999/rss-channels",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_list_alerts_authorized():
    """Test: listar alertas de usuario autorizado"""
    r = client.post("/api/v1/auth/register", json={
        "email": "alerts@example.com",
        "first_name": "Alerts", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    user_id = r.json()["id"]
    token = client.post("/api/v1/auth/login",
        data={"username": "alerts@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get(f"/api/v1/users/{user_id}/alerts",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_register_duplicate_email():
    """Test: registro con email duplicado"""
    client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "first_name": "Dup", "last_name": "User",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    response = client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "first_name": "Dup", "last_name": "User",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    assert response.status_code == 400


def test_get_stats():
    """Test: obtener estadísticas"""
    client.post("/api/v1/auth/register", json={
        "email": "stats@example.com",
        "first_name": "Stats", "last_name": "Test",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "stats@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/stats",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_list_news_with_filters():
    """Test: listar noticias con filtros"""
    client.post("/api/v1/auth/register", json={
        "email": "newsfilter@example.com",
        "first_name": "News", "last_name": "Filter",
        "organization": "Test", "password": "pass123", "role_ids": []
    })
    token = client.post("/api/v1/auth/login",
        data={"username": "newsfilter@example.com", "password": "pass123"}).json()["access_token"]

    response = client.get("/api/v1/news?category_id=1&alert_id=1",
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200