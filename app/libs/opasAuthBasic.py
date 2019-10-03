import sys
sys.path.append('../libs')

from datetime import datetime, timedelta
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel

#from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from passlib.context import CryptContext
from starlette.status import HTTP_401_UNAUTHORIZED
import pymysql
import opasCentralDBLib

# to get a string like this run:
# openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password):
    """
    >>> get_password_hash("secret")
    
    """
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """
    >>> verify_password("secret", get_password_hash("secret"))
    
    """
    return pwd_context.verify(plain_password, hashed_password)


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str = None

class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    disabled: bool = None

class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI(
        debug=True,
       )

security = HTTPBasic()

def create_new_username(credentials: HTTPBasicCredentials = Depends(security)):
    new_pass = credentials.password
    user = UserInDB()
    user.username  = credentials.username
    return credentials.username

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "foo" or credentials.password != "password":
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/users/currentuser")
def read_current_user(username: str = Depends(get_current_username)):
    return {"username": username}

@app.get("/users/newuser")
def read_new_user(username: str = Depends(create_new_username)):
    return {"username": username}






# -------------------------------------------------------------------------------------------------------
# run it!

if __name__ == "__main__":
    import sys
    print ("Running in Python %s" % sys.version_info[0])
    
    cdb = opasCentralDBLib.opasCentralDB()
    
   
    import doctest
    doctest.testmod()    
    print ("Tests Completed")