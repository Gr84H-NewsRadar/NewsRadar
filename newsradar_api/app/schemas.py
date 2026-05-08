from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl

# ==================== TOKEN ====================


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ==================== METRIC (usado por Notification y Stats) ====================


class Metric(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    value: float


# ==================== ROLES ====================


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True


# ==================== USERS ====================


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization: str = Field(..., min_length=1, max_length=180)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    role_ids: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(None, min_length=1, max_length=120)
    organization: Optional[str] = Field(None, min_length=1, max_length=180)
    role_ids: Optional[List[int]] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class User(UserBase):
    id: int
    role_ids: List[int] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== CATEGORIES ====================


class CategoryBase(BaseModel):
    # El profe NO incluye 'code' en el schema externo, solo 'name' y 'source'
    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(default="IPTC", pattern="^IPTC$")


class CategoryCreate(CategoryBase):
    source: str = Field(..., pattern="^IPTC$")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    source: Optional[str] = Field(None, pattern="^IPTC$")


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# ==================== INFORMATION SOURCES ====================


class InformationSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl


class InformationSourceCreate(InformationSourceBase):
    pass


class InformationSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    url: Optional[HttpUrl] = None


class InformationSource(InformationSourceBase):
    id: int

    class Config:
        from_attributes = True


# ==================== RSS CHANNELS ====================


class RSSChannelBase(BaseModel):
    url: HttpUrl
    category_id: int


class RSSChannelCreate(RSSChannelBase):
    pass


class RSSChannelUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class RSSChannel(RSSChannelBase):
    id: int
    information_source_id: int

    class Config:
        from_attributes = True


# ==================== ALERTS ====================
# IMPORTANTE: el profe usa 'descriptors' (= keywords) y 'categories' (lista de objetos)


class AlertCategoryItem(BaseModel):
    code: str = Field(..., min_length=1, max_length=60)
    label: str = Field(..., min_length=1, max_length=120)


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    descriptors: List[str] = Field(default_factory=list)  # = keywords internamente
    categories: List[AlertCategoryItem] = Field(
        default_factory=list
    )  # = category_code internamente
    cron_expression: str = Field(..., min_length=1, max_length=120)


class AlertCreate(AlertBase):
    # Campos extra que usamos internamente pero el profe no define
    rss_channel_ids: List[int] = Field(default_factory=list)
    notify_email: bool = True
    notify_inbox: bool = True


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    descriptors: Optional[List[str]] = None
    categories: Optional[List[AlertCategoryItem]] = None
    cron_expression: Optional[str] = Field(None, min_length=1, max_length=120)
    is_active: Optional[bool] = None
    notify_email: Optional[bool] = None
    notify_inbox: Optional[bool] = None
    rss_channel_ids: Optional[List[int]] = None


class Alert(AlertBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

    # Mapeamos desde el modelo de BD (keywords -> descriptors, category_code -> categories)
    @classmethod
    def from_orm_alert(cls, alert_orm):
        """Convierte un Alert de BD al schema del profe"""
        cats = []
        if alert_orm.category_code:
            cats = [
                AlertCategoryItem(
                    code=alert_orm.category_code, label=alert_orm.category_code
                )
            ]
        return cls(
            id=alert_orm.id,
            user_id=alert_orm.user_id,
            name=alert_orm.name,
            descriptors=alert_orm.keywords or [],
            categories=cats,
            cron_expression=alert_orm.cron_expression or "0 */6 * * *",
        )


# ==================== NOTIFICATIONS ====================
# IMPORTANTE: el profe usa 'timestamp' y 'metrics: List[Metric]'


class NotificationBase(BaseModel):
    timestamp: datetime
    metrics: List[Metric] = Field(default_factory=list)


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    metrics: Optional[List[Metric]] = None


class Notification(NotificationBase):
    id: int
    alert_id: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_notification(cls, notif_orm):
        """Convierte una Notification de BD al schema del profe"""
        # Intentamos leer metrics del campo statistics si existe
        metrics = []
        if notif_orm.statistics and isinstance(notif_orm.statistics, dict):
            for k, v in notif_orm.statistics.items():
                try:
                    metrics.append(Metric(name=k, value=float(v)))
                except Exception:
                    pass
        return cls(
            id=notif_orm.id,
            alert_id=notif_orm.alert_id,
            timestamp=notif_orm.created_at,
            metrics=metrics,
        )


# ==================== STATS ====================
# IMPORTANTE: el profe usa 'metrics: List[Metric]'


class StatsBase(BaseModel):
    metrics: List[Metric] = Field(default_factory=list)


class StatsCreate(StatsBase):
    pass


class StatsUpdate(BaseModel):
    metrics: Optional[List[Metric]] = None


class Stats(StatsBase):
    id: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_stats(cls, stats_orm):
        """Convierte ProcessingStats de BD al schema del profe"""
        if getattr(stats_orm, "metrics", None):
            return cls(
                id=stats_orm.id,
                metrics=[Metric(name=str(item["name"]), value=float(item["value"])) for item in stats_orm.metrics],
            )
        metrics = [
            Metric(
                name="total_feeds_processed",
                value=float(stats_orm.total_feeds_processed or 0),
            ),
            Metric(
                name="total_feeds_failed",
                value=float(stats_orm.total_feeds_failed or 0),
            ),
            Metric(
                name="total_news_items", value=float(stats_orm.total_news_items or 0)
            ),
            Metric(
                name="total_alerts_triggered",
                value=float(stats_orm.total_alerts_triggered or 0),
            ),
            Metric(
                name="processing_time_seconds",
                value=float(stats_orm.processing_time_seconds or 0),
            ),
        ]
        return cls(id=stats_orm.id, metrics=metrics)


# ==================== SCHEMAS INTERNOS (no expuestos al profe) ====================


class NewsItemBase(BaseModel):
    title: str
    link: str
    description: Optional[str] = None
    published_date: Optional[datetime] = None


class NewsItem(NewsItemBase):
    id: int
    rss_channel_id: int
    category_id: Optional[int] = None
    alert_id: Optional[int] = None
    matched_keywords: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessingStats(BaseModel):
    id: int
    total_feeds_processed: int = 0
    total_feeds_failed: int = 0
    total_news_items: int = 0
    total_alerts_triggered: int = 0
    processing_time_seconds: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_sources: int
    total_news: int
    total_alerts: int
    news_by_category: dict
    alerts_by_category: dict


class SynonymRecommendation(BaseModel):
    keyword: str
    synonyms: List[str]
