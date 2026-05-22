import logging
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

import feedparser
from sqlalchemy.orm import Session

from app import models
from app.email_service import send_cycle_summary

logger = logging.getLogger(__name__)


def fetch_rss_feed(url: str, timeout: int = 30) -> Dict:
    """Fetch and parse RSS feed"""
    try:
        feed = feedparser.parse(url)
        return feed
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error fetching RSS feed %s: %s", url, str(e))
        return None


def extract_news_items(feed: Dict) -> List[Dict]:
    """Extract news items from parsed feed"""
    items = []
    if not feed or not hasattr(feed, "entries"):
        return items

    for entry in feed.entries:
        item = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "description": entry.get("description", ""),
            "published_date": None,
        }

        # Parse published date
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                item["published_date"] = datetime(*entry.published_parsed[:6])
            except Exception:
                pass

        items.append(item)

    return items


def match_keywords(text: str, keywords: List[str]) -> List[str]:
    """Check if any keywords match in text"""
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    return matched


async def process_rss_channels(db: Session, user_id: int | None = None) -> Dict:
    """Process all active RSS channels and match against alerts"""
    stats = {
        "total_feeds_processed": 0,
        "total_feeds_failed": 0,
        "total_news_items": 0,
        "total_alerts_triggered": 0,
        "start_time": datetime.utcnow(),
    }

    # Track matches per alert: {alert_id: {'alert': alert, 'matches': [news_item, ...]}}
    alert_matches = {}

    # User-triggered runs only process channels attached to that user's active
    # alerts, so notifications stay scoped to the account that started the run.
    channels_query = db.query(models.RSSChannel).filter(models.RSSChannel.is_active)
    if user_id is not None:
        user_alerts = (
            db.query(models.Alert)
            .filter(models.Alert.is_active, models.Alert.user_id == user_id)
            .all()
        )
        channel_ids = sorted(
            {
                channel.id
                for alert in user_alerts
                for channel in list(alert.rss_channels or [])
            }
        )
        if not channel_ids:
            stats["alert_summaries"] = []
            stats["processing_time_seconds"] = 0
            return stats
        channels_query = channels_query.filter(models.RSSChannel.id.in_(channel_ids))

    channels = channels_query.all()

    for channel in channels:
        try:
            # Fetch RSS feed
            feed = fetch_rss_feed(str(channel.url))
            if not feed:
                stats["total_feeds_failed"] += 1
                continue

            # Extract news items
            news_items = extract_news_items(feed)
            stats["total_news_items"] += len(news_items)

            # Process each news item
            for item_data in news_items:
                # Check if news item already exists
                existing = (
                    db.query(models.NewsItem)
                    .filter(models.NewsItem.link == item_data["link"])
                    .first()
                )

                if existing:
                    if existing.rss_channel_id is None:
                        existing.rss_channel_id = channel.id
                    if existing.category_id is None:
                        existing.category_id = channel.category_id
                    # Re-match existing items too, so repeated processing can still
                    # notify the current user's alert when the feed exposes known URLs.
                    if user_id is not None:
                        match_news_against_alerts(
                            db, existing, item_data, alert_matches, stats, user_id=user_id
                        )
                    elif existing.alert_id is None:
                        match_news_against_alerts(
                            db, existing, item_data, alert_matches, stats
                        )
                    continue

                # Create news item
                news_item = models.NewsItem(
                    title=item_data["title"],
                    link=item_data["link"],
                    description=item_data["description"],
                    published_date=item_data["published_date"],
                    rss_channel_id=channel.id,
                    category_id=channel.category_id,
                )
                db.add(news_item)
                db.flush()

                # Match against alerts
                match_news_against_alerts(
                    db, news_item, item_data, alert_matches, stats, user_id=user_id
                )

            # Update last fetched time
            channel.last_fetched = datetime.utcnow()
            stats["total_feeds_processed"] += 1

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error processing channel %s: %s", channel.id, str(e))
            stats["total_feeds_failed"] += 1

    db.commit()

    # Calculate processing time
    end_time = datetime.utcnow()
    stats["processing_time_seconds"] = int(
        (end_time - stats["start_time"]).total_seconds()
    )

    # Save processing stats
    processing_stats = models.ProcessingStats(
        total_feeds_processed=stats["total_feeds_processed"],
        total_feeds_failed=stats["total_feeds_failed"],
        total_news_items=stats["total_news_items"],
        total_alerts_triggered=stats["total_alerts_triggered"],
        processing_time_seconds=stats["processing_time_seconds"],
    )
    db.add(processing_stats)
    db.commit()

    stats["alert_summaries"] = [
        {
            "alert_id": data["alert"].id,
            "alert_name": data["alert"].name,
            "matches_count": len(data["matches"]),
            "sources": list(
                {
                    n.rss_channel.information_source.name
                    for n in data["matches"]
                    if n.rss_channel and n.rss_channel.information_source
                }
            ),
            "matched_keywords": list(
                {
                    kw
                    for n in data["matches"]
                    if n.matched_keywords
                    for kw in n.matched_keywords
                }
            ),
        }
        for data in alert_matches.values()
    ]

    # Send one summary notification per alert that had matches
    for _, data in alert_matches.items():
        await send_cycle_notification(db, data["alert"], data["matches"], stats)

    return stats


