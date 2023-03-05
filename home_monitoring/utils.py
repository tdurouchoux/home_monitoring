import logging


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
