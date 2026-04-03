from __future__ import annotations
import json, logging, sys
from typing import Any, Dict

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Include extra keys if provided
        for k, v in getattr(record, "__dict__", {}).items():
            if k not in payload and k not in ("args", "msg", "name", "levelno", "levelname",
                                              "pathname", "filename", "module", "exc_info",
                                              "exc_text", "stack_info", "lineno", "funcName",
                                              "created", "msecs", "relativeCreated", "thread",
                                              "threadName", "processName", "process"):
                payload[k] = v
        return json.dumps(payload, ensure_ascii=False)

def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
