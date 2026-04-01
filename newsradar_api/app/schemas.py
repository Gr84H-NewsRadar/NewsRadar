from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, HttpUrl


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# Role schemas
class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True


# User schemas
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
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    roles: List[Role] = []
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Category schemas
class CategoryBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=120)
    source: str = Field(default="IPTC")


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Information Source schemas
class InformationSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl


class InformationSourceCreate(InformationSourceBase):
    pass


class InformationSource(InformationSourceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# RSS Channel schemas
class RSSChannelBase(BaseModel):
    url: HttpUrl
    category_id: int


class RSSChannelCreate(RSSChannelBase):
    pass


class RSSChannel(RSSChannelBase):
    id: int
    information_source_id: int
    is_active: bool
    last_fetched: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Alert schemas
class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    keywords: List[str] = Field(..., min_items=1)
    category_code: Optional[str] = None
    cron_expression: str = Field(default="0 */6 * * *")
    notify_email: bool = True
    notify_inbox: bool = True


class AlertCreate(AlertBase):
    rss_channel_ids: List[int] = Field(default_factory=list)


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    keywords: Optional[List[str]] = None
    category_code: Optional[str] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    notify_email: Optional[bool] = None
    notify_inbox: Optional[bool] = None
    rss_channel_ids: Optional[List[int]] = None


class Alert(AlertBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# News Item schemas
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


# Notification schemas
class NotificationBase(BaseModel):
    title: str
    message: str
    statistics: Optional[dict] = None


class NotificationCreate(NotificationBase):
    alert_id: int


class Notification(NotificationBase):
    id: int
    alert_id: int
    is_read: bool
    sent_email: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Statistics schemas
class ProcessingStatsBase(BaseModel):
    total_feeds_processed: int = 0
    total_feeds_failed: int = 0
    total_news_items: int = 0
    total_alerts_triggered: int = 0
    processing_time_seconds: int = 0


class ProcessingStats(ProcessingStatsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard statistics
class DashboardStats(BaseModel):
    total_sources: int
    total_news: int
    total_alerts: int
    news_by_category: dict
    alerts_by_category: dict


# Synonym recommendation
class SynonymRecommendation(BaseModel):
    keyword: str
    synonyms: List[str]
