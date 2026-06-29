
from logging.config import dictConfig
import yaml

def configure_logging(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    dictConfig(cfg)
