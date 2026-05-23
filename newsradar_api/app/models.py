from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

# Tablas de asociación
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
)

alert_rss_channels = Table(
    "alert_rss_channels",
    Base.metadata,
    Column("alert_id", Integer, ForeignKey("alerts.id", ondelete="CASCADE")),
    Column(
        "rss_channel_id", Integer, ForeignKey("rss_channels.id", ondelete="CASCADE")
    ),
)


class User(Base):
    """Usuario del sistema con roles (admin, gestor, lector)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    organization = Column(String(180), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

    @property
    def role_ids(self):
        return [role.id for role in self.roles]


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", secondary=user_roles, back_populates="roles")


class Category(Base):
    """Categoría IPTC Media Topics de primer nivel"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(60), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    source = Column(String(20), default="IPTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rss_channels = relationship("RSSChannel", back_populates="category")
    news_items = relationship("NewsItem", back_populates="category")


class InformationSource(Base):
    __tablename__ = "information_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rss_channels = relationship(
        "RSSChannel", back_populates="information_source", cascade="all, delete-orphan"
    )


class RSSChannel(Base):
    """Canal RSS de un medio de comunicación asociado a una categoría"""
    __tablename__ = "rss_channels"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    information_source_id = Column(
        Integer, ForeignKey("information_sources.id", ondelete="CASCADE")
    )
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    information_source = relationship(
        "InformationSource", back_populates="rss_channels"
    )
    category = relationship("Category", back_populates="rss_channels")
    alerts = relationship(
        "Alert", secondary=alert_rss_channels, back_populates="rss_channels"
    )
    news_items = relationship("NewsItem", back_populates="rss_channel")


class Alert(Base):
    """Alerta de monitorización con palabras clave, categoría IPTC y expresión cron"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    keywords = Column(JSON, nullable=False)  # List of keywords
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    category_code = Column(String(60), nullable=True)
    cron_expression = Column(String(120), default="0 */6 * * *")  # Every 6 hours
    is_active = Column(Boolean, default=True)
    notify_email = Column(Boolean, default=True)
    notify_inbox = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="alerts")
    rss_channels = relationship(
        "RSSChannel", secondary=alert_rss_channels, back_populates="alerts"
    )
    notifications = relationship(
        "Notification", back_populates="alert", cascade="all, delete-orphan"
    )
    matched_news = relationship("NewsItem", back_populates="alert")


class NewsItem(Base):
    """Noticia capturada de un canal RSS que coincide con una alerta"""
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    rss_channel_id = Column(Integer, ForeignKey("rss_channels.id", ondelete="CASCADE"))
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    alert_id = Column(
        Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True
    )
    matched_keywords = Column(JSON, nullable=True)  # Keywords that matched
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rss_channel = relationship("RSSChannel", back_populates="news_items")
    category = relationship("Category", back_populates="news_items")
    alert = relationship("Alert", back_populates="matched_news")


class Notification(Base):
    """Notificación generada cuando una alerta detecta noticias relevantes"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"))
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    statistics = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    sent_email = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert", back_populates="notifications")


class ProcessingStats(Base):
    __tablename__ = "processing_stats"

    id = Column(Integer, primary_key=True, index=True)
    metrics = Column(JSON, nullable=True)
    total_feeds_processed = Column(Integer, default=0)
    total_feeds_failed = Column(Integer, default=0)
    total_news_items = Column(Integer, default=0)
    total_alerts_triggered = Column(Integer, default=0)
    processing_time_seconds = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
