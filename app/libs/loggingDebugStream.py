#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0321,C0103,C0301,E1101,C0303,E1004,C0330,R0915,R0914,W0703,C0326

# A simple logger to go to the display under some debugging conditions as well as the log.
import logging
logger = logging.getLogger(__name__)

def log_everywhere_if(condition, level, msg):
    if level == "debug":    
        logger.debug(msg)
        level_int = 10
    elif level == "info":
        logger.info(msg)
        level_int = 20
    elif level == "warning":
        logger.warning(msg)
        level_int = 30
    elif level == "error" or level == "severe":
        logger.error(msg)
        level_int = 40
    elif level == "fatal":
        logger.fatal(msg)
        level_int = 50
        
    if condition and (logger.parent.level <= level_int or level_int == 20): # want to see info msgs if condition
        print (msg)

    