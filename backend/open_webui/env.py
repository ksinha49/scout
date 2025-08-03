"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description           |
|------------|----------------|--------------------|-----------------------|
| 2024-11-05 | AAK7S          | AMER-ENH           | OCR ENHANCEMENT       |
| 2025-06-11 | AAK7S          | AMERITAS-ENH-3.1   | Added SSL certi for   |
|            |                |                    |Bedrock API connection |
"""
import importlib.metadata
import json
import logging
import os
import pkgutil
import sys
import shutil
from pathlib import Path
import builtins           #AMER-ENH

import markdown
from bs4 import BeautifulSoup
from open_webui.constants import ERROR_MESSAGES

####################################
# Load .env file
####################################

OPEN_WEBUI_DIR = Path(__file__).parent  # the path containing this file
print(OPEN_WEBUI_DIR)

BACKEND_DIR = OPEN_WEBUI_DIR.parent  # the path containing this file
BASE_DIR = BACKEND_DIR.parent  # the path containing the backend/
## Start AMER-ENH
DOCS_DIR = BASE_DIR / "docs"
print(BACKEND_DIR)
print(BASE_DIR)
OCR_CACHE_DIR = BACKEND_DIR / "cache"
ENV_TMP_DIR = BACKEND_DIR / "tmp"
## END of AMER-ENH

try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(str(BASE_DIR / ".env")))
except ImportError:
    print("dotenv not installed, skipping...")

DOCKER = os.environ.get("DOCKER", "False").lower() == "true"

# device type embedding models - "cpu" (default), "cuda" (nvidia gpu required) or "mps" (apple silicon) - choosing this right can lead to better performance
USE_CUDA = os.environ.get("USE_CUDA_DOCKER", "false")

if USE_CUDA.lower() == "true":
    try:
        import torch
        # Confirm both CUDA and cuDNN are available before enabling GPU
        assert torch.cuda.is_available() and torch.backends.cudnn.is_available(), (
            "CUDA or cuDNN not available"
        )
        DEVICE_TYPE = "cuda"
    except Exception as e:
        cuda_warning = (
            "CUDA/cuDNN unavailable but USE_CUDA_DOCKER is true. "
            f"Resetting USE_CUDA_DOCKER to false: {e}"
        )
        # Fall back to CPU when either CUDA or cuDNN is missing
        os.environ["USE_CUDA_DOCKER"] = "false"
        USE_CUDA = "false"
        DEVICE_TYPE = "cpu"
else:
    DEVICE_TYPE = "cpu"

try:
    import torch

    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        DEVICE_TYPE = "mps"
except Exception:
    pass

####################################
# LOGGING
####################################

GLOBAL_LOG_LEVEL = os.environ.get("GLOBAL_LOG_LEVEL", "").upper()
if GLOBAL_LOG_LEVEL in logging.getLevelNamesMapping():
    logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL, force=True)
else:
    GLOBAL_LOG_LEVEL = "INFO"

log = logging.getLogger(__name__)
log.info(f"GLOBAL_LOG_LEVEL: {GLOBAL_LOG_LEVEL}")

if "cuda_warning" in locals():
    log.warning(cuda_warning)
    del cuda_warning

log_sources = [
    "AUDIO",
    "COMFYUI",
    "CONFIG",
    "DB",
    "IMAGES",
    "MAIN",
    "MODELS",
    "OLLAMA",
    "OPENAI",
    "RAG",
    "WEBHOOK",
    "SOCKET",
    "OAUTH",
]

SRC_LOG_LEVELS = {}

for source in log_sources:
    log_env_var = source + "_LOG_LEVEL"
    SRC_LOG_LEVELS[source] = os.environ.get(log_env_var, "").upper()
    if SRC_LOG_LEVELS[source] not in logging.getLevelNamesMapping():
        SRC_LOG_LEVELS[source] = GLOBAL_LOG_LEVEL
    log.info(f"{log_env_var}: {SRC_LOG_LEVELS[source]}")

log.setLevel(SRC_LOG_LEVELS["CONFIG"])

LOGS_DIR = BACKEND_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
APP_ERROR_LOG_PATH = Path(
    os.environ.get("APP_ERROR_LOG_PATH", LOGS_DIR / "backendlog_error.log")
)
APP_ADMIN_ACTIVITY_LOG_PATH = Path(
    os.environ.get("APP_ADMIN_ACTIVITY_LOG_PATH", LOGS_DIR / "backendlog_admin_activity.log")
)
GUNICORN_CRASH_LOG_PATH = Path(
    os.environ.get("GUNICORN_CRASH_LOG_PATH", LOGS_DIR / "backendlog_gunicorn_crash.log")
)

##Start of AMER-ENH

WEBUI_NAME = os.environ.get("WEBUI_NAME", "AmeritasGPT")

WEBUI_FAVICON_URL = os.environ.get("WEBUI_FAVICON_URL","https://marvel-b1-cdn.bc0a.com/f00000000142088/www.ameritas.com/wp-content/uploads/2021/07/logo_header_@2x.png")


####################################
# Enable/Disable Citations
####################################

ENABLE_CITATION = os.environ.get("ENABLE_CITATION","True").lower() == "true"

####################################
# OLLAMA AND BEDROCK SERVER CERT
####################################

TRUSTED_SIGNATURE_KEY = os.environ.get("TRUSTED_SIGNATURE_KEY", "")
OLLAMA_SERVER_CERT = os.environ.get("OLLAMA_SERVER_CERT"," ")
BEDROCK_SERVER_CERT = os.environ.get("OLLAMA_SERVER_CERT"," ")
IS_CERT_REQ = os.environ.get("IS_CERT_REQ",False) # MOD TAG AMER-ENH
####################################
# ENV (dev,test,prod)
####################################

ENV = os.environ.get("OPENWEBUI_ENV", "dev")

## End of AMER-ENH

FROM_INIT_PY = os.environ.get("FROM_INIT_PY", "False").lower() == "true"

if FROM_INIT_PY:
    PACKAGE_DATA = {"version": importlib.metadata.version("open-webui")}
else:
    try:
        PACKAGE_DATA = json.loads((BASE_DIR / "package.json").read_text())
    except Exception:
        PACKAGE_DATA = {"version": "0.0.0"}


VERSION = PACKAGE_DATA["version"]

## AMER-ENH for proxy setup
AMERITAS_PROXY_URL = os.environ.get("AMERITAS_PROXY_URL", "")

# Function to parse each section
def parse_section(section):
    items = []
    for li in section.find_all("li"):
        # Extract raw HTML string
        raw_html = str(li)

        # Extract text without HTML tags
        text = li.get_text(separator=" ", strip=True)

        # Split into title and content
        parts = text.split(": ", 1)
        title = parts[0].strip() if len(parts) > 1 else ""
        content = parts[1].strip() if len(parts) > 1 else text

        items.append({"title": title, "content": content, "raw": raw_html})
    return items

## Changes for AMER-ENH
try:
    changelog_path = BASE_DIR / "CHANGELOG.md"
    with open(str(changelog_path.absolute()), "r", encoding="utf8") as file:
        changelog_content = file.read()

except Exception:
    changelog_content = (pkgutil.get_data("Scout", "CHANGELOG.md") or b"").decode()

security_md_path = DOCS_DIR / "SECURITY.md"
try:
    with open(security_md_path, "r", encoding="utf8") as file:
        security_md_content = file.read()

except FileNotFoundError:
    log.error("SECURITY.md file not found!")
    security_md_content = ""

# Convert markdown content to HTML
html_content = markdown.markdown(changelog_content)
sec_md_html_content=markdown.markdown(security_md_content)

# Parse the HTML content
soup = BeautifulSoup(html_content, "html.parser")

# Initialize JSON structure
changelog_json = {}
security_json = {}

##End of AMER-ENH

# Iterate over each version
for version in soup.find_all("h2"):
    version_text = version.get_text().strip()
    parts = version_text.split(" - ", 1)
    if len(parts) < 2:
        log.warning(f"Skipping changelog entry with missing date: {version_text}")
        continue
    version_number = parts[0][1:-1]  # Remove brackets
    date = parts[1]

    version_data = {"date": date}

    # Find the next sibling that is a h3 tag (section title)
    current = version.find_next_sibling()

    while current and current.name != "h2":
        if current.name == "h3":
            section_title = current.get_text().lower()  # e.g., "added", "fixed"
            section_items = parse_section(current.find_next_sibling("ul"))
            version_data[section_title] = section_items

        # Move to the next element
        current = current.find_next_sibling()

    changelog_json[version_number] = version_data


CHANGELOG = changelog_json

## AMER-ENH Parse the HTML content
soup = BeautifulSoup(sec_md_html_content, "html.parser")

for section in soup.find_all("h2"):
    section_title = section.get_text().strip()  # Get the title of the section

    # Try to find the next sibling which is an unordered list (assuming that's where details are)
    current = section.find_next_sibling()

    section_data = []
    while current and current.name != "h2":  # Stop when the next section starts
        if current.name == "ul":  # If it's a list, process it using parse_section
            section_data.extend(parse_section(current))
        # Move to the next sibling element
        current = current.find_next_sibling()

    # Add the parsed data for this section to the JSON structure
    security_json[section_title] = section_data

SECURITYMD = security_json

## End of AMER-ENH

####################################
# SAFE_MODE
####################################

SAFE_MODE = os.environ.get("SAFE_MODE", "false").lower() == "true"

####################################
# ENABLE_FORWARD_USER_INFO_HEADERS
####################################

ENABLE_FORWARD_USER_INFO_HEADERS = (
    os.environ.get("ENABLE_FORWARD_USER_INFO_HEADERS", "False").lower() == "true"
)

####################################
# WEBUI_BUILD_HASH
####################################

WEBUI_BUILD_HASH = os.environ.get("WEBUI_BUILD_HASH", "dev-build")

####################################
# DATA/FRONTEND BUILD DIR
####################################

DATA_DIR = Path(os.getenv("DATA_DIR", BACKEND_DIR / "data")).resolve()

if FROM_INIT_PY:
    NEW_DATA_DIR = Path(os.getenv("DATA_DIR", OPEN_WEBUI_DIR / "data")).resolve()
    NEW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check if the data directory exists in the package directory
    if DATA_DIR.exists() and DATA_DIR != NEW_DATA_DIR:
        log.info(f"Moving {DATA_DIR} to {NEW_DATA_DIR}")
        for item in DATA_DIR.iterdir():
            dest = NEW_DATA_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        # Zip the data directory
        shutil.make_archive(DATA_DIR.parent / "open_webui_data", "zip", DATA_DIR)

        # Remove the old data directory
        shutil.rmtree(DATA_DIR)

    DATA_DIR = Path(os.getenv("DATA_DIR", OPEN_WEBUI_DIR / "data"))

STATIC_DIR = Path(os.getenv("STATIC_DIR", OPEN_WEBUI_DIR / "static"))

FONTS_DIR = Path(os.getenv("FONTS_DIR", OPEN_WEBUI_DIR / "static" / "fonts"))

FRONTEND_BUILD_DIR = Path(os.getenv("FRONTEND_BUILD_DIR", BASE_DIR / "build")).resolve()

if FROM_INIT_PY:
    FRONTEND_BUILD_DIR = Path(
        os.getenv("FRONTEND_BUILD_DIR", OPEN_WEBUI_DIR / "frontend")
    ).resolve()

CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("TORCH_HOME", str(CACHE_DIR / "torch"))
os.environ.setdefault("HF_HOME", str(CACHE_DIR / "huggingface"))
os.environ.setdefault("HF_DATASETS_CACHE", str(CACHE_DIR / "huggingface" / "datasets"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(CACHE_DIR / "huggingface"))
for env_var in ("TORCH_HOME", "HF_HOME", "HF_DATASETS_CACHE", "TRANSFORMERS_CACHE"):
    Path(os.environ[env_var]).mkdir(parents=True, exist_ok=True)

####################################
# Whisper model directory
####################################

WHISPER_MODEL_DIR = Path(
    os.getenv("WHISPER_MODEL_DIR", DATA_DIR / "cache" / "whisper" / "models")
).resolve()
WHISPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)

####################################
# Database
####################################

# Check if the file exists
if os.path.exists(f"{DATA_DIR}/ollama.db"):
    # Rename the file
    os.rename(f"{DATA_DIR}/ollama.db", f"{DATA_DIR}/webui.db")
    log.info("Database migrated from Ollama-WebUI successfully.")
else:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR}/webui.db")

# Replace the postgres:// with postgresql://
if "postgres://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

DATABASE_SCHEMA = os.environ.get("DATABASE_SCHEMA", None)

DATABASE_POOL_SIZE = os.environ.get("DATABASE_POOL_SIZE", 0)

if DATABASE_POOL_SIZE == "":
    DATABASE_POOL_SIZE = 0
else:
    try:
        DATABASE_POOL_SIZE = int(DATABASE_POOL_SIZE)
    except Exception:
        DATABASE_POOL_SIZE = 0

DATABASE_POOL_MAX_OVERFLOW = os.environ.get("DATABASE_POOL_MAX_OVERFLOW", 0)

if DATABASE_POOL_MAX_OVERFLOW == "":
    DATABASE_POOL_MAX_OVERFLOW = 0
else:
    try:
        DATABASE_POOL_MAX_OVERFLOW = int(DATABASE_POOL_MAX_OVERFLOW)
    except Exception:
        DATABASE_POOL_MAX_OVERFLOW = 0

DATABASE_POOL_TIMEOUT = os.environ.get("DATABASE_POOL_TIMEOUT", 30)

if DATABASE_POOL_TIMEOUT == "":
    DATABASE_POOL_TIMEOUT = 30
else:
    try:
        DATABASE_POOL_TIMEOUT = int(DATABASE_POOL_TIMEOUT)
    except Exception:
        DATABASE_POOL_TIMEOUT = 30

DATABASE_POOL_RECYCLE = os.environ.get("DATABASE_POOL_RECYCLE", 3600)

if DATABASE_POOL_RECYCLE == "":
    DATABASE_POOL_RECYCLE = 3600
else:
    try:
        DATABASE_POOL_RECYCLE = int(DATABASE_POOL_RECYCLE)
    except Exception:
        DATABASE_POOL_RECYCLE = 3600

RESET_CONFIG_ON_START = (
    os.environ.get("RESET_CONFIG_ON_START", "False").lower() == "true"
)

ENABLE_REALTIME_CHAT_SAVE = (
    os.environ.get("ENABLE_REALTIME_CHAT_SAVE", "False").lower() == "true"
)

####################################
# REDIS
####################################

REDIS_URL = os.environ.get("REDIS_URL", "")
REDIS_SENTINEL_HOSTS = os.environ.get("REDIS_SENTINEL_HOSTS", "")
REDIS_SENTINEL_PORT = os.environ.get("REDIS_SENTINEL_PORT", "26379")

####################################
# WEBUI_AUTH (Required for security)
####################################

WEBUI_AUTH = os.environ.get("WEBUI_AUTH", "True").lower() == "true"
WEBUI_AUTH_TRUSTED_EMAIL_HEADER = os.environ.get(
    "WEBUI_AUTH_TRUSTED_EMAIL_HEADER", None
)
WEBUI_AUTH_TRUSTED_NAME_HEADER = os.environ.get("WEBUI_AUTH_TRUSTED_NAME_HEADER", None)

BYPASS_MODEL_ACCESS_CONTROL = (
    os.environ.get("BYPASS_MODEL_ACCESS_CONTROL", "False").lower() == "true"
)

####################################
# WEBUI_SECRET_KEY
####################################

WEBUI_SECRET_KEY = os.environ.get(
    "WEBUI_SECRET_KEY",
    os.environ.get(
        "WEBUI_JWT_SECRET_KEY", "t0p-s3cr3t"
    ),  # DEPRECATED: remove at next major version
)

WEBUI_SESSION_COOKIE_SAME_SITE = os.environ.get("WEBUI_SESSION_COOKIE_SAME_SITE", "lax")

WEBUI_SESSION_COOKIE_SECURE = (
    os.environ.get("WEBUI_SESSION_COOKIE_SECURE", "false").lower() == "true"
)

WEBUI_AUTH_COOKIE_SAME_SITE = os.environ.get(
    "WEBUI_AUTH_COOKIE_SAME_SITE", WEBUI_SESSION_COOKIE_SAME_SITE
)

WEBUI_AUTH_COOKIE_SECURE = (
    os.environ.get(
        "WEBUI_AUTH_COOKIE_SECURE",
        os.environ.get("WEBUI_SESSION_COOKIE_SECURE", "false"),
    ).lower()
    == "true"
)

FILE_PROCESSING_FUNCTIONAL_USER = os.environ.get("FILE_PROCESSING_FUNCTIONAL_USER", "")
FILE_TIMEOUT = os.environ.get("FILE_TIMEOUT", "")
FUNCTIONAL_USER_ROLE = os.environ.get("FUNCTIONAL_USER_ROLE", "")
if WEBUI_AUTH and WEBUI_SECRET_KEY == "":
    raise ValueError(ERROR_MESSAGES.ENV_VAR_NOT_FOUND)

ENABLE_WEBSOCKET_SUPPORT = (
    os.environ.get("ENABLE_WEBSOCKET_SUPPORT", "True").lower() == "true"
)

WEBSOCKET_MANAGER = os.environ.get("WEBSOCKET_MANAGER", "")

WEBSOCKET_REDIS_URL = os.environ.get("WEBSOCKET_REDIS_URL", REDIS_URL)
WEBSOCKET_REDIS_LOCK_TIMEOUT = os.environ.get("WEBSOCKET_REDIS_LOCK_TIMEOUT", 60)

WEBSOCKET_SENTINEL_HOSTS = os.environ.get("WEBSOCKET_SENTINEL_HOSTS", "")

WEBSOCKET_SENTINEL_PORT = os.environ.get("WEBSOCKET_SENTINEL_PORT", "26379")

AIOHTTP_CLIENT_TIMEOUT = os.environ.get("AIOHTTP_CLIENT_TIMEOUT", "")

CHAT_AMERITAS_FRONT_END_URL = os.environ.get("CHAT_AMERITAS_FRONT_END_URL", "")

if AIOHTTP_CLIENT_TIMEOUT == "":
    AIOHTTP_CLIENT_TIMEOUT = None
else:
    try:
        AIOHTTP_CLIENT_TIMEOUT = int(AIOHTTP_CLIENT_TIMEOUT)
    except Exception:
        AIOHTTP_CLIENT_TIMEOUT = 300

AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST = os.environ.get(
    "AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST",
    os.environ.get("AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST", "10"),
)

if AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST == "":
    AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST = None
else:
    try:
        AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST = int(AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST)
    except Exception:
        AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST = 10

####################################
# OFFLINE_MODE
####################################

OFFLINE_MODE = os.environ.get("OFFLINE_MODE", "false").lower() == "true"

if OFFLINE_MODE:
    os.environ["HF_HUB_OFFLINE"] = "1"

####################################
# AUDIT LOGGING
####################################
# Where to store log file
AUDIT_LOGS_FILE_PATH = f"{DATA_DIR}/audit.log"
# Maximum size of a file before rotating into a new log file
AUDIT_LOG_FILE_ROTATION_SIZE = os.getenv("AUDIT_LOG_FILE_ROTATION_SIZE", "10MB")
# METADATA | REQUEST | REQUEST_RESPONSE
AUDIT_LOG_LEVEL = os.getenv("AUDIT_LOG_LEVEL", "NONE").upper()
try:
    MAX_BODY_LOG_SIZE = int(os.environ.get("MAX_BODY_LOG_SIZE") or 2048)
except ValueError:
    MAX_BODY_LOG_SIZE = 2048

# Comma separated list for urls to exclude from audit
AUDIT_EXCLUDED_PATHS = os.getenv("AUDIT_EXCLUDED_PATHS", "/chats,/chat,/folders").split(
    ","
)
AUDIT_EXCLUDED_PATHS = [path.strip() for path in AUDIT_EXCLUDED_PATHS]
AUDIT_EXCLUDED_PATHS = [path.lstrip("/") for path in AUDIT_EXCLUDED_PATHS]

####################################
# OPENTELEMETRY
####################################

ENABLE_OTEL = os.environ.get("ENABLE_OTEL", "False").lower() == "true"
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
)
OTEL_SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "open-webui")
OTEL_RESOURCE_ATTRIBUTES = os.environ.get(
    "OTEL_RESOURCE_ATTRIBUTES", ""
)  # e.g. key1=val1,key2=val2
OTEL_TRACES_SAMPLER = os.environ.get(
    "OTEL_TRACES_SAMPLER", "parentbased_always_on"
).lower()

####################################
# TOOLS/FUNCTIONS PIP OPTIONS
####################################

PIP_OPTIONS = os.getenv("PIP_OPTIONS", "").split()
PIP_PACKAGE_INDEX_OPTIONS = os.getenv("PIP_PACKAGE_INDEX_OPTIONS", "").split()


## AMER-ENH additional config
####################################
# OCR ENV VARAIBLES 
####################################
USE_CUDA = os.environ.get("USE_CUDA", "true").lower() == "true"
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 10))
DPI = int(os.environ.get("DPI", 100))
MAX_GPU_RETRIES = int(os.environ.get("MAX_GPU_RETRIES", 3))
PYTORCH_CUDA_ALLOC_CONF = os.environ.get("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
OCR_ENGINE = os.environ.get("OCR_ENGINE","easyocr")
CACHE_EXPIRY_DAYS = int(os.environ.get("CACHE_EXPIRY_DAYS",7))
OCR_TIMEOUT = int(os.environ.get("OCR_TIMEOUT",700))

####################################
# SAFE EXECUTION CONFIG
####################################
# Option 1: Load safe builtins from a file (if SAFE_BUILTINS_FILE is set)
def load_list_from_file(env_var_name, default_list=None):
    filepath = os.environ.get(env_var_name)
    if filepath and Path(filepath).exists():
        with open(filepath, "r", encoding="utf-8") as f:
            json_data=json.load(f)
            return json_data
        
    return default_list if default_list is not None else []

# Default lists if no external file is provided
DEFAULT_SAFE_BUILTINS_LIST = ["abs", "all", "any", "bool", "callable", "chr",
                                "dict", "enumerate", "filter", "float", "int",
                                "len", "list", "map", "max", "min", "ord",
                                "pow", "range", "reversed", "round", "set",
                                "slice", "str", "sum", "tuple"]
DEFAULT_ALLOWED_MODULES_LIST = ["os", "re", "sys", "logging", "tempfile", "types"]

# Option 2: Load safe builtins directly from JSON provided in the env variable
SAFE_BUILTINS_JSON = os.environ.get("SAFE_BUILTINS_JSON")
if SAFE_BUILTINS_JSON:
    try:
        # Expecting a JSON object mapping keys to built-in names, e.g.,
        # {"abs": "abs", "all": "all", ...}
        safe_builtins_config = json.loads(SAFE_BUILTINS_JSON)
        # Convert string values to actual built-in functions from the builtins module.
        SAFE_BUILTINS = {
            key: getattr(builtins, func_name)
            for key, func_name in safe_builtins_config.items()
            if hasattr(builtins, func_name)
        }
        log.info("Loaded SAFE_BUILTINS from SAFE_BUILTINS_JSON")
    except Exception as e:
        log.error(f"Error parsing SAFE_BUILTINS_JSON: {e}")
        SAFE_BUILTINS = {name: getattr(builtins, name) for name in DEFAULT_SAFE_BUILTINS_LIST}
else:
    # Fallback: try loading from file; if not set, use default list.
    SAFE_BUILTINS_LIST = load_list_from_file("SAFE_BUILTINS_FILE", DEFAULT_SAFE_BUILTINS_LIST)
    SAFE_BUILTINS = {name: getattr(builtins, name) for name in SAFE_BUILTINS_LIST}

# Allowed modules list
ALLOWED_MODULES_LIST = load_list_from_file("ALLOWED_MODULES_FILE", DEFAULT_ALLOWED_MODULES_LIST)
ALLOWED_MODULES = {
                key: getattr(builtins, func_name)
                for key, func_name in ALLOWED_MODULES_LIST.items()
                if hasattr(builtins, func_name)
            }
####################################
# AUTHORIZED URLS
####################################
def get_authorized_urls():
    # Retrieve a comma-separated string from an environment variable
    urls = os.environ.get("AUTHORIZED_URLS", "")
    # Split the string into a list and strip any whitespace
    return [url.strip() for url in urls.split(",") if url.strip()]

AUTHORIZED_URLS = get_authorized_urls()