#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpasCentral DB Pydantic Models


"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0620.1"
__status__      = "Development"

from datetime import datetime, timedelta
from pydantic import BaseModel

class User(BaseModel):  # snake_case names to match DB
    user_id: int = None
    username: str = None
    full_name: str = None
    email_address: str = None
    company: str = None
    modified_by_user_id: int = None
    enabled: bool = True
    admin: bool = False
    user_agrees_date: datetime = None
    user_agrees_to_tracking: bool = None
    user_agrees_to_cookies: bool = None
    added_date: datetime = None
    last_update: datetime = None

class UserInDB(User):
    password: str = None
  
class Session(BaseModel):
    api_session_id: int = None
    user_id: int = None
    authenticated: bool = False
    session_start: datetime = None
    session_end: datetime = None
    session_token: str = None
    session_expires_time: datetime = None
    api_client_id: int = None            
    
class Subscriptions(BaseModel):
    user_id: int = None
    subsystem_id: int = None
    product_id: int = None
    start_date: datetime = None
    end_date: datetime = None
    max_concurrency: int = None
    content_start_date: datetime = None
    content_end_date: datetime = None
    perpetual: bool = None
    modified_by_user_id: int = None
    last_update: datetime = None
    
    