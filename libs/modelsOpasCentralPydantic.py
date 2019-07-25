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
  
class UserSubscriptions(UserInDB):
    """
    __View user_active_subscriptions__

    Includes UserInDB and key Subscriptions
      fields.  Filtered down to "active"
      subscriptions, enabled and in date.
 
    User alone is not enough to verify a username
      since they could be in the database
      but not have any active subscriptions
      
    """
    product_id: int = None
    start_date: datetime = None
    end_date: datetime = None
    max_concurrency: int = None
    content_start_date: datetime = None
    content_end_date: datetime = None
    perpetual: bool = None
    referrer: str = None

class Session(BaseModel):  # subset of sessionInfo
    session_id: str = None
    user_id: int = None
    user_ip: str = None
    connected_via: str = None
    referrer: str = None
    session_start: datetime = None
    session_end: datetime = None
    session_expires_time: datetime = None
    access_token: str = None
    token_type: str = None
    authenticated: bool = False
    keep_active: bool = False
    api_client_id: int = None            
    
class Subscriptions(BaseModel):
    user_id: int = None
    product_id: int = None
    start_date: datetime = None
    end_date: datetime = None
    max_concurrency: int = None
    content_start_date: datetime = None
    content_end_date: datetime = None
    perpetual: bool = None
    modified_by_user_id: int = None
    last_update: datetime = None
    
class MostCitedArticles(BaseModel):
    """
    __Table mostcitedarticles__

    A view with rxCode counts derived from the fullbiblioxml table and the articles table
      for citing sources in one of the date ranges.
    """
    rxCode: str = None
    countAll: int = 0
    count5: int = 0
    count10: int = 0
    count20: int = 0
    
class MostCitedArticlesWithDetails(MostCitedArticles):
    """
    __Table MostCitedArticlesWithDetails__
    based on 
    __Table mostcitedarticles__

    A view with rxCode counts derived from the fullbiblioxml table and the articles table
      for citing sources in one of the date ranges.

    Adds to MostCitedArticles model more of the cited article information for display
    
    """
    hdgauthor: str = None
    hdgtitle: str = None
    srctitleseries: str = None
    year: int = None
    vol: str = None
    pgrg: str = None
    