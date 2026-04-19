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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NewsRadar API",
    version="1.0.0",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS."
)

# CORS middleware
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
    """Initialize database on startup"""
    db = next(get_db())
    try:
        initialize_database(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
    finally:
        db.close()


# ==================== HEALTH & SYSTEM ====================

@app.get(f"{API_PREFIX}/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ==================== AUTHENTICATION ====================

@app.post(f"{API_PREFIX}/auth/register", response_model=schemas.User, status_code=201, tags=["auth"])
async def register(
    user_data: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user"""
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


@app.get(f"{API_PREFIX}/auth/verify", tags=["auth"])
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with token"""
    user = db.query(models.User).filter(models.User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if user.verification_token_expires and user.verification_token_expires.replace(tzinfo=None) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification token has expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return {"message": "Email verified successfully"}


@app.post(f"{API_PREFIX}/auth/login", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token (OAuth2 compatible)"""
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
    """Login with JSON body (alternative to OAuth2 form)"""
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


@app.get(f"{API_PREFIX}/auth/me", response_model=schemas.User, tags=["auth"])
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# ==================== ROLES ====================

@app.get(f"{API_PREFIX}/roles", response_model=List[schemas.Role], tags=["roles"])
def list_roles(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """List all roles"""
    return db.query(models.Role).all()


# ==================== USERS ====================

@app.get(f"{API_PREFIX}/users", response_model=List[schemas.User], tags=["users"])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all users"""
    return db.query(models.User).offset(skip).limit(limit).all()


@app.get(f"{API_PREFIX}/users/{{user_id}}", response_model=schemas.User, tags=["users"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user by ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ==================== CATEGORIES ====================

@app.get(f"{API_PREFIX}/categories", response_model=List[schemas.Category], tags=["categories"])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all IPTC categories"""
    return db.query(models.Category).all()


@app.get(f"{API_PREFIX}/categories/{{category_id}}", response_model=schemas.Category, tags=["categories"])
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get category by ID"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# ==================== INFORMATION SOURCES ====================

@app.get(f"{API_PREFIX}/information-sources", response_model=List[schemas.InformationSource], tags=["sources"])
def list_sources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all information sources"""
    return db.query(models.InformationSource).offset(skip).limit(limit).all()


@app.post(f"{API_PREFIX}/information-sources", response_model=schemas.InformationSource, status_code=201, tags=["sources"])
def create_source(
    source_data: schemas.InformationSourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    """Create a new information source (Manager only)"""
    data = source_data.model_dump()
    data["url"] = str(data["url"])
    source = models.InformationSource(**data)
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
    """Get information source by ID"""
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    return source


# ==================== RSS CHANNELS ====================

@app.get(f"{API_PREFIX}/information-sources/{{source_id}}/rss-channels", response_model=List[schemas.RSSChannel], tags=["rss-channels"])
def list_rss_channels(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List RSS channels for a source"""
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
    """Create RSS channel for a source (Manager only)"""
    source = db.query(models.InformationSource).filter(models.InformationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Information source not found")
    
    category = db.query(models.Category).filter(models.Category.id == channel_data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    data = channel_data.model_dump()
    data["url"] = str(data["url"])
    channel = models.RSSChannel(
        information_source_id=source_id,
        **data
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


# ==================== ALERTS ====================

@app.get(f"{API_PREFIX}/users/{{user_id}}/alerts", response_model=List[schemas.Alert], tags=["alerts"])
def list_user_alerts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List alerts for a user"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(models.Alert).filter(models.Alert.user_id == user_id).all()


@app.post(f"{API_PREFIX}/users/{{user_id}}/alerts", response_model=schemas.Alert, status_code=201, tags=["alerts"])
def create_alert(
    user_id: int,
    alert_data: schemas.AlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    """Create a new alert (Manager only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check max alerts limit
    alert_count = db.query(models.Alert).filter(models.Alert.user_id == user_id).count()
    if alert_count >= settings.MAX_ALERTS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.MAX_ALERTS_PER_USER} alerts per user")
    
    # Validate category_code if provided
    category_code = alert_data.category_code
    if category_code:
        valid = db.query(models.Category).filter(models.Category.code == category_code).first()
        if not valid:
            category_code = None

    alert = models.Alert(
        user_id=user_id,
        name=alert_data.name,
        keywords=alert_data.keywords,
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
    return alert


@app.get(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}", response_model=schemas.Alert, tags=["alerts"])
def get_alert(
    user_id: int,
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get alert by ID"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.put(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}", response_model=schemas.Alert, tags=["alerts"])
def update_alert(
    user_id: int,
    alert_id: int,
    alert_data: schemas.AlertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    """Update an alert (Manager only)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == user_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    update_data = alert_data.model_dump(exclude_unset=True)
    
    if "rss_channel_ids" in update_data:
        channel_ids = update_data.pop("rss_channel_ids")
        if channel_ids is not None:
            channels = db.query(models.RSSChannel).filter(models.RSSChannel.id.in_(channel_ids)).all()
            alert.rss_channels = channels
    
    for key, value in update_data.items():
        setattr(alert, key, value)
    
    db.commit()
    db.refresh(alert)
    return alert


@app.delete(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}", status_code=204, tags=["alerts"])
def delete_alert(
    user_id: int,
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    """Delete an alert (Manager only)"""
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


# ==================== NEWS ITEMS ====================

@app.get(f"{API_PREFIX}/news", response_model=List[schemas.NewsItem], tags=["news"])
def list_news(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    alert_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List news items with optional filters"""
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
    """Get news item by ID"""
    news = db.query(models.NewsItem).filter(models.NewsItem.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News item not found")
    return news


# ==================== NOTIFICATIONS ====================

@app.get(f"{API_PREFIX}/users/{{user_id}}/alerts/{{alert_id}}/notifications", response_model=List[schemas.Notification], tags=["notifications"])
def list_notifications(
    user_id: int,
    alert_id: int,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List notifications for an alert. Use unread_only=true to filter unread."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    query = db.query(models.Notification).filter(
        models.Notification.alert_id == alert_id
    )
    if unread_only:
        query = query.filter(models.Notification.is_read == False)

    return query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()


@app.patch(f"{API_PREFIX}/users/{{user_id}}/notifications/{{notification_id}}/read", response_model=schemas.Notification, tags=["notifications"])
def mark_notification_read(
    user_id: int,
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a notification as read"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


# ==================== SYNONYMS ====================

@app.get(f"{API_PREFIX}/synonyms", tags=["utilities"])
def get_keyword_synonyms(
    keyword: str = Query(..., description="Keyword to get synonyms for"),
    current_user: models.User = Depends(get_current_user)
):
    """Get synonym recommendations for a keyword"""
    synonyms = get_synonyms(keyword, settings.MIN_SYNONYMS, settings.MAX_SYNONYMS)
    return {
        "keyword": keyword,
        "synonyms": synonyms,
        "count": len(synonyms)
    }


# ==================== STATISTICS ====================

@app.get(f"{API_PREFIX}/stats", response_model=List[schemas.ProcessingStats], tags=["statistics"])
def get_processing_stats(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get processing statistics"""
    return db.query(models.ProcessingStats).order_by(
        models.ProcessingStats.created_at.desc()
    ).offset(skip).limit(limit).all()


@app.get(f"{API_PREFIX}/dashboard/stats", tags=["statistics"])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    total_sources = db.query(models.InformationSource).count()
    total_news = db.query(models.NewsItem).count()
    total_alerts = db.query(models.Alert).count()
    
    # News by category
    news_by_category = {}
    categories = db.query(models.Category).all()
    for cat in categories:
        count = db.query(models.NewsItem).filter(models.NewsItem.category_id == cat.id).count()
        if count > 0:
            news_by_category[cat.name] = count
    
    # Alerts by category
    alerts_by_category = {}
    for cat in categories:
        count = db.query(models.Alert).filter(models.Alert.category_code == cat.code).count()
        if count > 0:
            alerts_by_category[cat.name] = count
    
    return {
        "total_sources": total_sources,
        "total_news": total_news,
        "total_alerts": total_alerts,
        "news_by_category": news_by_category,
        "alerts_by_category": alerts_by_category
    }


# ==================== RSS PROCESSING ====================

@app.post(f"{API_PREFIX}/process-rss", tags=["utilities"])
async def trigger_rss_processing(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager)
):
    """Manually trigger RSS feed processing (Manager only)"""
    try:
        stats = await process_rss_channels(db)
        return {
            "status": "completed",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error processing RSS feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing RSS feeds: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
