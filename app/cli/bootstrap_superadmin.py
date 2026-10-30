import logging

from app.core.config import settings
from app.core.database import get_session_factory
from app.core.logging import configure_logging
from app.modules.usuarios.services.user_service import bootstrap_superadmin


def main() -> None:
    configure_logging(settings.log_level)
    logger = logging.getLogger("researchhub.bootstrap")
    with get_session_factory()() as db:
        result = bootstrap_superadmin(db, settings)
    logger.info("superadmin_bootstrap_%s", result)


if __name__ == "__main__":
    main()
