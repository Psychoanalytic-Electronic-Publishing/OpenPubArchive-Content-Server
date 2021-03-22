#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019-2021, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2021.0321.1"
__status__      = "Development"

"""
Opas Push DB settings to production
"""

import sys
import re
sys.path.append('../libs')
sys.path.append('../config')

import os.path
import time
import datetime
from datetime import datetime
TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ'

from pydantic import ValidationError
import solrpy as solr # needed for extended search
from config.opasConfig import OPASSESSIONID, OPASACCESSTOKEN, OPASEXPIRES
import config.opasConfig as opasConfig

import logging
logger = logging.getLogger(__name__)
import starlette.status as httpCodes

from errorMessages import *

import models
import opasCentralDBLib
import opasFileSupport
import opasQueryHelper
import opasSchemaHelper
import opasDocPermissions
import opasPySolrLib

