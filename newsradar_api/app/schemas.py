from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator

# ==================== TOKEN ====================


class Token(BaseModel):
    """Token JWT de autenticación"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos extraídos del token JWT"""

    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Petición de login con email y contraseña"""

    email: EmailStr
    password: str


# ==================== METRIC (usado por Notification y Stats) ====================


class Metric(BaseModel):
    """Métrica con nombre y valor numérico"""

    name: str = Field(..., min_length=1, max_length=80)
    value: float


# ==================== ROLES ====================


class RoleBase(BaseModel):
    """Rol base (admin, gestor, lector)"""

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
    """Usuario base con datos personales"""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    organization: str = Field(..., min_length=1, max_length=180)
    telefono: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")


class UserCreate(UserBase):
    """Creación de usuario con contraseña y roles"""

    password: str = Field(..., min_length=6, max_length=128)
    role_ids: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(None, min_length=1, max_length=120)
    organization: Optional[str] = Field(None, min_length=1, max_length=180)
    telefono: Optional[str] = Field(None, min_length=9, max_length=9, pattern=r"^\d{9}$")
    role_ids: Optional[List[int]] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class User(UserBase):
    id: int
    role_ids: List[int] = Field(default_factory=list)
    roles: List[Role] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== CATEGORIES ====================


class CategoryBase(BaseModel):
    """Categoría IPTC Media Topics"""

    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(default="IPTC", pattern=r"^(IPTC|iptc|medtop:\d{8})$")


class CategoryCreate(CategoryBase):
    source: str = Field(..., pattern=r"^(IPTC|iptc|medtop:\d{8})$")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    source: Optional[str] = Field(None, pattern=r"^(IPTC|iptc|medtop:\d{8})$")


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# ==================== INFORMATION SOURCES ====================


class InformationSourceBase(BaseModel):
    """Medio de comunicación o fuente oficial"""

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
    """Canal RSS de un medio asociado a una categoría"""

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


class AlertCategoryItem(BaseModel):
    """Item de categoría IPTC para alertas"""

    code: str = Field(..., min_length=1, max_length=60)
    label: str = Field(..., min_length=1, max_length=120)


class AlertBase(BaseModel):
    """Alerta de monitorización con palabras clave y categoría"""

    name: str = Field(..., min_length=1, max_length=200)
    descriptors: List[str] = Field(default_factory=list)  # = keywords internamente
    categories: List[AlertCategoryItem] = Field(
        default_factory=list
    )  # = category_code internamente
    # Permitir asociar RSS y fuentes a la alerta
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
    cron_expression: str = Field(..., min_length=1, max_length=120)


class AlertCreate(AlertBase):
    # Campos extra que usamos internamente
    rss_channel_ids: List[int] = Field(default_factory=list)
    notify_email: bool = True
    notify_inbox: bool = True


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    descriptors: Optional[List[str]] = None
    categories: Optional[List[AlertCategoryItem]] = None
    # Permitir asociar RSS y fuentes a la alerta
    rss_channels_ids: List[str] = Field(default_factory=list)
    information_sources_ids: List[str] = Field(default_factory=list)
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
        """Convierte un Alert de BD al schema del enunciado"""
        cats = []
        if alert_orm.category_code:
            cats = [
                AlertCategoryItem(
                    code=alert_orm.category_code, label=alert_orm.category_code
                )
            ]
        # Poblamos rss_channels_ids e information_sources_ids
        # a partir de los canales RSS asociados (lista N-N en BD).
        rss_ids: List[str] = []
        info_src_ids: List[str] = []
        try:
            channels = list(alert_orm.rss_channels or [])
        except Exception:
            channels = []
        for ch in channels:
            if getattr(ch, "id", None) is not None:
                rss_ids.append(str(ch.id))
            if getattr(ch, "information_source_id", None) is not None:
                info_src_ids.append(str(ch.information_source_id))
        # Eliminamos duplicados de fuentes preservando el orden
        info_src_ids = list(dict.fromkeys(info_src_ids))
        return cls(
            id=alert_orm.id,
            user_id=alert_orm.user_id,
            name=alert_orm.name,
            descriptors=alert_orm.keywords or [],
            categories=cats,
            rss_channels_ids=rss_ids,
            information_sources_ids=info_src_ids,
            cron_expression=alert_orm.cron_expression or "0 */6 * * *",
        )


# ==================== NOTIFICATIONS ====================


class NotificationBase(BaseModel):
    """Notificación generada por una alerta con métricas"""

    timestamp: datetime
    metrics: List[Metric] = Field(default_factory=list)


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    metrics: Optional[List[Metric]] = None
    is_read: Optional[bool] = None


class Notification(NotificationBase):
    id: int
    alert_id: int
    is_read: bool = False
    sent_email: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_notification(cls, notif_orm):
        """Convierte una Notification de BD al schema del enunciado"""
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
            is_read=bool(getattr(notif_orm, "is_read", False)),
            sent_email=bool(getattr(notif_orm, "sent_email", False)),
        )


# ==================== STATS ====================


class StatsBase(BaseModel):
    """Estadísticas de procesamiento con métricas"""

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
        """Convierte ProcessingStats de BD al schema del enunciado"""
        if getattr(stats_orm, "metrics", None):
            return cls(
                id=stats_orm.id,
                metrics=[
                    Metric(name=str(item["name"]), value=float(item["value"]))
                    for item in stats_orm.metrics
                ],
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


# ==================== SCHEMAS INTERNOS (no expuestos en el enunciado) ====================


class NewsItemBase(BaseModel):
    """Noticia capturada de un canal RSS"""

    title: str
    link: str
    description: Optional[str] = None
    published_date: Optional[datetime] = None


class NewsItem(NewsItemBase):
    """Noticia completa con relaciones a canal, categoría y alerta"""

    id: int
    rss_channel_id: int
    category_id: Optional[int] = None
    alert_id: Optional[int] = None
    matched_keywords: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("matched_keywords", mode="before")
    @classmethod
    def normalize_matched_keywords(cls, value):
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [value]
        return [str(value)]


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
    """Estadísticas globales del dashboard"""

    total_sources: int
    total_news: int
    total_alerts: int
    news_by_category: dict
    alerts_by_category: dict


class SynonymRecommendation(BaseModel):
    """Recomendación de sinónimos para una palabra clave"""

    keyword: str
    synonyms: List[str]
