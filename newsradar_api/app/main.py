from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import logging

from app.database import engine, get_db, Base
from app import models, schemas
from app.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_active_user, require_manager
)
from app.email_service import send_verification_email
from app.synonym_service import get_synonyms, expand_keywords
from app.rss_processor import process_rss_channels
from app.init_db import initialize_database
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NewsRadar API",
    version="1.0.0",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"


@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    try:
        initialize_database(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
    finally:
        db.close()


# ==================== HEALTH ====================

@app.get(f"{API_PREFIX}/health", tags=["system"])
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ==================== AUTH ====================

@app.post(f"{API_PREFIX}/auth/login", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login OAuth2 form (compatible con el profe)"""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(f"{API_PREFIX}/auth/login-json", response_model=schemas.Token, tags=["auth"])
def login_json(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login con JSON body"""
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(f"{API_PREFIX}/auth/register", response_model=schemas.User, status_code=201, tags=["auth"])
async def register(
    user_data: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    verification_token = secrets.token_urlsafe(32)
    user = models.User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        organization=user_data.organization,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=datetime.utcnow() + timedelta(hours=24)
    )

    if user_data.role_ids:
        roles = db.query(models.Role).filter(models.Role.id.in_(user_data.role_ids)).all()
        user.roles.extend(roles)

    db.add(user)
    db.commit()
    db.refresh(user)
    background_tasks.add_task(send_verification_email, user.email, verification_token)
    return user


@app.get(f"{API_PREFIX}/auth/me", response_model=schemas.User, tags=["auth"])
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    return current_user


# ==================== USERS ====================

@app.get(f"{API_PREFIX}/users", response_model=List[schemas.User], tags=["users"])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.User).offset(skip).limit(limit).all()


@app.post(f"{API_PREFIX}/users", response_model=schemas.User, status_code=201, tags=["users"])
async def create_user(
    user_data: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    """Create user (Manager only) - mismo comportamiento que register"""
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    verification_token = secrets.token_urlsafe(32)
    user = models.User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        organization=user_data.organization,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=datetime.utcnow() + timedelta(hours=24)
    )
    if user_data.role_ids:
        roles = db.query(models.Role).filter(models.Role.id.in_(user_data.role_ids)).all()
        user.roles.extend(roles)

    db.add(user)
    db.commit()
    db.refresh(user)
    background_tasks.add_task(send_verification_email, user.email, verification_token)
    return user


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=schemas.User, tags=["users"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put(f"{API_PREFIX}/users/{{user_id}}", response_model=schemas.User, tags=["users"])
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@app.delete(f"{API_PREFIX}/users/{{user_id}}", status_code=204, tags=["users"])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


# ==================== ROLES ====================

@app.get(f"{API_PREFIX}/roles", response_model=List[schemas.Role], tags=["roles"])
def list_roles(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Role).all()


@app.post(f"{API_PREFIX}/roles", response_model=schemas.Role, status_code=201, tags=["roles"])
def create_role(
    role_data: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    existing = db.query(models.Role).filter(models.Role.name == role_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
    role = models.Role(name=role_data.name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@app.get(f"{API_PREFIX}/roles/{{role_id}}", response_model=schemas.Role, tags=["roles"])
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@app.put(f"{API_PREFIX}/roles/{{role_id}}", response_model=schemas.Role, tags=["roles"])
def update_role(
    role_id: int,
    role_data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role_data.name:
        role.name = role_data.name
    db.commit()
    db.refresh(role)
    return role


@app.delete(f"{API_PREFIX}/roles/{{role_id}}", status_code=204, tags=["roles"])
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()


# ==================== ALERTS ====================
# NOTA: mapeamos descriptors<->keywords y categories<->category_code

@app.get(f"{API_PREFIX}/users/{{user_id}}/alerts", response_model=List[schemas.Alert], tags=["alerts"])
def list_user_alerts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    alerts_orm = db.query(models.Alert).filter(models.Alert.user_id == user_id).all()
    return [schemas.Alert.from_orm_alert(a) for a in alerts_orm]


@app.post(f"{API_PREFIX}/users/{{user_id}}/alerts", response_model=schemas.Alert, status_code=201, tags=["alerts"])
def create_alert(
    user_id: int,
    alert_data: schemas.AlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    alert_count = db.query(models.Alert).filter(models.Alert.user_id == user_id).count()
    if alert_count >= settings.MAX_ALERTS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.MAX_ALERTS_PER_USER} alerts per user")

    # Mapear descriptors -> keywords, categories -> category_code
    category_code = alert_data.categories[0].code if alert_data.categories else None

    alert = models.Alert(
        user_id=user_id,
        name=alert_data.name,
        keywords=alert_data.descriptors,
        category_code=category_code,
        cron_expression=alert_data.cron_expression,
        notify_email=alert_data.notify_email,
        notify_inbox=alert_data.notify_inbox
    )

    if alert_data.rss_channel_ids:
        channels = db.query(models.RSSChannel).filter(models.RSSChannel.id.in_(alert_data.rss_channel_ids)).all()
        alert.rss_channels.extend(channels)

    db.add(alert)
    db.commit()
    db.refresh(alert)
    return schemas.Alert.from_orm_alert(alert)


@app.get(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}", response_model=schemas.Alert, tags=["alerts"])
def get_alert(
    user_id: int,
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return schemas.Alert.from_orm_alert(alert)


@app.put(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}", response_model=schemas.Alert, tags=["alerts"])
def update_alert(
    user_id: int,
    alert_id: int,
    alert_data: schemas.AlertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_data = alert_data.model_dump(exclude_unset=True)

    # Mapear campos del profe a campos internos
    if "descriptors" in update_data:
        alert.keywords = update_data.pop("descriptors")
    if "categories" in update_data:
        cats = update_data.pop("categories")
        alert.category_code = cats[0]["code"] if cats else None
    if "rss_channel_ids" in update_data:
        channel_ids = update_data.pop("rss_channel_ids")
        if channel_ids is not None:
            channels = db.query(models.RSSChannel).filter(models.RSSChannel.id.in_(channel_ids)).all()
            alert.rss_channels = channels

    for key, value in update_data.items():
        setattr(alert, key, value)

    db.commit()
    db.refresh(alert)
    return schemas.Alert.from_orm_alert(alert)


@app.delete(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}", status_code=204, tags=["alerts"])
def delete_alert(
    user_id: int,
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()


# ==================== NOTIFICATIONS ====================
# NOTA: mapeamos title/message/statistics -> timestamp/metrics

@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=List[schemas.Notification],
    tags=["notifications"]
)
def list_notifications(
    user_id: int,
    alert_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    notifications = db.query(models.Notification).filter(
        models.Notification.alert_id == alert_id
    ).order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()
    return [schemas.Notification.from_orm_notification(n) for n in notifications]


@app.post(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications",
    response_model=schemas.Notification,
    status_code=201,
    tags=["notifications"]
)
def create_notification(
    user_id: int,
    alert_id: int,
    notif_data: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == user_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Mapear timestamp/metrics -> title/message/statistics
    stats_dict = {m.name: m.value for m in notif_data.metrics} if notif_data.metrics else {}
    notif = models.Notification(
        alert_id=alert_id,
        title=f"Actualización en {notif_data.timestamp.strftime('%d/%m/%Y %H:%M')}",
        message=f"Notificación generada el {notif_data.timestamp.isoformat()}",
        statistics=stats_dict
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return schemas.Notification.from_orm_notification(notif)


@app.get(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    response_model=schemas.Notification,
    tags=["notifications"]
)
def get_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.alert_id == alert_id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return schemas.Notification.from_orm_notification(notif)


@app.put(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    response_model=schemas.Notification,
    tags=["notifications"]
)
def update_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    notif_data: schemas.NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.alert_id == alert_id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notif_data.metrics is not None:
        notif.statistics = {m.name: m.value for m in notif_data.metrics}
    if notif_data.timestamp is not None:
        notif.title = f"Actualización en {notif_data.timestamp.strftime('%d/%m/%Y %H:%M')}"

    db.commit()
    db.refresh(notif)
    return schemas.Notification.from_orm_notification(notif)


@app.delete(
    f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications/{{notification_id}}",
    status_code=204,
    tags=["notifications"]
)
def delete_notification(
    user_id: int,
    alert_id: int,
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.alert_id == alert_id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()


# ==================== CATEGORIES ====================

@app.get(f"{API_PREFIX}/categories", response_model=List[schemas.Category], tags=["categories"])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Category).all()


@app.post(f"{API_PREFIX}/categories", response_model=schemas.Category, status_code=201, tags=["categories"])
def create_category(
    cat_data: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    # El profe no manda 'code', lo generamos desde el nombre si no viene
    code = cat_data.code if cat_data.code else cat_data.name.upper().replace(" ", "_")[:60]
    existing = db.query(models.Category).filter(models.Category.code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = models.Category(name=cat_data.name, source=cat_data.source, code=code)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@app.get(f"{API_PREFIX}/categories/{{category_id}}", response_model=schemas.Category, tags=["categories"])
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@app.put(f"{API_PREFIX}/categories/{{category_id}}", response_model=schemas.Category, tags=["categories"])
def update_category(
    category_id: int,
    cat_data: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    update_data = cat_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return cat


@app.delete(f"{API_PREFIX}/categories/{{category_id}}", status_code=204, tags=["categories"])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()


# ==================== INFORMATION SOURCES ====================

@app.get(f"{API_PREFIX}/information-sources", response_model=List[schemas.InformationSource], tags=["sources"])
def list_sources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.InformationSource).offset(skip).limit(limit).all()


@app.post(f"{API_PREFIX}/information-sources", response_model=schemas.InformationSource, status_code=201, tags=["sources"])
def create_source(
    source_data: schemas.InformationSourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    source = models.InformationSource(**source_data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.get(f"{API_PREFIX}/information-sources/{{source_id}}", response_model=schemas.InformationSource, tags=["sources"])
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    return source


@app.put(f"{API_PREFIX}/information-sources/{{source_id}}", response_model=schemas.InformationSource, tags=["sources"])
def update_source(
    source_id: int,
    source_data: schemas.InformationSourceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    update_data = source_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


@app.delete(f"{API_PREFIX}/information-sources/{{source_id}}", status_code=204, tags=["sources"])
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    db.delete(source)
    db.commit()


# ==================== RSS CHANNELS ====================

@app.get(f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels", response_model=List[schemas.RSSChannel], tags=["rss-channels"])
def list_rss_channels(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    return db.query(models.RSSChannel).filter(models.RSSChannel.information_source_id == source_id).all()


@app.post(f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels", response_model=schemas.RSSChannel, status_code=201, tags=["rss-channels"])
def create_rss_channel(
    source_id: int,
    channel_data: schemas.RSSChannelCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    category = db.query(models.Category).filter(models.Category.id == channel_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    channel = models.RSSChannel(information_source_id=source_id, **channel_data.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@app.get(f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}", response_model=schemas.RSSChannel, tags=["rss-channels"])
def get_rss_channel(
    source_id: int,
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    channel = db.query(models.RSSChannel).filter(
        models.RSSChannel.id == channel_id,
        models.RSSChannel.information_source_id == source_id
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="RSS channel not found")
    return channel


@app.put(f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}", response_model=schemas.RSSChannel, tags=["rss-channels"])
def update_rss_channel(
    source_id: int,
    channel_id: int,
    channel_data: schemas.RSSChannelUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    channel = db.query(models.RSSChannel).filter(
        models.RSSChannel.id == channel_id,
        models.RSSChannel.information_source_id == source_id
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="RSS channel not found")
    update_data = channel_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)
    db.commit()
    db.refresh(channel)
    return channel


@app.delete(f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels/{{channel_id}}", status_code=204, tags=["rss-channels"])
def delete_rss_channel(
    source_id: int,
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    channel = db.query(models.RSSChannel).filter(
        models.RSSChannel.id == channel_id,
        models.RSSChannel.information_source_id == source_id
    ).first()
    if not channel:
        raise HTTPException(status_code=404, detail="RSS channel not found")
    db.delete(channel)
    db.commit()


# ==================== STATS ====================
# NOTA: el profe usa metrics: List[Metric], mapeamos desde ProcessingStats interno

@app.get(f"{API_PREFIX}/stats", response_model=List[schemas.Stats], tags=["stats"])
def get_stats(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    stats_orm = db.query(models.ProcessingStats).order_by(
        models.ProcessingStats.created_at.desc()
    ).offset(skip).limit(limit).all()
    return [schemas.Stats.from_orm_stats(s) for s in stats_orm]


@app.post(f"{API_PREFIX}/stats", response_model=schemas.Stats, status_code=201, tags=["stats"])
def create_stats(
    stats_data: schemas.StatsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    # Mapear metrics -> campos individuales
    metrics_dict = {m.name: m.value for m in stats_data.metrics}
    stats = models.ProcessingStats(
        total_feeds_processed=int(metrics_dict.get("total_feeds_processed", 0)),
        total_feeds_failed=int(metrics_dict.get("total_feeds_failed", 0)),
        total_news_items=int(metrics_dict.get("total_news_items", 0)),
        total_alerts_triggered=int(metrics_dict.get("total_alerts_triggered", 0)),
        processing_time_seconds=int(metrics_dict.get("processing_time_seconds", 0)),
    )
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return schemas.Stats.from_orm_stats(stats)


@app.get(f"{API_PREFIX}/stats/{{stats_id}}", response_model=schemas.Stats, tags=["stats"])
def get_stats_by_id(
    stats_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    s = db.query(models.ProcessingStats).filter(models.ProcessingStats.id == stats_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Stats not found")
    return schemas.Stats.from_orm_stats(s)


@app.put(f"{API_PREFIX}/stats/{{stats_id}}", response_model=schemas.Stats, tags=["stats"])
def update_stats(
    stats_id: int,
    stats_data: schemas.StatsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    s = db.query(models.ProcessingStats).filter(models.ProcessingStats.id == stats_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Stats not found")
    if stats_data.metrics:
        metrics_dict = {m.name: m.value for m in stats_data.metrics}
        s.total_feeds_processed = int(metrics_dict.get("total_feeds_processed", s.total_feeds_processed))
        s.total_feeds_failed = int(metrics_dict.get("total_feeds_failed", s.total_feeds_failed))
        s.total_news_items = int(metrics_dict.get("total_news_items", s.total_news_items))
        s.total_alerts_triggered = int(metrics_dict.get("total_alerts_triggered", s.total_alerts_triggered))
        s.processing_time_seconds = int(metrics_dict.get("processing_time_seconds", s.processing_time_seconds))
    db.commit()
    db.refresh(s)
    return schemas.Stats.from_orm_stats(s)


@app.delete(f"{API_PREFIX}/stats/{{stats_id}}", status_code=204, tags=["stats"])
def delete_stats(
    stats_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    s = db.query(models.ProcessingStats).filter(models.ProcessingStats.id == stats_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Stats not found")
    db.delete(s)
    db.commit()


# ==================== EXTRAS (no son del profe pero los conservamos) ====================

@app.get(f"{API_PREFIX}/news", response_model=List[schemas.NewsItem], tags=["news"])
def list_news(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    alert_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.NewsItem)
    if category_id:
        query = query.filter(models.NewsItem.category_id == category_id)
    if alert_id:
        query = query.filter(models.NewsItem.alert_id == alert_id)
    return query.order_by(models.NewsItem.created_at.desc()).offset(skip).limit(limit).all()


@app.get(f"{API_PREFIX}/news/{{news_id}}", response_model=schemas.NewsItem, tags=["news"])
def get_news_item(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    news = db.query(models.NewsItem).filter(models.NewsItem.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News item not found")
    return news


@app.get(f"{API_PREFIX}/synonyms", tags=["utilities"])
def get_keyword_synonyms(
    keyword: str = Query(..., description="Keyword to get synonyms for"),
    current_user: models.User = Depends(get_current_user)
):
    synonyms = get_synonyms(keyword, settings.MIN_SYNONYMS, settings.MAX_SYNONYMS)
    return {"keyword": keyword, "synonyms": synonyms, "count": len(synonyms)}


@app.get(f"{API_PREFIX}/dashboard/stats", tags=["statistics"])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    total_sources = db.query(models.InformationSource).count()
    total_news = db.query(models.NewsItem).count()
    total_alerts = db.query(models.Alert).count()
    news_by_category = {}
    alerts_by_category = {}
    categories = db.query(models.Category).all()
    for cat in categories:
        count = db.query(models.NewsItem).filter(models.NewsItem.category_id == cat.id).count()
        if count > 0:
            news_by_category[cat.name] = count
        count2 = db.query(models.Alert).filter(models.Alert.category_code == cat.code).count()
        if count2 > 0:
            alerts_by_category[cat.name] = count2
    return {
        "total_sources": total_sources,
        "total_news": total_news,
        "total_alerts": total_alerts,
        "news_by_category": news_by_category,
        "alerts_by_category": alerts_by_category
    }


@app.post(f"{API_PREFIX}/process-rss", tags=["utilities"])
async def trigger_rss_processing(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    try:
        stats = await process_rss_channels(db)
        return {"status": "completed", "statistics": stats}
    except Exception as e:
        logger.error(f"Error processing RSS feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing RSS feeds: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
