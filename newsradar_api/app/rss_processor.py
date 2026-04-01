import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Set
from sqlalchemy.orm import Session
from app import models
from app.email_service import send_alert_notification

logger = logging.getLogger(__name__)


def fetch_rss_feed(url: str, timeout: int = 30) -> Dict:
    """Fetch and parse RSS feed"""
    try:
        feed = feedparser.parse(url)
        return feed
    except Exception as e:
        logger.error(f"Error fetching RSS feed {url}: {str(e)}")
        return None



def extract_news_items(feed: Dict) -> List[Dict]:
    """Extract news items from parsed feed"""
    items = []
    if not feed or not hasattr(feed, 'entries'):
        return items
    
    for entry in feed.entries:
        item = {
            'title': entry.get('title', ''),
            'link': entry.get('link', ''),
            'description': entry.get('description', ''),
            'published_date': None
        }
        
        # Parse published date
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                item['published_date'] = datetime(*entry.published_parsed[:6])
            except:
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



async def process_rss_channels(db: Session) -> Dict:
    """Process all active RSS channels and match against alerts"""
    stats = {
        'total_feeds_processed': 0,
        'total_feeds_failed': 0,
        'total_news_items': 0,
        'total_alerts_triggered': 0,
        'start_time': datetime.utcnow()
    }
    
    # Get all active RSS channels
    channels = db.query(models.RSSChannel).filter(models.RSSChannel.is_active == True).all()
    
    for channel in channels:
        try:
            # Fetch RSS feed
            feed = fetch_rss_feed(str(channel.url))
            if not feed:
                stats['total_feeds_failed'] += 1
                continue
            
            # Extract news items
            news_items = extract_news_items(feed)
            stats['total_news_items'] += len(news_items)
            
            # Process each news item
            for item_data in news_items:
                # Check if news item already exists
                existing = db.query(models.NewsItem).filter(
                    models.NewsItem.link == item_data['link']
                ).first()
                
                if existing:
                    continue
                
                # Create news item
                news_item = models.NewsItem(
                    title=item_data['title'],
                    link=item_data['link'],
                    description=item_data['description'],
                    published_date=item_data['published_date'],
                    rss_channel_id=channel.id,
                    category_id=channel.category_id
                )
                db.add(news_item)
                db.flush()
                
                # Match against alerts
                await match_news_against_alerts(db, news_item, item_data)
            
            # Update last fetched time
            channel.last_fetched = datetime.utcnow()
            stats['total_feeds_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing channel {channel.id}: {str(e)}")
            stats['total_feeds_failed'] += 1
    
    db.commit()
    
    # Calculate processing time
    end_time = datetime.utcnow()
    stats['processing_time_seconds'] = int((end_time - stats['start_time']).total_seconds())
    
    # Save processing stats
    processing_stats = models.ProcessingStats(
        total_feeds_processed=stats['total_feeds_processed'],
        total_feeds_failed=stats['total_feeds_failed'],
        total_news_items=stats['total_news_items'],
        total_alerts_triggered=stats['total_alerts_triggered'],
        processing_time_seconds=stats['processing_time_seconds']
    )
    db.add(processing_stats)
    db.commit()
    
    return stats



async def match_news_against_alerts(db: Session, news_item: models.NewsItem, item_data: Dict):
    """Match news item against active alerts"""
    # Get all active alerts
    alerts = db.query(models.Alert).filter(models.Alert.is_active == True).all()
    
    for alert in alerts:
        # Check if alert has specific RSS channels configured
        if alert.rss_channels:
            channel_ids = [ch.id for ch in alert.rss_channels]
            if news_item.rss_channel_id not in channel_ids:
                continue
        
        # Check if alert has category filter
        if alert.category_code and news_item.category_id:
            category = db.query(models.Category).filter(models.Category.id == news_item.category_id).first()
            if category and category.code != alert.category_code:
                continue
        
        # Match keywords
        text_to_search = f"{item_data['title']} {item_data['description']}"
        matched_keywords = match_keywords(text_to_search, alert.keywords)
        
        if matched_keywords:
            # Update news item with alert association
            news_item.alert_id = alert.id
            news_item.matched_keywords = matched_keywords
            
            # Create notification
            await create_alert_notification(db, alert, news_item, matched_keywords)


async def create_alert_notification(db: Session, alert: models.Alert, news_item: models.NewsItem, matched_keywords: List[str]):
    """Create notification for matched alert"""
    statistics = {
        'timestamp': datetime.utcnow().isoformat(),
        'news_count': 1,
        'matched_keywords': matched_keywords,
        'sources': [news_item.rss_channel.information_source.name]
    }
    
    # Create inbox notification
    if alert.notify_inbox:
        notification = models.Notification(
            alert_id=alert.id,
            title=f"Alert: {alert.name}",
            message=f"New news item matched: {news_item.title}",
            statistics=statistics,
            is_read=False,
            sent_email=False
        )
        db.add(notification)
    
    # Send email notification
    if alert.notify_email and alert.user.email:
        try:
            await send_alert_notification(
                alert.user.email,
                alert.name,
                statistics
            )
            if alert.notify_inbox:
                notification.sent_email = True
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    
    db.commit()
