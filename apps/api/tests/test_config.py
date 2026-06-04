from sqlalchemy.engine import make_url

from app.core.config import Settings


def test_db_url_is_built_from_components_with_reserved_password_chars():
    settings = Settings(
        db_url=None,
        db_user="postgres",
        db_password="pa@@word",
        db_host="postgres",
        db_port=5432,
        db_name="photo_coach",
    )

    parsed = make_url(settings.db_url)

    assert parsed.username == "postgres"
    assert parsed.password == "pa@@word"
    assert parsed.host == "postgres"
    assert parsed.database == "photo_coach"
