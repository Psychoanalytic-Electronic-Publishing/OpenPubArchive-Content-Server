import sys

sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import os.path
import time
import datetime
from datetime import datetime
import re
import wget
import io
import urllib.parse
import random

from urllib import parse

import uvicorn
from fastapi import FastAPI, Query, Body, Path, Header, Security, Depends, HTTPException, File #Form, UploadFile, Cookie
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, FileResponse, StreamingResponse # RedirectResponse
from starlette.middleware.cors import CORSMiddleware
import starlette.status as httpCodes
from typing import Union
import pandas as pd
import requests
from urllib import parse

import uvicorn
from fastapi import FastAPI, Query, Body, Path, Header, Security, Depends, HTTPException, File #Form, UploadFile, Cookie
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, FileResponse, StreamingResponse # RedirectResponse
from starlette.middleware.cors import CORSMiddleware
import starlette.status as httpCodes
from typing import Union
import pandas as pd
import requests

from requests.auth import HTTPBasicAuth

# TIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%SZ' # moved to opasConfig

from pydantic import ValidationError
import solrpy as solr # needed for extended search
import logging
logger = logging.getLogger(__name__)

import localsecrets
import opasConfig
import models
import opasCentralDBLib
import opasFileSupport
import opasGenSupportLib
import opasQueryHelper
import opasSchemaHelper
import opasDocPermissions
import opasSolrPyLib
import opasPySolrLib

print ("Hi there")