#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
opasBasicLoginLib

This library is the very BASIC login form as demonstrated in the fastAPI docs

A more sophisticated one can be developed and then imported into the api app, instead of this one
  but using the same login endpoint for starters.  That way the level of login can be "chosen".

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0620.1"
__status__      = "Development"

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
import opasCentralDBLib

app = FastAPI()

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    ocd = opasCentralDBLib.opasCentralDB()
    userSession = ocd.authenticateUser(credentials.username, credentials.password)
    if userSession is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return userSession  # pydantic model based user.  See modelsOpasCentralPydantic.py

@app.get("/users/login")
def read_current_user(username: str = Depends(get_current_user)):
    return {"username": username}