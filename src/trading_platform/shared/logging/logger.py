import logging
from logging.config import dictConfig
import yaml

def configure(path):
    with open(path,"r",encoding="utf-8") as f:
        dictConfig(yaml.safe_load(f))
    return logging.getLogger("trading_platform")
