import os
import sys
import logging
from .person_detection_model import *
from django.conf import settings

CURR_DIR = os.path.dirname(__file__)
logger = logging.getLogger(__name__)

try:
    person_detector = PersonDetection(
        os.path.join(CURR_DIR, "object_detect", "MobileNetSSD_deploy.prototxt.txt"),
        os.path.join(CURR_DIR, "object_detect", "MobileNetSSD_deploy.caffemodel"),
        settings.CONFIG,
        0.35,
    )
except Exception as e:
    logger.exception("importing PersonDetection files : {}".format(e))
