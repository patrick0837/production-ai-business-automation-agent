import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(
            self,
            record: logging.LogRecord,
    ) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        context_fields = (
            "event",
            "request_id",
            "business_request_id",
            "agent_action_id",
            "celery_task_id",
            "attempt",
            "request_status",
            "countdown_seconds",
            "agent_status",
            "agent_action_count",
            "category",
            "priority",
            "intent",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "source",
        )

        for field in context_fields:
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                log_entry[field] = value

        if record.exc_info:
            log_entry["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            log_entry,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(
        log_level: str = "INFO",
) -> None:
    level = getattr(
        logging,
        log_level.upper(),
        logging.INFO,
    )

    handler = logging.StreamHandler(
        sys.stdout
    )
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)