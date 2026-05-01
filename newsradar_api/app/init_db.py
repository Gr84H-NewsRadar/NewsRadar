import logging

from sqlalchemy.orm import Session

from app import models
from app.auth import get_password_hash

logger = logging.getLogger(__name__)


def init_roles(db: Session):
    """Initialize default roles"""
    roles_data = [{"name": "admin"}, {"name": "manager"}, {"name": "reader"}]

    for role_data in roles_data:
        existing = (
            db.query(models.Role).filter(models.Role.name == role_data["name"]).first()
        )
        if not existing:
            role = models.Role(**role_data)
            db.add(role)
            logger.info("Created role: %s", role_data['name'])

    db.commit()


def init_categories(db: Session):
    """Initialize IPTC Media Topics first-level categories"""
    categories_data = [
        {
            "code": "01000000",
            "name": "arts, culture and entertainment",
            "source": "IPTC",
        },
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
        existing = (
            db.query(models.Category)
            .filter(models.Category.code == cat_data["code"])
            .first()
        )
        if not existing:
            category = models.Category(**cat_data)
            db.add(category)
            logger.info("Created category: %s", cat_data['name'])

    db.commit()


def init_admin_user(db: Session):
    """Initialize admin user"""
    admin_email = "admin@newsradar.com"
    existing = db.query(models.User).filter(models.User.email == admin_email).first()

    if not existing:
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()

        admin_user = models.User(
            email=admin_email,
            first_name="Admin",
            last_name="NewsRadar",
            organization="NewsRadar",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_verified=True,
        )

        if admin_role:
            admin_user.roles.append(admin_role)

        db.add(admin_user)
        db.commit()
        logger.info("Created admin user: %s", admin_email)
    else:
        logger.info("Admin user already exists: %s", admin_email)


def init_sample_sources(db: Session):
    """
    Initialize RSS sources with 100+ channels from 10+ different media sources,
    covering all 17 IPTC first-level categories as required by the project specification.
    """
    sources_data = [
        # ─────────────────────────────────────────
        # 1. RTVE (Radiotelevisión Española)
        # ─────────────────────────────────────────
        {
            "name": "RTVE",
            "url": "https://www.rtve.es",
            "channels": [
                {
                    "url": "https://www.rtve.es/api/noticias.rss",
                    "category_code": "11000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/economia.rss",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/sociedad.rss",
                    "category_code": "14000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/ciencia-tecnologia.rss",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/cultura.rss",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/deportes.rss",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/internacional.rss",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/salud.rss",
                    "category_code": "07000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/medio-ambiente.rss",
                    "category_code": "06000000",
                },
                {
                    "url": "https://www.rtve.es/api/noticias/sucesos.rss",
                    "category_code": "02000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 2. El País
        # ─────────────────────────────────────────
        {
            "name": "El País",
            "url": "https://elpais.com",
            "channels": [
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
                    "category_code": "11000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia",
                    "category_code": "04000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/sociedad",
                    "category_code": "14000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia",
                    "category_code": "13000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/cultura",
                    "category_code": "01000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/deportes",
                    "category_code": "15000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional",
                    "category_code": "16000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/salud",
                    "category_code": "07000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia",
                    "category_code": "13000000",
                },
                {
                    "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/clima",
                    "category_code": "06000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 3. ABC
        # ─────────────────────────────────────────
        {
            "name": "ABC",
            "url": "https://www.abc.es",
            "channels": [
                {
                    "url": "https://www.abc.es/rss/feeds/abc_EspanaEspana.xml",
                    "category_code": "11000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Economia.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Cultura.xml",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Deportes.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Internacional.xml",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Sociedad.xml",
                    "category_code": "14000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Ciencia.xml",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Tecnologia.xml",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Salud.xml",
                    "category_code": "07000000",
                },
                {
                    "url": "https://www.abc.es/rss/feeds/abc_Familia.xml",
                    "category_code": "10000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 4. El Confidencial
        # ─────────────────────────────────────────
        {
            "name": "El Confidencial",
            "url": "https://www.elconfidencial.com",
            "channels": [
                {
                    "url": "https://www.elconfidencial.com/rss/espana.xml",
                    "category_code": "11000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/economia.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/tecnologia.xml",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/deportes.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/cultura.xml",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/mundo.xml",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/sociedad.xml",
                    "category_code": "14000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/empresas.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/vivienda.xml",
                    "category_code": "10000000",
                },
                {
                    "url": "https://www.elconfidencial.com/rss/medioambiente.xml",
                    "category_code": "06000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 5. Marca
        # ─────────────────────────────────────────
        {
            "name": "Marca",
            "url": "https://www.marca.com",
            "channels": [
                {
                    "url": "https://www.marca.com/rss/portada.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/futbol.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/baloncesto.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/tenis.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/formula1.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/ciclismo.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/atletismo.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/otros-deportes.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/motor.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.marca.com/rss/polideportivo.xml",
                    "category_code": "15000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 6. Antena 3
        # ─────────────────────────────────────────
        {
            "name": "Antena 3",
            "url": "https://www.antena3.com",
            "channels": [
                {
                    "url": "https://www.antena3.com/rss/noticias.xml",
                    "category_code": "11000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/sociedad.xml",
                    "category_code": "14000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/economia.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/mundo.xml",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/sucesos.xml",
                    "category_code": "02000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/deportes.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.antena3.com/rss/series.xml",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.antena3.com/rss/cine.xml",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/gente.xml",
                    "category_code": "08000000",
                },
                {
                    "url": "https://www.antena3.com/rss/noticias/tiempo.xml",
                    "category_code": "17000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 7. El Diario
        # ─────────────────────────────────────────
        {
            "name": "El Diario",
            "url": "https://www.eldiario.es",
            "channels": [
                {"url": "https://www.eldiario.es/rss/", "category_code": "11000000"},
                {
                    "url": "https://www.eldiario.es/economia/rss/",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.eldiario.es/sociedad/rss/",
                    "category_code": "14000000",
                },
                {
                    "url": "https://www.eldiario.es/tecnologia/rss/",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.eldiario.es/cultura/rss/",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.eldiario.es/internacional/rss/",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.eldiario.es/salud/rss/",
                    "category_code": "07000000",
                },
                {
                    "url": "https://www.eldiario.es/medioambiente/rss/",
                    "category_code": "06000000",
                },
                {
                    "url": "https://www.eldiario.es/educacion/rss/",
                    "category_code": "05000000",
                },
                {
                    "url": "https://www.eldiario.es/desalambre/rss/",
                    "category_code": "08000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 8. La Moncloa (Gobierno de España)
        # ─────────────────────────────────────────
        {
            "name": "La Moncloa",
            "url": "https://www.lamoncloa.gob.es",
            "channels": [
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/presidencia/Paginas/rss.aspx",
                    "category_code": "11000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/hacienda/Paginas/rss.aspx",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/trabajo/Paginas/rss.aspx",
                    "category_code": "09000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/educacion/Paginas/rss.aspx",
                    "category_code": "05000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/sanidad/Paginas/rss.aspx",
                    "category_code": "07000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/ciencia/Paginas/rss.aspx",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/exteriores/Paginas/rss.aspx",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/transicion-ecologica/Paginas/rss.aspx",
                    "category_code": "06000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/cultura/Paginas/rss.aspx",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/interior/Paginas/rss.aspx",
                    "category_code": "02000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 9. 20 Minutos
        # ─────────────────────────────────────────
        {
            "name": "20 Minutos",
            "url": "https://www.20minutos.es",
            "channels": [
                {"url": "https://www.20minutos.es/rss/", "category_code": "11000000"},
                {
                    "url": "https://www.20minutos.es/rss/nacional/",
                    "category_code": "11000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/economia/",
                    "category_code": "04000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/deportes/",
                    "category_code": "15000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/tecnologia/",
                    "category_code": "13000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/sociedad/",
                    "category_code": "14000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/cultura/",
                    "category_code": "01000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/internacional/",
                    "category_code": "16000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/salud/",
                    "category_code": "07000000",
                },
                {
                    "url": "https://www.20minutos.es/rss/ciencia/",
                    "category_code": "13000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 10. Expansión
        # ─────────────────────────────────────────
        {
            "name": "Expansión",
            "url": "https://www.expansion.com",
            "channels": [
                {
                    "url": "https://e00-expansion.uecdn.es/rss/portada.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/empresas.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/mercados.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/economia.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/juridico.xml",
                    "category_code": "02000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/tecnologia.xml",
                    "category_code": "13000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/opinion.xml",
                    "category_code": "11000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/emprendedores.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/funcion-publica.xml",
                    "category_code": "09000000",
                },
                {
                    "url": "https://e00-expansion.uecdn.es/rss/accesible.xml",
                    "category_code": "14000000",
                },
            ],
        },
        # ─────────────────────────────────────────
        # 11. El Mundo (bonus para superar los 100)
        # ─────────────────────────────────────────
        {
            "name": "El Mundo",
            "url": "https://www.elmundo.es",
            "channels": [
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/portada.xml",
                    "category_code": "11000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/economia.xml",
                    "category_code": "04000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/deportes.xml",
                    "category_code": "15000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/cultura.xml",
                    "category_code": "01000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/ciencia.xml",
                    "category_code": "13000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/salud.xml",
                    "category_code": "07000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/internacional.xml",
                    "category_code": "16000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/sociedad.xml",
                    "category_code": "14000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/tecnologia.xml",
                    "category_code": "13000000",
                },
                {
                    "url": "https://e00-elmundo.uecdn.es/rss/espana.xml",
                    "category_code": "11000000",
                },
            ],
        },
    ]

    total_channels = 0
    for source_data in sources_data:
        existing = (
            db.query(models.InformationSource)
            .filter(models.InformationSource.name == source_data["name"])
            .first()
        )

        if not existing:
            source = models.InformationSource(
                name=source_data["name"], url=source_data["url"]
            )
            db.add(source)
            db.flush()

            for channel_data in source_data["channels"]:
                category = (
                    db.query(models.Category)
                    .filter(models.Category.code == channel_data["category_code"])
                    .first()
                )

                if category:
                    channel = models.RSSChannel(
                        url=channel_data["url"],
                        information_source_id=source.id,
                        category_id=category.id,
                        is_active=True,
                    )
                    db.add(channel)
                    total_channels += 1

            logger.info(
                f"Created source: {source_data['name']} with {len(source_data['channels'])} channels"
            )

    db.commit()
    logger.info(f"Total channels created: {total_channels}")


def initialize_database(db: Session):
    """Initialize database with seed data"""
    logger.info("Initializing database...")
    init_roles(db)
    init_categories(db)
    init_admin_user(db)
    init_sample_sources(db)
    logger.info("Database initialization complete")