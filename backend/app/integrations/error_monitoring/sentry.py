import sentry_sdk

from app.core.config import settings


def configure_sentry():
    print("Sentry_dsn", settings.SENTRY_DSN)
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
    )