def match_news_against_alerts(
    db: Session,
    news_item: models.NewsItem,
    item_data: Dict,
    alert_matches: Dict,
    stats: Dict,
    user_id: int | None = None,
):
    """Match news item against active alerts and accumulate matches"""
    # Get all active alerts
    alerts_query = db.query(models.Alert).filter(models.Alert.is_active)
    if user_id is not None:
        alerts_query = alerts_query.filter(models.Alert.user_id == user_id)
    alerts = alerts_query.all()

    for alert in alerts:
        # Check if alert has specific RSS channels configured
        if alert.rss_channels:
            channel_ids = [ch.id for ch in alert.rss_channels]
            if news_item.rss_channel_id not in channel_ids:
                continue

        # Check if alert has category filter
        if alert.category_code and news_item.category_id:
            # Validate that category_code exists in the DB; skip filter if invalid
            valid_category = (
                db.query(models.Category)
                .filter(models.Category.code == alert.category_code)
                .first()
            )
            if not valid_category:
                logger.warning(
                    "Alert %s has invalid category_code '%s', ignoring category filter",
                    alert.id,
                    alert.category_code,
                )
            else:
                category = (
                    db.query(models.Category)
                    .filter(models.Category.id == news_item.category_id)
                    .first()
                )
                if category and category.code != alert.category_code:
                    continue

        # Match keywords
        text_to_search = f"{item_data['title']} {item_data['description']}"
        matched_keywords = match_keywords(text_to_search, alert.keywords)

        if matched_keywords:
            # Update news item with alert association
            news_item.alert_id = alert.id
            news_item.matched_keywords = matched_keywords
            stats["total_alerts_triggered"] += 1

            # Accumulate match for end-of-cycle summary
            if alert.id not in alert_matches:
                alert_matches[alert.id] = {"alert": alert, "matches": []}
            alert_matches[alert.id]["matches"].append(news_item)


async def send_cycle_notification(
    db: Session, alert: models.Alert, matched_news: List[models.NewsItem], stats: Dict
):
    """Create one summary notification per alert after the full processing cycle"""
    now = datetime.now(ZoneInfo("Europe/Madrid"))
    timestamp_display = now.strftime("%d/%m/%Y %H:%M:%S")

    # Collect unique sources from matched news
    sources = list(
        {
            n.rss_channel.information_source.name
            for n in matched_news
            if n.rss_channel and n.rss_channel.information_source
        }
    )

    statistics = {
        "timestamp": now.isoformat(),
        "news_processed": stats["total_news_items"],
        "matches_count": len(matched_news),
        "feeds_ok": stats["total_feeds_processed"],
        "feeds_ko": stats["total_feeds_failed"],
        "matched_keywords": list(
            {
                kw
                for n in matched_news
                if n.matched_keywords
                for kw in n.matched_keywords
            }
        ),
        "sources": sources,
    }

    # Create inbox notification
    if alert.notify_inbox:
        notification = models.Notification(
            alert_id=alert.id,
            title=f"Actualización de alerta: {alert.name}",
            message=f"{len(matched_news)} noticias coincidieron con la alerta",
            statistics=statistics,
            is_read=False,
            sent_email=False,
        )
        db.add(notification)

    # Send one summary email
    if alert.notify_email and alert.user.email:
        try:
            email_sent = await send_cycle_summary(
                to_email=alert.user.email,
                alert_name=alert.name,
                timestamp_display=timestamp_display,
                matched_news=matched_news,
                statistics=statistics,
            )
            if alert.notify_inbox and email_sent:
                notification.sent_email = True
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Failed to send summary email: %s", str(e))

    db.commit()
