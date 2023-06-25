import logging
import reactivex as rx
from reactivex import operators as ops


def logger_factory(
    logger_name: str,
    filename: str,
    log_level=logging.INFO,
    log_format: str = "%(asctime)s -- %(levelname)s | %(message)s",
    date_format="%Y-%m-%d %H:%M:%S",
):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    handler = logging.FileHandler(filename)

    formatter = logging.Formatter(log_format, datefmt=date_format)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def handle_errors_observable(
    observable: rx.Observable, nb_retry: int, logger=logging
) -> rx.Observable:
    def catch_error(e, observable):
        logger.error(f"Observable stopped after {nb_retry} try.")

        return rx.empty()

    observable = observable.pipe(
        ops.do_action(
            on_error=lambda e: logger.warning(f"Observable got following error : {e}")
        ),
        ops.retry(nb_retry),
        ops.catch(handler=catch_error),
    )

    return observable
