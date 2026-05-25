from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import main as main_module, models
from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


_client_post = client.post


def _post_with_default_phone(url, *args, **kwargs):
    json_data = kwargs.get("json")
    if url in {"/api/v1/auth/register", "/api/v1/users"} and isinstance(json_data, dict):
        payload = dict(json_data)
        payload.setdefault("telefono", "123456789")
        kwargs["json"] = payload
    return _client_post(url, *args, **kwargs)


client.post = _post_with_default_phone


def _mark_user_verified(email: str):
    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email.lower()).first()
        assert user is not None
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()
    finally:
        db.close()


def _login_verified_user(email: str, password: str = "pass123") -> str:
    _mark_user_verified(email)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


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
            "role_ids": [],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser123@example.com"
    assert data["telefono"] == "123456789"
    assert "id" in data

    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter_by(email="newuser123@example.com").first()
        assert user is not None
        assert user.is_verified is False
    finally:
        db.close()


def test_register_user_rejects_invalid_phone_format():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "badphone@example.com",
            "first_name": "Bad",
            "last_name": "Phone",
            "organization": "Test Org",
            "telefono": "123",
            "password": "testpass123",
            "role_ids": [],
        },
    )
    assert response.status_code == 422


def test_unverified_user_cannot_login():
    """Un usuario recién registrado no puede iniciar sesión ni recibe JWT."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "pending@example.com",
            "first_name": "Pending",
            "last_name": "User",
            "organization": "Test Org",
            "password": "pass123",
            "role_ids": [],
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "pending@example.com", "password": "pass123"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "status": "error",
        "message": "Please verify your email before logging in",
    }
    assert "access_token" not in response.json()


def test_verify_email_with_valid_token_allows_login(monkeypatch):
    """Un token válido verifica la cuenta y habilita el login."""
    raw_token = "valid-verification-token"
    monkeypatch.setattr(main_module.secrets, "token_urlsafe", lambda size: raw_token)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "verify@example.com",
            "first_name": "Verify",
            "last_name": "User",
            "organization": "Test Org",
            "password": "pass123",
            "role_ids": [],
        },
    )

    response = client.get(f"/api/v1/auth/verify?token={raw_token}")
    assert response.status_code == 200
    assert response.json() == {
        "status": "verified",
        "message": "Email verified successfully",
    }

    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter_by(email="verify@example.com").first()
        assert user.is_verified is True
        assert user.verification_token is None
        assert user.verification_token_expires is None
    finally:
        db.close()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "verify@example.com", "password": "pass123"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_expired_verification_token_does_not_verify():
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "expired@example.com",
            "first_name": "Expired",
            "last_name": "User",
            "organization": "Test Org",
            "password": "pass123",
            "role_ids": [],
        },
    )
    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter_by(email="expired@example.com").first()
        user.verification_token = "expired-token"
        user.verification_token_expires = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/auth/verify?token=expired-token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Verification token expired"

    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter_by(email="expired@example.com").first()
        assert user.is_verified is False
    finally:
        db.close()


def test_invalid_verification_token_returns_error():
    response = client.get("/api/v1/auth/verify?token=does-not-exist")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification token"


def test_used_verification_token_cannot_be_reused(monkeypatch):
    raw_token = "single-use-token"
    monkeypatch.setattr(main_module.secrets, "token_urlsafe", lambda size: raw_token)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reuse@example.com",
            "first_name": "Reuse",
            "last_name": "User",
            "organization": "Test Org",
            "password": "pass123",
            "role_ids": [],
        },
    )

    first = client.get(f"/api/v1/auth/verify?token={raw_token}")
    second = client.get(f"/api/v1/auth/verify?token={raw_token}")
    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "Invalid verification token"


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
            "role_ids": [],
        },
    )
    _mark_user_verified("login@example.com")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "password123"},
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
            "role_ids": [],
        },
    )
    _mark_user_verified("loginjson@example.com")
    response = client.post(
        "/api/v1/auth/login-json",
        json={"email": "loginjson@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_credentials():
    """Test funcional: login con credenciales incorrectas"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_list_categories_unauthorized():
    """Test funcional: acceso sin token devuelve 401"""
    response = client.get("/api/v1/categories")
    assert response.status_code == 401


