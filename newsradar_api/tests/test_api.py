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


# ==================== TESTS PARCHE PROFE (28/04/2026) ====================
# El profe pidió añadir rss_channels_ids e information_sources_ids al API
# en AlertBase y AlertUpdate.

def _bootstrap_manager_with_roles():
    """Crea rol manager + usuario manager verificado y devuelve (user_id, token)."""
    from app import models  # import local para evitar ciclos
    db = TestingSessionLocal()
    try:
        manager_role = models.Role(name="manager")
        db.add(manager_role)
        db.commit()
        db.refresh(manager_role)
        manager_role_id = manager_role.id
    finally:
        db.close()

    r = client.post("/api/v1/auth/register", json={
        "email": "patchmgr@example.com",
        "first_name": "Patch", "last_name": "Mgr",
        "organization": "UC3M", "password": "pass123",
        "role_ids": [manager_role_id]
    })
    assert r.status_code == 201, r.text
    user_id = r.json()["id"]

    # El usuario nace con is_verified=False; require_manager exige verificación.
    db = TestingSessionLocal()
    try:
        u = db.query(models.User).filter(models.User.id == user_id).first()
        u.is_verified = True
        db.commit()
    finally:
        db.close()

    token = client.post("/api/v1/auth/login",
        data={"username": "patchmgr@example.com", "password": "pass123"}
    ).json()["access_token"]
    return user_id, token


def test_alertbase_schema_has_new_fields():
    """Parche profe: AlertBase debe exponer rss_channels_ids e information_sources_ids."""
    from app.schemas import AlertBase, AlertUpdate
    base_fields = AlertBase.model_fields
    update_fields = AlertUpdate.model_fields
    assert "rss_channels_ids" in base_fields
    assert "information_sources_ids" in base_fields
    assert "rss_channels_ids" in update_fields
    assert "information_sources_ids" in update_fields


def test_create_alert_with_new_fields_returns_them():
    """Parche profe: crear alerta enviando los nuevos campos y verlos en la respuesta."""
    user_id, token = _bootstrap_manager_with_roles()

    payload = {
        "name": "Alerta parche",
        "descriptors": ["python", "fastapi"],
        "categories": [],
        "rss_channels_ids": [],          # campo nuevo profe
        "information_sources_ids": [],   # campo nuevo profe
        "cron_expression": "0 */6 * * *"
    }
    r = client.post(
        f"/api/v1/users/{user_id}/alerts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "rss_channels_ids" in body
    assert "information_sources_ids" in body
    assert body["rss_channels_ids"] == []
    assert body["information_sources_ids"] == []


def test_update_alert_with_new_fields_does_not_break():
    """Parche profe: PUT con los nuevos campos no debe romper el endpoint."""
    user_id, token = _bootstrap_manager_with_roles()

    # Crear alerta inicial
    create_payload = {
        "name": "Alerta a actualizar",
        "descriptors": ["test"],
        "categories": [],
        "rss_channels_ids": [],
        "information_sources_ids": [],
        "cron_expression": "0 */6 * * *"
    }
    r = client.post(
        f"/api/v1/users/{user_id}/alerts",
        json=create_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 201, r.text
    alert_id = r.json()["id"]

    # PUT incluyendo los nuevos campos vacíos
    update_payload = {
        "name": "Alerta renombrada",
        "rss_channels_ids": [],
        "information_sources_ids": []
    }
    r = client.put(
        f"/api/v1/users/{user_id}/alerts/{alert_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Alerta renombrada"
    assert body["rss_channels_ids"] == []
    assert body["information_sources_ids"] == []


def test_alert_response_uses_strings_for_new_id_fields():
    """Parche profe: tipo declarado es List[str], la respuesta debe ser strings."""
    user_id, token = _bootstrap_manager_with_roles()

    payload = {
        "name": "Alerta tipos",
        "descriptors": [],
        "categories": [],
        "rss_channels_ids": [],
        "information_sources_ids": [],
        "cron_expression": "0 */6 * * *"
    }
    r = client.post(
        f"/api/v1/users/{user_id}/alerts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 201, r.text
    body = r.json()
    # Las listas son vacías, pero el tipado del schema fuerza List[str].
    assert isinstance(body["rss_channels_ids"], list)
    assert isinstance(body["information_sources_ids"], list)
    # Si en algún momento hubiera elementos, comprobamos que serían str
    for x in body["rss_channels_ids"]:
        assert isinstance(x, str)
    for x in body["information_sources_ids"]:
        assert isinstance(x, str)