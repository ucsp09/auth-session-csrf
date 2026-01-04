from fastapi import FastAPI, Request, HTTPException, status, Response, Depends
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from aiofile import AIOFile
import json
from uuid import uuid4
import time
from typing import Optional, List

_DEFAULT_ADMIN_USERNAME = 'admin'
_DEFAULT_ADMIN_PASSWORD = 'P@ssword9'
_SESSIONS_JSON_FILE_PATH = 'sessions.json'

logLevel = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(logLevel)
ch = logging.StreamHandler()
ch.setLevel(logLevel)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class LoginRequestSchema(BaseModel):
    username: str
    password: str

class LoginResponseSchema(BaseModel):
    message: str
    sessionId: str
    csrfToken: str

class LoginStatusResponseSchema(BaseModel):
    isLoggedIn: bool
    sessionId: Optional[str] = None
    csrfToken: Optional[str] = None

class LogoutResponseSchema(BaseModel):
    message: str

class GetResourceResponseSchema(BaseModel):
    name: str
    properties: Optional[dict] = None

class GetAllResourcesResponseSchema(BaseModel):
    items: List[GetResourceResponseSchema]
    total: int

def get_uuid():
    return uuid4().hex

async def startup_event_handler():
    logger.info("Running the startup event handler")
    logger.info("Initializing session json file")
    await init_sessions_json_file()
    logger.info("session json file initialized successfully")
    logger.info("startup event handler completed successfully")


async def init_sessions_json_file():
    try:
        if not os.path.exists(_SESSIONS_JSON_FILE_PATH):
            logger.info("sessions json file does not exist. Attempting to create file ...")
            await write_sessions_to_file(content={})
        else:
            logger.info("sessions json file already exists. Skipping creation ...")
    except Exception as e:
        logger.error(f"Error occured while initializing sessions json file. Error:{e}")
        raise

async def read_sessions_from_file():
    try:
        logger.debug("Reading sessions from file")
        async with AIOFile(_SESSIONS_JSON_FILE_PATH, 'r') as afp:
            content = await afp.read()
            return json.loads(content) if content else {}
    except Exception as e:
        logger.error(f"Error occured while reading session file. Error:{e}")
        raise 

async def write_sessions_to_file(content: dict):
    try:
        logger.debug("Writing sessions to file")
        async with AIOFile(_SESSIONS_JSON_FILE_PATH, 'w+') as afp:
            await afp.write(json.dumps(content, indent=4))
    except Exception as e:
        logger.error(f"Error occured while writing session file. Error:{e}")
        raise 

async def create_session(session_id: str, data: dict):
    try:
        sessions = await read_sessions_from_file()
        sessions[session_id] = data
        await write_sessions_to_file(sessions)
    except Exception as e:
        logger.error(f"Error occured while creating session. Error:{e}")
        raise

async def get_session_by_session_id(session_id: str):
    try:
        sessions = await read_sessions_from_file()
        if session_id in sessions:
            return sessions[session_id]
        else:
            return None
    except Exception as e:
        logger.error(f"Error occured while getting session by session_id. Error:{e}")
        raise

async def delete_session_by_session_id(session_id: str):
    try:
        sessions = await read_sessions_from_file()
        sessions.pop(session_id, None)
        await write_sessions_to_file(sessions)
    except Exception as e:
        logger.error(f"Error occured while deleting session by session_id. Error:{e}")
        raise

def is_session_valid(session_expires_at):
    logger.debug(f"Checking session validity. Expires at: {session_expires_at}, Current time: {time.monotonic()}")
    if time.monotonic() >= session_expires_at:
        return False
    return True

def get_session_expiration_timestamp(duration_seconds: int) -> float:
    """Get the expiration timestamp for a session given a duration in seconds."""
    logger.debug(f"Calculating session expiration timestamp with duration: {duration_seconds} seconds.")
    return time.monotonic() + duration_seconds

login_api_router = APIRouter()

