import os
import pathlib
from scrapy.utils.conf import closest_scrapy_cfg
from loguru import logger

format_ = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <7}</level> | ' \
          '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> --<level>{message}</level>'
proj_root = pathlib.Path(closest_scrapy_cfg()).parent
logger.add(os.path.join(proj_root, "sek.log"), rotation="500 MB", level="DEBUG", format=format_)
