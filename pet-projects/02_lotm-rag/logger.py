import inspect
import logging
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


class _ClassNameFilter(logging.Filter):
    """Injects `class_name` into each log record by inspecting the call stack."""

    def filter(self, record: logging.LogRecord) -> bool:
        class_name = ""
        frame = inspect.currentframe()
        try:
            while frame:
                caller = frame.f_locals.get("self") or frame.f_locals.get("cls")
                if caller and frame.f_code.co_name == record.funcName:
                    class_name = (
                        type(caller).__name__
                        if not isinstance(caller, type)
                        else caller.__name__
                    )
                    break
                frame = frame.f_back
        finally:
            del frame
        record.class_name = class_name
        return True


class _OptionalFormatter(logging.Formatter):
    """Renders class name and method name only when present."""

    def format(self, record: logging.LogRecord) -> str:
        class_name = getattr(record, "class_name", "")
        func_name = record.funcName

        if class_name and func_name:
            record.location = f".{class_name}.{func_name}"
        elif func_name:
            record.location = f".{func_name}"
        else:
            record.location = ""

        return super().format(record)


def get_logger(name: str = "lotm_rag") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    context_filter = _ClassNameFilter()
    formatter = _OptionalFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s%(location)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — DEBUG and above
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    logger.addHandler(file_handler)

    return logger