@login_api_router.post("/api/v1/login")
async def login(input: LoginRequestSchema, request: Request, response: Response):
    logger.info(f"Recevied a login request for username: {input.username}")
    
    session_id = request.cookies.get('session_id')
    if session_id:
        logger.info(f"Found a session_id:{session_id} in cookie")
        existing_session = await get_session_by_session_id(session_id=session_id)
        if existing_session is not None:
            session_expires_at = existing_session.get('expires_at')
            csrf_token = existing_session.get('csrfToken')
            if session_expires_at is None:
                logger.warning(f"Could not find expires_at field in session record. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
            elif csrf_token is None:
                logger.warning(f"Could not find csrf_token field in session record in db. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
            else:
                logger.info(f"Found a valid session record in db for session_id:{session_id}")
                logger.info("Checking if session is still valid or not")
                if is_session_valid(session_expires_at=session_expires_at):
                    logger.info("Session is valid. Skipping login")
                    return LoginResponseSchema(message=f"There is already an active session for user: {input.username}. Skipping login",
                                               sessionId=session_id,
                                               csrfToken=csrf_token)
                else:
                    logger.info("Session is expired.")
                    logger.info("Deleting the expired session record in db")
                    await delete_session_by_session_id(session_id=session_id)
        else:
            logger.warning(f"Could not find a session record in db for session_id:{session_id}. Possibly cookie deletion in client's browser failed or else some attacker has sent invalid session_id in cookie")

    logger.info(f"Checking if user with username:{input.username} is existing in internal db")
    if input.username == _DEFAULT_ADMIN_USERNAME:
        logger.info(f"User with username: {input.username} found")
        logger.info(f"Validating password for user with username: {input.username}")
        if input.password == _DEFAULT_ADMIN_PASSWORD:
            logger.info(f"Password validation successful for user with username: {input.username}")
        else:
            logger.info(f"Password validation failed for user with username: {input.username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                detail=f"Password validation failed for user with username: {input.username}")
    else:
        logger.info(f"User with username:{input.username} not found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"User with username:{input.username} not found")
    
    logger.info(f"Creating session record for user with username: {input.username} in db")
    session_id = get_uuid()
    csrf_token = get_uuid()
    session_expiration_timestamp = get_session_expiration_timestamp(duration_seconds=60)
    session_record = {
        'username': input.username,
        'csrfToken': csrf_token,
        'expires_at': session_expiration_timestamp
    }
    await create_session(session_id=session_id, data=session_record)
    logger.info(f"Session record with session_id: {session_id} created successfully for user with username: {input.username}")
    
    logger.info(f"Setting session_id cookie in response")
    response.set_cookie("session_id", session_id, max_age=60, httponly=True, samesite='lax')
    logger.info(f"Successfully set the session_id={session_id} cookie in response with params: max_age=60, httponly=true, samesite=lax")

    return LoginResponseSchema(message=f"Logged in user: {input.username} successfully",
                               sessionId=session_id,
                               csrfToken=csrf_token)


@login_api_router.get("/api/v1/login/status")
async def login_status(request: Request):
    logger.info("Received a login status request")

    session_id = request.cookies.get('session_id')
    if session_id is None:
        logger.warning("No session_id cookie found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="No session_id cookie found")
    else:
        logger.info(f"Found a session_id:{session_id} in cookie")
        existing_session = await get_session_by_session_id(session_id=session_id)
        if existing_session is None:
            logger.warning("Could not find a record for session_id in db. Possibly cookie deletion in client's browser failed or else some attacker has sent invalid session_id in cookie")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid session_id cookie sent")
        else:
            session_expires_at = existing_session.get('expires_at')
            username = existing_session.get('username')
            csrf_token = existing_session.get('csrfToken')
            if session_expires_at is None:
                logger.warning(f"Could not find expires_at field in session record. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
            elif csrf_token is None:
                logger.warning(f"Could not find csrf_token field in session record in db. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
            elif username is None:
                logger.warning(f"Could not find username field in session record. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Corrupted session record found in db")
            else:
                logger.info(f"Found a valid session record in db for session_id:{session_id}")
                logger.info("Checking if session is still valid or not")
                if is_session_valid(session_expires_at=session_expires_at):
                    logger.info("Session is valid.")
                    return LoginStatusResponseSchema(isLoggedIn=True, sessionId=session_id, csrfToken=csrf_token)
                else:
                    logger.info("Session is expired.")
                    logger.info("Deleting the expired session record in db")
                    await delete_session_by_session_id(session_id=session_id)
                    return LoginStatusResponseSchema(isLoggedIn=False, sessionId=None, csrfToken=None)

@login_api_router.get("/api/v1/logout")
async def logout(request: Request, response: Response):
    logger.info("Received a logout request")

    session_id = request.cookies.get('session_id')
    if session_id is None:
        logger.warning("No session_id cookie found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="No session_id cookie found")
    else:
        logger.info(f"Found a session_id:{session_id} in cookie")
        existing_session = await get_session_by_session_id(session_id=session_id)
        if existing_session is None:
            logger.warning("Could not find a record for session_id in db. Possibly cookie deletion in client's browser failed or else some attacker has sent invalid session_id in cookie")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid session_id cookie sent")
        else:
            session_expires_at = existing_session.get('expires_at')
            username = existing_session.get('username')
            if session_expires_at is None:
                logger.warning(f"Could not find expires_at field in session record. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Corrupted session record found in db")
            elif username is None:
                logger.warning(f"Could not find username field in session record. Possibly the session record in db is corrupted.")
                logger.warning(f"Deleting the corrupted session record in db")
                await delete_session_by_session_id(session_id=session_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Corrupted session record found in db")
            else:
                logger.info(f"Found a valid session record in db for session_id:{session_id}")
                logger.info("Checking if session is still valid or not")
                if is_session_valid(session_expires_at=session_expires_at):
                    logger.info("Session is valid.")
                    logger.info("Deleting the session record in db")
                    await delete_session_by_session_id(session_id=session_id)
                    logger.info(f"Deleting session_id cookie in response")
                    response.delete_cookie('session_id')
                    logger.info(f"Successfully deleted session_id:{session_id} cookie in response")
                    return LogoutResponseSchema(message=f"Logged out session_id:{session_id} for user: {username} successfully")
                else:
                    logger.info("Session is expired.")
                    logger.info("Deleting the expired session record in db")
                    await delete_session_by_session_id(session_id=session_id)
                    logger.info(f"Deleting session_id cookie in response")
                    response.delete_cookie('session_id')
                    logger.info(f"Successfully deleted session_id:{session_id} cookie in response")
                    return LogoutResponseSchema(message=f"session_id:{session_id} for user: {username} is already expired")

async def validate_protected_api_request(request: Request):
    logger.info("Validating protected api request")
    session_id = request.cookies.get('session_id')
    if session_id is None:
        logger.error("No session_id cookie found in request")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="No session_id cookie found in request")
    else:
        logger.info(f"Found session_id={session_id} cookie in request")
        existing_session = await get_session_by_session_id(session_id=session_id)
        if existing_session is None:
            logger.warning(f"Could not find a session record in db for session_id={session_id}. Possibly cookie deletion in client's browser failed or else some attacker has sent invalid session_id in cookie")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid session_id cookie")
        else:
            logger.info(f"Found a session record in db for session_id={session_id}")
            csrf_token_header = request.headers.get('X-CSRF-TOKEN')
            if csrf_token_header is None:
                logger.error("No csrf token header found in request. Possibly some attacker performing cross site request")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="No csrf token header found in request")
            else:
                session_expires_at = existing_session.get('expires_at')
                username = existing_session.get('username')
                csrf_token = existing_session.get('csrfToken')
                if session_expires_at is None:
                    logger.warning(f"Could not find expires_at field in session record. Possibly the session record in db is corrupted.")
                    logger.warning(f"Deleting the corrupted session record in db")
                    await delete_session_by_session_id(session_id=session_id)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="Corrupted session record found in db")
                elif csrf_token is None:
                    logger.warning(f"Could not find csrf_token field in session record in db. Possibly the session record in db is corrupted.")
                    logger.warning(f"Deleting the corrupted session record in db")
                    await delete_session_by_session_id(session_id=session_id)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="Corrupted session record found in db")
                elif username is None:
                    logger.warning(f"Could not find username field in session record. Possibly the session record in db is corrupted.")
                    logger.warning(f"Deleting the corrupted session record in db")
                    await delete_session_by_session_id(session_id=session_id)
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="Corrupted session record found in db")
                elif csrf_token != csrf_token_header:
                    logger.error(f"csrf token validation failed. Possibly some attacker performing cross site request with invalid csrf token")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                        detail="csrf token validation failed")
                else:
                    logger.info("csrf token validation successfull")
                    logger.info(f"Found a valid session record in db for session_id:{session_id}")
                    logger.info("Checking if session is still valid or not")
                    if is_session_valid(session_expires_at=session_expires_at):
                        logger.info("Session is valid.")
                        return
                    else:
                        logger.info("Session is expired.")
                        logger.info("Deleting the expired session record in db")
                        await delete_session_by_session_id(session_id=session_id)
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                            detail=f"session expired for session_id={session_id}")

protected_api_router = APIRouter()

@protected_api_router.get('/api/v1/protected/resources')
async def get_all_resources(request: Request):
    resources = [{'name': 'resource1', 'properties': {'k1': 'v1', 'k2': 'v2'}},
                 {'name': 'resource2', 'properties': {'k1': 1, 'k2': 2}},]
    return GetAllResourcesResponseSchema(
        items=[GetResourceResponseSchema(name=resource['name'], 
                                         properties=resource['properties']) for resource in resources], 
        total=len(resources))


logger.info("Initializing app")
app = FastAPI()
logger.info("Adding middlewares")
app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    allow_credentials=True,
    allow_headers="*",
    allow_methods="*"
)
logger.info("Adding event handlers")
app.add_event_handler('startup', startup_event_handler)
logger.info("Adding routers")
app.include_router(router=login_api_router)
app.include_router(router=protected_api_router, dependencies=[Depends(validate_protected_api_request)])