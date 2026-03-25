from sqlalchemy.orm import Session
from app import models
from app.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)


def init_roles(db: Session):
    """Initialize default roles"""
    roles_data = [
        {"name": "admin"},
        {"name": "manager"},
        {"name": "reader"}
    ]
    
    for role_data in roles_data:
        existing = db.query(models.Role).filter(models.Role.name == role_data["name"]).first()
        if not existing:
            role = models.Role(**role_data)
            db.add(role)
            logger.info(f"Created role: {role_data['name']}")
    
    db.commit()


def init_categories(db: Session):
    """Initialize IPTC Media Topics first-level categories"""
    categories_data = [
        {"code": "01000000", "name": "arts, culture and entertainment", "source": "IPTC"},
        {"code": "02000000", "name": "crime, law and justice", "source": "IPTC"},
        {"code": "03000000", "name": "disaster and accident", "source": "IPTC"},
        {"code": "04000000", "name": "economy, business and finance", "source": "IPTC"},
        {"code": "05000000", "name": "education", "source": "IPTC"},
        {"code": "06000000", "name": "environment", "source": "IPTC"},
        {"code": "07000000", "name": "health", "source": "IPTC"},
        {"code": "08000000", "name": "human interest", "source": "IPTC"},
        {"code": "09000000", "name": "labour", "source": "IPTC"},
        {"code": "10000000", "name": "lifestyle and leisure", "source": "IPTC"},
        {"code": "11000000", "name": "politics", "source": "IPTC"},
        {"code": "12000000", "name": "religion and belief", "source": "IPTC"},
        {"code": "13000000", "name": "science and technology", "source": "IPTC"},
        {"code": "14000000", "name": "society", "source": "IPTC"},
        {"code": "15000000", "name": "sport", "source": "IPTC"},
        {"code": "16000000", "name": "unrest, conflicts and war", "source": "IPTC"},
        {"code": "17000000", "name": "weather", "source": "IPTC"},
    ]
    
    for cat_data in categories_data:
        existing = db.query(models.Category).filter(models.Category.code == cat_data["code"]).first()
        if not existing:
            category = models.Category(**cat_data)
            db.add(category)
            logger.info(f"Created category: {cat_data['name']}")
    
    db.commit()



def init_admin_user(db: Session):
    """Initialize admin user"""
    admin_email = "admin@newsradar.com"
    existing = db.query(models.User).filter(models.User.email == admin_email).first()
    
    if not existing:
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        
        # Use a simple password that works with bcrypt
        simple_password = "admin123"
        
        admin_user = models.User(
            email=admin_email,
            first_name="Admin",
            last_name="NewsRadar",
            organization="NewsRadar",
            hashed_password=get_password_hash(simple_password),
            is_active=True,
            is_verified=True
        )
        
        if admin_role:
            admin_user.roles.append(admin_role)
        
        db.add(admin_user)
        db.commit()
        logger.info(f"Created admin user: {admin_email}")
    else:
        logger.info(f"Admin user already exists: {admin_email}")


def init_sample_sources(db: Session):
    """Initialize sample RSS sources"""
    sources_data = [
        {
            "name": "RTVE",
            "url": "https://www.rtve.es",
            "channels": [
                {"url": "https://www.rtve.es/api/noticias.rss", "category_code": "11000000"}
            ]
        },
        {
            "name": "El País",
            "url": "https://elpais.com",
            "channels": [
                {"url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "category_code": "11000000"}
            ]
        }
    ]
    
    for source_data in sources_data:
        existing = db.query(models.InformationSource).filter(
            models.InformationSource.name == source_data["name"]
        ).first()
        
        if not existing:
            source = models.InformationSource(
                name=source_data["name"],
                url=source_data["url"]
            )
            db.add(source)
            db.flush()
            
            for channel_data in source_data["channels"]:
                category = db.query(models.Category).filter(
                    models.Category.code == channel_data["category_code"]
                ).first()
                
                if category:
                    channel = models.RSSChannel(
                        url=channel_data["url"],
                        information_source_id=source.id,
                        category_id=category.id,
                        is_active=True
                    )
                    db.add(channel)
            
            logger.info(f"Created source: {source_data['name']}")
    
    db.commit()


def initialize_database(db: Session):
    """Initialize database with seed data"""
    logger.info("Initializing database...")
    init_roles(db)
    init_categories(db)
    init_admin_user(db)
    init_sample_sources(db)
    logger.info("Database initialization complete")