def test_list_categories_authorized():
    """Test: listar categorías con token"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "cat@example.com",
            "first_name": "Cat",
            "last_name": "User",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("cat@example.com")

    response = client.get(
        "/api/v1/categories", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_users_authorized():
    """Test: listar usuarios con token"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "users@example.com",
            "first_name": "Users",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("users@example.com")

    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_list_sources_authorized():
    """Test: listar fuentes con token"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "sources@example.com",
            "first_name": "Sources",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("sources@example.com")

    response = client.get(
        "/api/v1/information-sources", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_dashboard_stats():
    """Test: estadísticas del dashboard"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "dash@example.com",
            "first_name": "Dash",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("dash@example.com")

    response = client.get(
        "/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_get_current_user():
    """Test: obtener usuario actual"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "first_name": "Me",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("me@example.com")

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_list_news_authorized():
    """Test: listar noticias con token"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "news@example.com",
            "first_name": "News",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("news@example.com")

    response = client.get("/api/v1/news", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_get_user_by_id():
    """Test: obtener usuario por id"""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "getuser@example.com",
            "first_name": "Get",
            "last_name": "User",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    user_id = r.json()["id"]
    token = _login_verified_user("getuser@example.com")

    response = client.get(
        f"/api/v1/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "getuser@example.com"


def test_get_user_not_found():
    """Test: usuario no encontrado"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "notfound@example.com",
            "first_name": "Not",
            "last_name": "Found",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("notfound@example.com")

    response = client.get(
        "/api/v1/users/99999", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_list_roles():
    """Test: listar roles"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "roles@example.com",
            "first_name": "Roles",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("roles@example.com")

    response = client.get("/api/v1/roles", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_alerts_unauthorized():
    """Test: listar alertas sin token"""
    response = client.get("/api/v1/users/1/alerts")
    assert response.status_code == 401


def test_get_synonyms():
    """Test: obtener sinónimos"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "syn@example.com",
            "first_name": "Syn",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("syn@example.com")

    response = client.get(
        "/api/v1/synonyms?keyword=tecnologia",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "synonyms" in response.json()


def test_get_category_not_found():
    """Test: categoría no encontrada"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "catnotfound@example.com",
            "first_name": "Cat",
            "last_name": "NF",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("catnotfound@example.com")

    response = client.get(
        "/api/v1/categories/99999", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_get_news_not_found():
    """Test: noticia no encontrada"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "newsnotfound@example.com",
            "first_name": "News",
            "last_name": "NF",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("newsnotfound@example.com")

    response = client.get(
        "/api/v1/news/99999", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_source_not_found():
    """Test: fuente no encontrada"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "srcnotfound@example.com",
            "first_name": "Src",
            "last_name": "NF",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("srcnotfound@example.com")

    response = client.get(
        "/api/v1/information-sources/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_update_user():
    """Test: actualizar usuario"""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "update@example.com",
            "first_name": "Update",
            "last_name": "User",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    user_id = r.json()["id"]
    token = _login_verified_user("update@example.com")

    response = client.put(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"


def test_list_rss_channels_source_not_found():
    """Test: listar canales RSS de fuente inexistente"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "rss@example.com",
            "first_name": "RSS",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("rss@example.com")

    response = client.get(
        "/api/v1/information-sources/99999/rss-channels",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_list_alerts_authorized():
    """Test: listar alertas de usuario autorizado"""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alerts@example.com",
            "first_name": "Alerts",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    user_id = r.json()["id"]
    token = _login_verified_user("alerts@example.com")

    response = client.get(
        f"/api/v1/users/{user_id}/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_register_duplicate_email():
    """Test: registro con email duplicado"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    assert response.status_code == 400


def test_get_stats():
    """Test: obtener estadísticas"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "stats@example.com",
            "first_name": "Stats",
            "last_name": "Test",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("stats@example.com")

    response = client.get("/api/v1/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_list_news_with_filters():
    """Test: listar noticias con filtros"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "newsfilter@example.com",
            "first_name": "News",
            "last_name": "Filter",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("newsfilter@example.com")

    response = client.get(
        "/api/v1/news?category_id=1&alert_id=1",
        headers={"Authorization": f"Bearer {token}"},
    )
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

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "patchmgr@example.com",
            "first_name": "Patch",
            "last_name": "Mgr",
            "organization": "UC3M",
            "password": "pass123",
            "role_ids": [manager_role_id],
        },
    )
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

    token = client.post(
        "/api/v1/auth/login",
        data={"username": "patchmgr@example.com", "password": "pass123"},
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
        "rss_channels_ids": [],  # campo nuevo profe
        "information_sources_ids": [],  # campo nuevo profe
        "cron_expression": "0 */6 * * *",
    }
    r = client.post(
        f"/api/v1/users/{user_id}/alerts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
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
        "cron_expression": "0 */6 * * *",
    }
    r = client.post(
        f"/api/v1/users/{user_id}/alerts",
        json=create_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    alert_id = r.json()["id"]

    # PUT incluyendo los nuevos campos vacíos
    update_payload = {
        "name": "Alerta renombrada",
        "rss_channels_ids": [],
        "information_sources_ids": [],
    }
    r = client.put(
        f"/api/v1/users/{user_id}/alerts/{alert_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
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
        "cron_expression": "0 */6 * * *",
    }
    r = client.post(
        f"/api/v1/users/{user_id}/alerts",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
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


def test_synonym_service_expand_keywords():
    """Test: expandir múltiples keywords con sinónimos"""
    from app.synonym_service import expand_keywords

    result = expand_keywords(["tecnología", "salud"])
    assert isinstance(result, dict)
    assert "tecnología" in result or "salud" in result


def test_synonym_service_no_synonyms():
    """Test: keyword sin sinónimos devuelve lista vacía"""
    from app.synonym_service import get_synonyms

    result = get_synonyms("palabrainexistente123")
    assert result == []


def test_database_get_db_closes():
    """Test: get_db cierra la sesión correctamente"""
    from app.database import get_db

    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass  # Esperado: el generador cierra la sesión


def test_auth_get_current_active_user_not_verified():
    """Test: usuario no verificado no puede acceder"""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "notverified@example.com",
            "first_name": "Not",
            "last_name": "Verified",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    user_id = r.json()["id"]

    # Marcar como no verificado
    db = TestingSessionLocal()
    try:
        u = db.query(models.User).filter(models.User.id == user_id).first()
        u.is_verified = True
        db.commit()
    finally:
        db.close()

    token = client.post(
        "/api/v1/auth/login",
        data={"username": "notverified@example.com", "password": "pass123"},
    ).json()["access_token"]

    db = TestingSessionLocal()
    try:
        u = db.query(models.User).filter(models.User.id == user_id).first()
        u.is_verified = False
        db.commit()
    finally:
        db.close()

    # Intentar acceder a un endpoint que requiere verificación
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    # Debería funcionar porque get_current_user no requiere verificación
    assert response.status_code == 403
    assert response.json()["message"] == "Please verify your email before logging in"


def test_patch_user():
    """Test: actualizar usuario con PATCH"""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "patch@example.com",
            "first_name": "Patch",
            "last_name": "User",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    user_id = r.json()["id"]
    token = _login_verified_user("patch@example.com")

    response = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"organization": "Patched Org"},
    )
    assert response.status_code == 200
    assert response.json()["organization"] == "Patched Org"


def test_wordcloud_endpoint():
    """Test: endpoint de wordcloud"""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wordcloud@example.com",
            "first_name": "Word",
            "last_name": "Cloud",
            "organization": "Test",
            "password": "pass123",
            "role_ids": [],
        },
    )
    token = _login_verified_user("wordcloud@example.com")

    response = client.get(
        "/api/v1/dashboard/wordcloud", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
