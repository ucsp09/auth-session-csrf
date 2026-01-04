from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from aiofile import AIOFile
import logging
import os
import aiohttp


logLevel = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(logLevel)
ch = logging.StreamHandler()
ch.setLevel(logLevel)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Initializing FastAPI app")
app = FastAPI()

logger.info("Adding CORS middleware to app")
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=False,
    allow_headers="*",
    allow_methods="*"
)

async def get_file_content(file_path: str) -> str:
    """Read the content of a file asynchronously."""
    logger.debug(f"Attempting to read file: {file_path}")
    try:
        async with AIOFile(file_path, 'r') as afp:
            content = await afp.read()
        logger.debug(f"Successfully read file: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error reading file: {file_path}. Error: {e}")
        return f"<h1>Error loading file: {str(e)}</h1>"


@app.get("/ui/{page}")
async def serve_ui_page(page: str):
    """Serve a UI page."""
    logger.info(f"Serving UI page: {page}")
    try:
        ui_page_html_file_path = f"ui/{page}.html"
        if os.path.exists(ui_page_html_file_path):
            logger.debug(f"UI page file found at: {ui_page_html_file_path}")
            content = await get_file_content(ui_page_html_file_path)
            return HTMLResponse(content=content)
        else:
            logger.warning(f"UI page file not found at: {ui_page_html_file_path}")
            return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)
    except Exception as e:
        logger.error(f"Error serving UI page: {page}. Error: {e}")
        return HTMLResponse(content=f"<h1>Error loading page: {str(e)}</h1>", status_code=500)

@app.get("/ui/static/{file_path:path}")
async def serve_static_file(file_path: str):
    """Serve a static file."""
    logger.info(f"Serving static file: {file_path}")
    try:
        static_file_full_path = f"ui/static/{file_path}"
        if os.path.exists(static_file_full_path):
            logger.debug(f"Static file found at: {static_file_full_path}")
            return FileResponse(static_file_full_path)
        else:
            logger.warning(f"Static file not found at: {static_file_full_path}")
            return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)
    except Exception as e:
        logger.error(f"Error serving static file: {file_path}. Error: {e}")
        return HTMLResponse(content=f"<h1>Error loading file: {str(e)}</h1>", status_code=500)

@app.get("/ui/protected/resources")
async def get_all_resources(request: Request):
    logger.info("Request received: GET /ui/protected/resources")
    
    url = "http://localhost:8000/api/v1/protected/resources"
    logger.info(f"Fetching protected resources from URL: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=request.headers) as response:
                logger.info(f"Received response with status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully retrieved {data}")
                    return data
                else:
                    # Log detailed info for non-200 responses
                    text = await response.text()
                    logger.warning(f"Failed to retrieve resources. Status: {response.status}, Response: {text}")
                    return JSONResponse(status_code=response.status, content={"error": "Failed to fetch resources"})
    except Exception as e:
        logger.error(f"Exception occurred while retrieving resources: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
