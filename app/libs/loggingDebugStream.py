#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

# A simple logger to go to the display under some debugging conditions as well as the log.
import logging
logger = logging.getLogger(__name__)

def log_everywhere_if(condition, level, msg):
    if condition:
        print (msg)

    if level == "debug":
        logger.debug(msg)
    elif level == "info":
        logger.info(msg)
    elif level == "warning":
        logger.warning(msg)
    elif level == "error":
        logger.error(msg)
    elif level == "fatal":
        logger.fatal(msg)
            
        
    