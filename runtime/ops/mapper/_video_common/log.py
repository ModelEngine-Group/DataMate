# -*- coding: utf-8 -*-
import logging
import os

def get_logger(name: str, log_dir: str = None):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, "run.log"), encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger