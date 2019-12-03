#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
recreate users

This program was used to hash the passwords in the GVPi user table so they wouldn't be exposed
   at a glance

This file is PEP Only, mostly for testing and DB transfer, and NOT PART of OPAS distributable

"""
__author__      = "Neil R. Shapiro"
__copyright__   = "Copyright 2019, Psychoanalytic Electronic Publishing"
__license__     = "Apache 2.0"
__version__     = "2019.0619.1"
__status__      = "Development"

import sys
import os
import logging
sys.path.append(r'/usr3/keys')  # Private encryption keys
from datetime import datetime, timedelta

#import jwt
#from fastapi import Depends, FastAPI, HTTPException
#from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
#from jwt import PyJWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette.status import HTTP_401_UNAUTHORIZED
from PEPWebKeys import SECRET_KEY, ALGORITHM
import pymysql

db = pymysql.connect("localhost", "root", "", "opascentral")

class User(BaseModel):  # snake_case names to match DB
    user_id: int = None
    username: str = None
    full_name: str = None
    email_address: str = None
    company: str = None
    modified_by_user_id: int = 1
    enabled: bool = True
    admin: bool = False
    user_agrees_date: datetime = None
    user_agrees_to_tracking: bool = None
    user_agrees_to_cookies: bool = None
    added_date: datetime = None
    last_update: datetime = None

class UserInDB(User):
    password: str = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """
    >>> def verify_password(plain_password, hashed_password):
    ("secret", getPasswordHash("secret"))

    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    (Test disabled, since tested via verify_password docstring)
    >> get_password_hash("test 1 2 3 ")

    >>> get_password_hash("temporaryLover")

    """
    return pwd_context.hash(password)

def get_user(username: str):
    """
    >>> get_user("demo")

    """
    curs = db.cursor(pymysql.cursors.DictCursor)

    sql = """SELECT *
             FROM user
             WHERE username = '{}'""" .format(username)

    res = curs.execute(sql)
    if res == 1:
        user = curs.fetchone()
        return UserInDB(**user)
    else:
        return None

def verify_admin(username, password):
    """
    >>> verify_admin("TemporaryDeveloper", "temporaryLover")

    """
    retVal =  None
    admin = get_user(username)
    if admin.enabled and admin.admin:
        if verify_password(password, admin.password):
            retVal = admin

    return retVal   

def create_user(username, password, admin_username, admin_password, company=None, email=None):
    """
    Create a new user!

    >>> create_user("nobody", "nothing", "TemporaryDeveloper", "temporaryLover", "USGS", "nobody@usgs.com")

    """
    retVal = None
    curs = db.cursor(pymysql.cursors.DictCursor)

    admin = verify_admin(admin_username, admin_password)
    if admin is not None:
        # see if user exists:
        user = get_user(username)
        if user is None: # good to go
            user = UserInDB()
            user.username = username
            user.password = get_password_hash(password)
            user.company = company
            user.enabled = True
            user.email_address = email
            user.modified_by_user_id = admin.user_id
            user.enabled = True

            sql = """INSERT INTO user 
                     (
                        username,
                        email_address,
                        enabled,
                        company,
                        password,
                        modified_by_user_id,
                        added_date,
                        last_update
                        )
                    VALUES ('%s', '%s', %s, '%s', '%s', '%s', '%s', '%s')
                  """ % \
                      ( pymysql.escape_string(user.username),
                        user.email_address,
                        user.enabled,
                        pymysql.escape_string(user.company),
                        get_password_hash(user.password),
                        admin.user_id,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
            if curs.execute(sql):
                msg = "Created user {}".format(user.username)
                print (msg)
                db.commit()
            else:
                err = "Could not create user {}".format(user.username)
                logging.error(err)
                print (err)

            curs.close()
            retVal = User(**user.dict())
        else:
            err = "Username {} already in database.".format(user.username)
            logging.error(err)
            print (err)

    return retVal


def authenticate_user(username: str, password: str):
    """
    >>> authenticate_user("TemporaryDeveloper", "temporaryLover")
    <User user_id=13 username='TemporaryDeveloper' full_name=None email_address='neil@scilab-inc.com' company='Scilab Inc.' modified_by_user_id=10 enabled=True admin=True user_agrees_date=None user_agrees_to_tracking=False user_agrees_to_cookies=False added_date=None last_update=datetime.datetime(2019, 6, 20, 12, 9, 49)>

    """
    user = get_user(username)  # returns a UserInDB object
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return User(**user.dict())  # return the User model (sans hashed password), not the UserInDB


def hash_and_copy_passwords():
    """
    Copy all the records passwords from the GVPi user table to the Opas user table
      hashing the passwords so they are not exposed anymore.

    """
    db = pymysql.connect("localhost", "root", "", "opascentral")
    curs = db.cursor(pymysql.cursors.DictCursor)
    curs2 = db.cursor()

    sql = """SELECT *
             FROM user_gvpi
          """ 

    res = curs.execute(sql)
    count = 0
    while count < res:
        count += 1

        user = curs.fetchone()
        print (user)
        if user is not None:
            dbUser = UserInDB(**user)
            if dbUser.user_id < 20:
                continue

            #print (dbUser)

            sql = """INSERT INTO user 
                     (
                        user_id,
                        username,
                        email_address,
                        company,
                        password,
                        modified_by_user_id,
                        last_update
                        )
                    VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')
                  """ % \
                      ( dbUser.user_id,
                        pymysql.escape_string(dbUser.username),
                        dbUser.email_address,
                        pymysql.escape_string(dbUser.company),
                        get_password_hash(dbUser.password),
                        dbUser.modified_by_user_id,
                        dbUser.last_update 
                        )
            retVal = curs2.execute(sql)
            print (dbUser.username, retVal)


    db.commit()
    curs.close()
    curs2.close()



# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":

    print ("Running in Python %s" % sys.version_info[0])

    import doctest
    doctest.testmod()    
    print ("Tests Completed")

    print ("Tests complete")