import logging


def init_log(level=logging.DEBUG):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=log_format)
