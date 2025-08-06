# TODO: Merge this with the webui_app and make it a single app
"""
Modification Log:
------------------
| Date       | Author         | MOD TAG                       | Description                                                                    |
|------------|----------------|-------------------------------|--------------------------------------------------------------------------------|
| 2024-11-16 | AAK7S          | AMER-HOTFIX-1                 | VECTOR DB INSERT IN BATCH FOR BETTER PERFORMANCE                               |
| 2025-12-02 | X1BA           | CWE-209                       | Replace direct exception messages with generic responses in user-facing outputs|
| 2025-04-06 | AAK7S          | ASYNC-IMPROVEMENT       | Added parallel asynchronous batch insertion for large vector DB loads                |
"""

# MOD TAG RAG-FILTERS: Accept a single collection with optional filter list.
import json
import logging
import mimetypes
import os
import shutil

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union
import psutil

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    Request,
    status,
    APIRouter,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import tiktoken
from threading import BoundedSemaphore
from concurrent.futures import ThreadPoolExecutor, as_completed


from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_core.documents import Document

from open_webui.models.files import FileModel, Files
from open_webui.models.knowledge import Knowledges
from open_webui.models.users import UserModel
from open_webui.storage.provider import Storage


from open_webui.retrieval.vector.connector import VECTOR_DB_CLIENT

# Document loaders
from open_webui.retrieval.loaders.main import Loader
from open_webui.retrieval.loaders.youtube import YoutubeLoader

# Web search engines
from open_webui.retrieval.web.main import SearchResult
from open_webui.retrieval.web.utils import get_web_loader
from open_webui.retrieval.web.brave import search_brave
from open_webui.retrieval.web.kagi import search_kagi
from open_webui.retrieval.web.mojeek import search_mojeek
from open_webui.retrieval.web.bocha import search_bocha
from open_webui.retrieval.web.duckduckgo import search_duckduckgo
from open_webui.retrieval.web.google_pse import search_google_pse, GooglePSEError
from open_webui.retrieval.web.jina_search import search_jina
from open_webui.retrieval.web.searchapi import search_searchapi
from open_webui.retrieval.web.serpapi import search_serpapi
from open_webui.retrieval.web.searxng import search_searxng
from open_webui.retrieval.web.serper import search_serper
from open_webui.retrieval.web.serply import search_serply
from open_webui.retrieval.web.serpstack import search_serpstack
from open_webui.retrieval.web.tavily import search_tavily
from open_webui.retrieval.web.bing import search_bing
from open_webui.retrieval.web.exa import search_exa
from open_webui.retrieval.web.perplexity import search_perplexity

from open_webui.retrieval.utils import (
    get_embedding_function,
    get_model_path,
    query_collection,
    query_collection_with_hybrid_search,
    query_doc,
    query_doc_with_hybrid_search,
)
from open_webui.utils.misc import (
    calculate_sha256_string,
)
from open_webui.utils.collections import build_user_collection_name
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.exceptionutil import getErrorMsg

from open_webui.config import (
    ENV,
    RAG_EMBEDDING_MODEL_AUTO_UPDATE,
    RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE,
    RAG_RERANKING_MODEL_AUTO_UPDATE,
    RAG_RERANKING_MODEL_TRUST_REMOTE_CODE,
    UPLOAD_DIR,
    DEFAULT_LOCALE,
    RAG_EMBEDDING_CONTENT_PREFIX,
    RAG_EMBEDDING_QUERY_PREFIX,
)
from open_webui.env import (
    SRC_LOG_LEVELS,
    DEVICE_TYPE,
    DOCKER,
)
from open_webui.constants import ERROR_MESSAGES

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])

##########################################
#
# Utility functions
#
##########################################

"""
MOD: AMER-HOTFIX-1: Addressing vectordb Load performance issue
with batch processing
"""


def get_dynamic_batch_size(max_size=1000, min_size=10):
    """
    Determines the batch size based on current CPU and memory usage.

    Args:
        max_size (int): Maximum allowable batch size.
        min_size (int): Minimum allowable batch size.

    Returns:
        int: Calculated batch size.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    available_mem_mb = mem.available / (1024 * 1024)  # Convert bytes to MB

    # Define thresholds
    if cpu_percent < 50 and available_mem_mb > 1000:
        return max_size
    elif cpu_percent < 75 and available_mem_mb > 500:
        return max(max_size // 2, min_size)
    else:
        return min_size


"""
MOD: AMER-HOTFIX-1: End of Mod
"""


def get_ef(
    engine: str,
    embedding_model: str,
    auto_update: bool = False,
):
    ef = None
    if embedding_model and engine == "":
        from sentence_transformers import SentenceTransformer

        try:
            ef = SentenceTransformer(
                get_model_path(embedding_model, auto_update),
                device=DEVICE_TYPE,
                trust_remote_code=RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE,
            )
        except Exception as e:
            log.debug(f"Error loading SentenceTransformer: {e}")

    return ef


def get_rf(
    reranking_model: str,
    auto_update: bool = False,
):
    rf = None
    if reranking_model:
        if any(model in reranking_model for model in ["jinaai/jina-colbert-v2"]):
            try:
                from open_webui.retrieval.models.colbert import ColBERT

                rf = ColBERT(
                    get_model_path(reranking_model, auto_update),
                    env="docker" if DOCKER else None,
                )

            except Exception as e:
                log.error(f"ColBERT: {e}")
                raise Exception(ERROR_MESSAGES.DEFAULT(e))
        else:
            import sentence_transformers

            try:
                rf = sentence_transformers.CrossEncoder(
                    get_model_path(reranking_model, auto_update),
                    device=DEVICE_TYPE,
                    trust_remote_code=RAG_RERANKING_MODEL_TRUST_REMOTE_CODE,
                )
            except:
                log.error("CrossEncoder error")
                raise Exception(ERROR_MESSAGES.DEFAULT("CrossEncoder error"))
    return rf


##########################################
#
# Concurrency control for vector DB insertion
#
##########################################

# Limit concurrent vector DB insertions to 5 at a time.
CONCURRENT_INSERTION_SEMAPHORE = BoundedSemaphore(value=5)


def _safe_insert(collection_name: str, batch: list):
    with CONCURRENT_INSERTION_SEMAPHORE:
        VECTOR_DB_CLIENT.insert(collection_name=collection_name, items=batch)


##########################################
#
# API routes
#
##########################################


router = APIRouter()


class CollectionNameForm(BaseModel):
    collection_name: Optional[str] = None
    session_id: Optional[str] = None


class ProcessUrlForm(CollectionNameForm):
    url: str


class SearchForm(CollectionNameForm):
    query: str


@router.get("/")
async def get_status(request: Request) -> Dict[str, Any]:
    """Return current retrieval configuration values."""
    return {
        "status": True,
        "chunk_size": request.app.state.config.CHUNK_SIZE,
        "chunk_overlap": request.app.state.config.CHUNK_OVERLAP,
        "template": request.app.state.config.RAG_TEMPLATE,
        "embedding_engine": request.app.state.config.RAG_EMBEDDING_ENGINE,
        "embedding_model": request.app.state.config.RAG_EMBEDDING_MODEL,
        "reranking_model": request.app.state.config.RAG_RERANKING_MODEL,
        "embedding_batch_size": request.app.state.config.RAG_EMBEDDING_BATCH_SIZE,
    }


@router.get("/embedding")
async def get_embedding_config(
    request: Request, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Return embedding engine configuration."""
    return {
        "status": True,
        "embedding_engine": request.app.state.config.RAG_EMBEDDING_ENGINE,
        "embedding_model": request.app.state.config.RAG_EMBEDDING_MODEL,
        "embedding_batch_size": request.app.state.config.RAG_EMBEDDING_BATCH_SIZE,
        "openai_config": {
            "url": request.app.state.config.RAG_OPENAI_API_BASE_URL,
            "key": request.app.state.config.RAG_OPENAI_API_KEY,
        },
        "ollama_config": {
            "url": request.app.state.config.RAG_OLLAMA_BASE_URL,
            "key": request.app.state.config.RAG_OLLAMA_API_KEY,
        },
    }


@router.get("/reranking")
async def get_reraanking_config(
    request: Request, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Return reranking model configuration."""
    return {
        "status": True,
        "reranking_model": request.app.state.config.RAG_RERANKING_MODEL,
    }


class OpenAIConfigForm(BaseModel):
    url: str
    key: str


class OllamaConfigForm(BaseModel):
    url: str
    key: str


class EmbeddingModelUpdateForm(BaseModel):
    openai_config: Optional[OpenAIConfigForm] = None
    ollama_config: Optional[OllamaConfigForm] = None
    embedding_engine: str
    embedding_model: str
    embedding_batch_size: Optional[int] = 1


@router.post("/embedding/update")
async def update_embedding_config(
    request: Request, form_data: EmbeddingModelUpdateForm, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Modify embedding engine configuration."""
    log.info(
        f"Updating embedding model: {request.app.state.config.RAG_EMBEDDING_MODEL} to {form_data.embedding_model}"
    )
    try:
        request.app.state.config.RAG_EMBEDDING_ENGINE = form_data.embedding_engine
        request.app.state.config.RAG_EMBEDDING_MODEL = form_data.embedding_model

        if request.app.state.config.RAG_EMBEDDING_ENGINE in ["ollama", "openai"]:
            if form_data.openai_config is not None:
                request.app.state.config.RAG_OPENAI_API_BASE_URL = (
                    form_data.openai_config.url
                )
                request.app.state.config.RAG_OPENAI_API_KEY = (
                    form_data.openai_config.key
                )

            if form_data.ollama_config is not None:
                request.app.state.config.RAG_OLLAMA_BASE_URL = (
                    form_data.ollama_config.url
                )
                request.app.state.config.RAG_OLLAMA_API_KEY = (
                    form_data.ollama_config.key
                )

            request.app.state.config.RAG_EMBEDDING_BATCH_SIZE = (
                form_data.embedding_batch_size
            )

        request.app.state.ef = get_ef(
            request.app.state.config.RAG_EMBEDDING_ENGINE,
            request.app.state.config.RAG_EMBEDDING_MODEL,
        )

        request.app.state.EMBEDDING_FUNCTION = get_embedding_function(
            request.app.state.config.RAG_EMBEDDING_ENGINE,
            request.app.state.config.RAG_EMBEDDING_MODEL,
            request.app.state.ef,
            (
                request.app.state.config.RAG_OPENAI_API_BASE_URL
                if request.app.state.config.RAG_EMBEDDING_ENGINE == "openai"
                else request.app.state.config.RAG_OLLAMA_BASE_URL
            ),
            (
                request.app.state.config.RAG_OPENAI_API_KEY
                if request.app.state.config.RAG_EMBEDDING_ENGINE == "openai"
                else request.app.state.config.RAG_OLLAMA_API_KEY
            ),
            request.app.state.config.RAG_EMBEDDING_BATCH_SIZE,
        )
        log.info(
            "Embedding config updated",
            extra={
                "admin_activity": True,
                "admin_email": user.email,
                "action": "update_embedding_config",
                "payload": form_data.model_dump(),
            },
        )
        return {
            "status": True,
            "embedding_engine": request.app.state.config.RAG_EMBEDDING_ENGINE,
            "embedding_model": request.app.state.config.RAG_EMBEDDING_MODEL,
            "embedding_batch_size": request.app.state.config.RAG_EMBEDDING_BATCH_SIZE,
            "openai_config": {
                "url": request.app.state.config.RAG_OPENAI_API_BASE_URL,
                "key": request.app.state.config.RAG_OPENAI_API_KEY,
            },
            "ollama_config": {
                "url": request.app.state.config.RAG_OLLAMA_BASE_URL,
                "key": request.app.state.config.RAG_OLLAMA_API_KEY,
            },
        }
    except Exception as e:
        log.exception(f"Problem updating embedding model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


class RerankingModelUpdateForm(BaseModel):
    reranking_model: str


@router.post("/reranking/update")
async def update_reranking_config(
    request: Request, form_data: RerankingModelUpdateForm, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Change the reranking model in use."""
    log.info(
        f"Updating reranking model: {request.app.state.config.RAG_RERANKING_MODEL} to {form_data.reranking_model}"
    )
    try:
        request.app.state.config.RAG_RERANKING_MODEL = form_data.reranking_model

        try:
            request.app.state.rf = get_rf(
                request.app.state.config.RAG_RERANKING_MODEL,
                True,
            )
        except Exception as e:
            log.error(f"Error loading reranking model: {e}")
            request.app.state.config.ENABLE_RAG_HYBRID_SEARCH = False
        log.info(
            "Reranking config updated",
            extra={
                "admin_activity": True,
                "admin_email": user.email,
                "action": "update_reranking_config",
                "payload": form_data.model_dump(),
            },
        )
        return {
            "status": True,
            "reranking_model": request.app.state.config.RAG_RERANKING_MODEL,
        }
    except Exception as e:
        log.exception(f"Problem updating reranking model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


@router.get("/config")
async def get_rag_config(
    request: Request, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Return server-side retrieval configuration."""
    return {
        "status": True,
        "pdf_extract_images": request.app.state.config.PDF_EXTRACT_IMAGES,
        "RAG_FULL_CONTEXT": request.app.state.config.RAG_FULL_CONTEXT,
        "BYPASS_EMBEDDING_AND_RETRIEVAL": request.app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL,
        "enable_google_drive_integration": request.app.state.config.ENABLE_GOOGLE_DRIVE_INTEGRATION,
        "enable_onedrive_integration": request.app.state.config.ENABLE_ONEDRIVE_INTEGRATION,
        "content_extraction": {
            "engine": request.app.state.config.CONTENT_EXTRACTION_ENGINE,
            "tika_server_url": request.app.state.config.TIKA_SERVER_URL,
            "docling_server_url": request.app.state.config.DOCLING_SERVER_URL,
            "document_intelligence_config": {
                "endpoint": request.app.state.config.DOCUMENT_INTELLIGENCE_ENDPOINT,
                "key": request.app.state.config.DOCUMENT_INTELLIGENCE_KEY,
            },
        },
        "chunk": {
            "text_splitter": request.app.state.config.TEXT_SPLITTER,
            "chunk_size": request.app.state.config.CHUNK_SIZE,
            "chunk_overlap": request.app.state.config.CHUNK_OVERLAP,
        },
        "file": {
            "max_size": request.app.state.config.FILE_MAX_SIZE,
            "max_count": request.app.state.config.FILE_MAX_COUNT,
        },
        "youtube": {
            "language": request.app.state.config.YOUTUBE_LOADER_LANGUAGE,
            "translation": request.app.state.YOUTUBE_LOADER_TRANSLATION,
            "proxy_url": request.app.state.config.YOUTUBE_LOADER_PROXY_URL,
        },
        "web": {
            "ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION": request.app.state.config.ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION,
            "BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL": request.app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL,
            "search": {
                "enabled": request.app.state.config.ENABLE_RAG_WEB_SEARCH,
                "drive": request.app.state.config.ENABLE_GOOGLE_DRIVE_INTEGRATION,
                "onedrive": request.app.state.config.ENABLE_ONEDRIVE_INTEGRATION,
                "engine": request.app.state.config.RAG_WEB_SEARCH_ENGINE,
                "searxng_query_url": request.app.state.config.SEARXNG_QUERY_URL,
                "google_pse_api_key": request.app.state.config.GOOGLE_PSE_API_KEY,
                "google_pse_engine_id": request.app.state.config.GOOGLE_PSE_ENGINE_ID,
                "brave_search_api_key": request.app.state.config.BRAVE_SEARCH_API_KEY,
                "kagi_search_api_key": request.app.state.config.KAGI_SEARCH_API_KEY,
                "mojeek_search_api_key": request.app.state.config.MOJEEK_SEARCH_API_KEY,
                "bocha_search_api_key": request.app.state.config.BOCHA_SEARCH_API_KEY,
                "serpstack_api_key": request.app.state.config.SERPSTACK_API_KEY,
                "serpstack_https": request.app.state.config.SERPSTACK_HTTPS,
                "serper_api_key": request.app.state.config.SERPER_API_KEY,
                "serply_api_key": request.app.state.config.SERPLY_API_KEY,
                "tavily_api_key": request.app.state.config.TAVILY_API_KEY,
                "searchapi_api_key": request.app.state.config.SEARCHAPI_API_KEY,
                "searchapi_engine": request.app.state.config.SEARCHAPI_ENGINE,
                "serpapi_api_key": request.app.state.config.SERPAPI_API_KEY,
                "serpapi_engine": request.app.state.config.SERPAPI_ENGINE,
                "jina_api_key": request.app.state.config.JINA_API_KEY,
                "bing_search_v7_endpoint": request.app.state.config.BING_SEARCH_V7_ENDPOINT,
                "bing_search_v7_subscription_key": request.app.state.config.BING_SEARCH_V7_SUBSCRIPTION_KEY,
                "exa_api_key": request.app.state.config.EXA_API_KEY,
                "perplexity_api_key": request.app.state.config.PERPLEXITY_API_KEY,
                "result_count": request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                "trust_env": request.app.state.config.RAG_WEB_SEARCH_TRUST_ENV,
                "concurrent_requests": request.app.state.config.RAG_WEB_SEARCH_CONCURRENT_REQUESTS,
                "domain_filter_list": request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            },
        },
    }


class FileConfig(BaseModel):
    max_size: Optional[int] = None
    max_count: Optional[int] = None


class DocumentIntelligenceConfigForm(BaseModel):
    endpoint: str
    key: str


class ContentExtractionConfig(BaseModel):
    engine: str = ""
    tika_server_url: Optional[str] = None
    docling_server_url: Optional[str] = None
    document_intelligence_config: Optional[DocumentIntelligenceConfigForm] = None


class ChunkParamUpdateForm(BaseModel):
    text_splitter: Optional[str] = None
    chunk_size: int
    chunk_overlap: int


class YoutubeLoaderConfig(BaseModel):
    language: list[str]
    translation: Optional[str] = None
    proxy_url: str = ""


class WebSearchConfig(BaseModel):
    enabled: bool
    engine: Optional[str] = None
    searxng_query_url: Optional[str] = None
    google_pse_api_key: Optional[str] = None
    google_pse_engine_id: Optional[str] = None
    brave_search_api_key: Optional[str] = None
    kagi_search_api_key: Optional[str] = None
    mojeek_search_api_key: Optional[str] = None
    bocha_search_api_key: Optional[str] = None
    serpstack_api_key: Optional[str] = None
    serpstack_https: Optional[bool] = None
    serper_api_key: Optional[str] = None
    serply_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    searchapi_api_key: Optional[str] = None
    searchapi_engine: Optional[str] = None
    serpapi_api_key: Optional[str] = None
    serpapi_engine: Optional[str] = None
    jina_api_key: Optional[str] = None
    bing_search_v7_endpoint: Optional[str] = None
    bing_search_v7_subscription_key: Optional[str] = None
    exa_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    result_count: Optional[int] = None
    concurrent_requests: Optional[int] = None
    trust_env: Optional[bool] = None
    domain_filter_list: Optional[List[str]] = []


class WebConfig(BaseModel):
    search: WebSearchConfig
    ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION: Optional[bool] = None
    BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL: Optional[bool] = None


class ConfigUpdateForm(BaseModel):
    RAG_FULL_CONTEXT: Optional[bool] = None
    BYPASS_EMBEDDING_AND_RETRIEVAL: Optional[bool] = None
    pdf_extract_images: Optional[bool] = None
    enable_google_drive_integration: Optional[bool] = None
    enable_onedrive_integration: Optional[bool] = None
    file: Optional[FileConfig] = None
    content_extraction: Optional[ContentExtractionConfig] = None
    chunk: Optional[ChunkParamUpdateForm] = None
    youtube: Optional[YoutubeLoaderConfig] = None
    web: Optional[WebConfig] = None


@router.post("/config/update")
async def update_rag_config(
    request: Request, form_data: ConfigUpdateForm, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Update various retrieval settings."""
    request.app.state.config.PDF_EXTRACT_IMAGES = (
        form_data.pdf_extract_images
        if form_data.pdf_extract_images is not None
        else request.app.state.config.PDF_EXTRACT_IMAGES
    )

    request.app.state.config.RAG_FULL_CONTEXT = (
        form_data.RAG_FULL_CONTEXT
        if form_data.RAG_FULL_CONTEXT is not None
        else request.app.state.config.RAG_FULL_CONTEXT
    )

    request.app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL = (
        form_data.BYPASS_EMBEDDING_AND_RETRIEVAL
        if form_data.BYPASS_EMBEDDING_AND_RETRIEVAL is not None
        else request.app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL
    )

    request.app.state.config.ENABLE_GOOGLE_DRIVE_INTEGRATION = (
        form_data.enable_google_drive_integration
        if form_data.enable_google_drive_integration is not None
        else request.app.state.config.ENABLE_GOOGLE_DRIVE_INTEGRATION
    )

    request.app.state.config.ENABLE_ONEDRIVE_INTEGRATION = (
        form_data.enable_onedrive_integration
        if form_data.enable_onedrive_integration is not None
        else request.app.state.config.ENABLE_ONEDRIVE_INTEGRATION
    )

    if form_data.file is not None:
        request.app.state.config.FILE_MAX_SIZE = form_data.file.max_size
        request.app.state.config.FILE_MAX_COUNT = form_data.file.max_count

    if form_data.content_extraction is not None:
        log.info(
            f"Updating content extraction: {request.app.state.config.CONTENT_EXTRACTION_ENGINE} to {form_data.content_extraction.engine}"
        )
        request.app.state.config.CONTENT_EXTRACTION_ENGINE = (
            form_data.content_extraction.engine
        )
        request.app.state.config.TIKA_SERVER_URL = (
            form_data.content_extraction.tika_server_url
        )
        request.app.state.config.DOCLING_SERVER_URL = (
            form_data.content_extraction.docling_server_url
        )
        if form_data.content_extraction.document_intelligence_config is not None:
            request.app.state.config.DOCUMENT_INTELLIGENCE_ENDPOINT = (
                form_data.content_extraction.document_intelligence_config.endpoint
            )
            request.app.state.config.DOCUMENT_INTELLIGENCE_KEY = (
                form_data.content_extraction.document_intelligence_config.key
            )

    if form_data.chunk is not None:
        request.app.state.config.TEXT_SPLITTER = form_data.chunk.text_splitter
        request.app.state.config.CHUNK_SIZE = form_data.chunk.chunk_size
        request.app.state.config.CHUNK_OVERLAP = form_data.chunk.chunk_overlap

    if form_data.youtube is not None:
        request.app.state.config.YOUTUBE_LOADER_LANGUAGE = form_data.youtube.language
        request.app.state.config.YOUTUBE_LOADER_PROXY_URL = form_data.youtube.proxy_url
        request.app.state.YOUTUBE_LOADER_TRANSLATION = form_data.youtube.translation

    if form_data.web is not None:
        request.app.state.config.ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION = (
            # Note: When UI "Bypass SSL verification for Websites"=True then ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION=False
            form_data.web.ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION
        )

        request.app.state.config.ENABLE_RAG_WEB_SEARCH = form_data.web.search.enabled
        request.app.state.config.RAG_WEB_SEARCH_ENGINE = form_data.web.search.engine

        request.app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL = (
            form_data.web.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL
        )

        request.app.state.config.SEARXNG_QUERY_URL = (
            form_data.web.search.searxng_query_url
        )
        request.app.state.config.GOOGLE_PSE_API_KEY = (
            form_data.web.search.google_pse_api_key
        )
        request.app.state.config.GOOGLE_PSE_ENGINE_ID = (
            form_data.web.search.google_pse_engine_id
        )
        request.app.state.config.BRAVE_SEARCH_API_KEY = (
            form_data.web.search.brave_search_api_key
        )
        request.app.state.config.KAGI_SEARCH_API_KEY = (
            form_data.web.search.kagi_search_api_key
        )
        request.app.state.config.MOJEEK_SEARCH_API_KEY = (
            form_data.web.search.mojeek_search_api_key
        )
        request.app.state.config.BOCHA_SEARCH_API_KEY = (
            form_data.web.search.bocha_search_api_key
        )
        request.app.state.config.SERPSTACK_API_KEY = (
            form_data.web.search.serpstack_api_key
        )
        request.app.state.config.SERPSTACK_HTTPS = form_data.web.search.serpstack_https
        request.app.state.config.SERPER_API_KEY = form_data.web.search.serper_api_key
        request.app.state.config.SERPLY_API_KEY = form_data.web.search.serply_api_key
        request.app.state.config.TAVILY_API_KEY = form_data.web.search.tavily_api_key
        request.app.state.config.SEARCHAPI_API_KEY = (
            form_data.web.search.searchapi_api_key
        )
        request.app.state.config.SEARCHAPI_ENGINE = (
            form_data.web.search.searchapi_engine
        )

        request.app.state.config.SERPAPI_API_KEY = form_data.web.search.serpapi_api_key
        request.app.state.config.SERPAPI_ENGINE = form_data.web.search.serpapi_engine

        request.app.state.config.JINA_API_KEY = form_data.web.search.jina_api_key
        request.app.state.config.BING_SEARCH_V7_ENDPOINT = (
            form_data.web.search.bing_search_v7_endpoint
        )
        request.app.state.config.BING_SEARCH_V7_SUBSCRIPTION_KEY = (
            form_data.web.search.bing_search_v7_subscription_key
        )

        request.app.state.config.EXA_API_KEY = form_data.web.search.exa_api_key

        request.app.state.config.PERPLEXITY_API_KEY = (
            form_data.web.search.perplexity_api_key
        )

        request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT = (
            form_data.web.search.result_count
        )
        request.app.state.config.RAG_WEB_SEARCH_CONCURRENT_REQUESTS = (
            form_data.web.search.concurrent_requests
        )
        request.app.state.config.RAG_WEB_SEARCH_TRUST_ENV = (
            form_data.web.search.trust_env
        )
        request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST = (
            form_data.web.search.domain_filter_list
        )
    log.info(
        "RAG config updated",
        extra={
            "admin_activity": True,
            "admin_email": user.email,
            "action": "update_rag_config",
            "payload": form_data.model_dump(),
        },
    )
    return {
        "status": True,
        "pdf_extract_images": request.app.state.config.PDF_EXTRACT_IMAGES,
        "RAG_FULL_CONTEXT": request.app.state.config.RAG_FULL_CONTEXT,
        "BYPASS_EMBEDDING_AND_RETRIEVAL": request.app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL,
        "file": {
            "max_size": request.app.state.config.FILE_MAX_SIZE,
            "max_count": request.app.state.config.FILE_MAX_COUNT,
        },
        "content_extraction": {
            "engine": request.app.state.config.CONTENT_EXTRACTION_ENGINE,
            "tika_server_url": request.app.state.config.TIKA_SERVER_URL,
            "docling_server_url": request.app.state.config.DOCLING_SERVER_URL,
            "document_intelligence_config": {
                "endpoint": request.app.state.config.DOCUMENT_INTELLIGENCE_ENDPOINT,
                "key": request.app.state.config.DOCUMENT_INTELLIGENCE_KEY,
            },
        },
        "chunk": {
            "text_splitter": request.app.state.config.TEXT_SPLITTER,
            "chunk_size": request.app.state.config.CHUNK_SIZE,
            "chunk_overlap": request.app.state.config.CHUNK_OVERLAP,
        },
        "youtube": {
            "language": request.app.state.config.YOUTUBE_LOADER_LANGUAGE,
            "proxy_url": request.app.state.config.YOUTUBE_LOADER_PROXY_URL,
            "translation": request.app.state.YOUTUBE_LOADER_TRANSLATION,
        },
        "web": {
            "ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION": request.app.state.config.ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION,
            "BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL": request.app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL,
            "search": {
                "enabled": request.app.state.config.ENABLE_RAG_WEB_SEARCH,
                "engine": request.app.state.config.RAG_WEB_SEARCH_ENGINE,
                "searxng_query_url": request.app.state.config.SEARXNG_QUERY_URL,
                "google_pse_api_key": request.app.state.config.GOOGLE_PSE_API_KEY,
                "google_pse_engine_id": request.app.state.config.GOOGLE_PSE_ENGINE_ID,
                "brave_search_api_key": request.app.state.config.BRAVE_SEARCH_API_KEY,
                "kagi_search_api_key": request.app.state.config.KAGI_SEARCH_API_KEY,
                "mojeek_search_api_key": request.app.state.config.MOJEEK_SEARCH_API_KEY,
                "bocha_search_api_key": request.app.state.config.BOCHA_SEARCH_API_KEY,
                "serpstack_api_key": request.app.state.config.SERPSTACK_API_KEY,
                "serpstack_https": request.app.state.config.SERPSTACK_HTTPS,
                "serper_api_key": request.app.state.config.SERPER_API_KEY,
                "serply_api_key": request.app.state.config.SERPLY_API_KEY,
                "serachapi_api_key": request.app.state.config.SEARCHAPI_API_KEY,
                "searchapi_engine": request.app.state.config.SEARCHAPI_ENGINE,
                "serpapi_api_key": request.app.state.config.SERPAPI_API_KEY,
                "serpapi_engine": request.app.state.config.SERPAPI_ENGINE,
                "tavily_api_key": request.app.state.config.TAVILY_API_KEY,
                "jina_api_key": request.app.state.config.JINA_API_KEY,
                "bing_search_v7_endpoint": request.app.state.config.BING_SEARCH_V7_ENDPOINT,
                "bing_search_v7_subscription_key": request.app.state.config.BING_SEARCH_V7_SUBSCRIPTION_KEY,
                "exa_api_key": request.app.state.config.EXA_API_KEY,
                "perplexity_api_key": request.app.state.config.PERPLEXITY_API_KEY,
                "result_count": request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                "concurrent_requests": request.app.state.config.RAG_WEB_SEARCH_CONCURRENT_REQUESTS,
                "trust_env": request.app.state.config.RAG_WEB_SEARCH_TRUST_ENV,
                "domain_filter_list": request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            },
        },
    }


@router.get("/template")
async def get_rag_template(
    request: Request, user=Depends(get_verified_user)
) -> Dict[str, Any]:
    """Return the prompt template used for retrieval."""
    return {
        "status": True,
        "template": request.app.state.config.RAG_TEMPLATE,
    }


@router.get("/query/settings")
async def get_query_settings(
    request: Request, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Return retrieval query tuning parameters."""
    return {
        "status": True,
        "template": request.app.state.config.RAG_TEMPLATE,
        "k": request.app.state.config.TOP_K,
        "k_reranker": request.app.state.config.TOP_K_RERANKER,
        "r": request.app.state.config.RELEVANCE_THRESHOLD,
        "hybrid": request.app.state.config.ENABLE_RAG_HYBRID_SEARCH,
    }


class QuerySettingsForm(BaseModel):
    k: Optional[int] = None
    k_reranker: Optional[int] = None
    r: Optional[float] = None
    template: Optional[str] = None
    hybrid: Optional[bool] = None


@router.post("/query/settings/update")
async def update_query_settings(
    request: Request, form_data: QuerySettingsForm, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Update query parameters like top-k and template."""
    request.app.state.config.RAG_TEMPLATE = form_data.template
    request.app.state.config.TOP_K = form_data.k if form_data.k else 4
    request.app.state.config.TOP_K_RERANKER = form_data.k_reranker or 4
    request.app.state.config.RELEVANCE_THRESHOLD = form_data.r if form_data.r else 0.0

    request.app.state.config.ENABLE_RAG_HYBRID_SEARCH = (
        form_data.hybrid if form_data.hybrid else False
    )
    log.info(
        "Query settings updated",
        extra={
            "admin_activity": True,
            "admin_email": user.email,
            "action": "update_query_settings",
            "payload": form_data.model_dump(),
        },
    )
    return {
        "status": True,
        "template": request.app.state.config.RAG_TEMPLATE,
        "k": request.app.state.config.TOP_K,
        "k_reranker": request.app.state.config.TOP_K_RERANKER,
        "r": request.app.state.config.RELEVANCE_THRESHOLD,
        "hybrid": request.app.state.config.ENABLE_RAG_HYBRID_SEARCH,
    }


####################################
#
# Document process and retrieval
#
####################################


def save_docs_to_vector_db(
    request: Request,
    docs: Sequence[Document],
    collection_name: str,
    metadata: Optional[Union[Dict[str, Any], Sequence[Dict[str, Any]]]] = None,
    overwrite: bool = False,
    split: bool = True,
    add: bool = False,
    user: Optional[UserModel] = None,
) -> bool:
    """Persist documents to the vector database."""

    def _get_docs_info(docs: list[Document]) -> str:
        docs_info = set()

        # Trying to select relevant metadata identifying the document.
        for doc in docs:
            metadata = getattr(doc, "metadata", {})
            doc_name = metadata.get("name", "")
            if not doc_name:
                doc_name = metadata.get("title", "")
            if not doc_name:
                doc_name = metadata.get("source", "")
            if doc_name:
                docs_info.add(doc_name)

        return ", ".join(docs_info)

    log.debug(
        f"save_docs_to_vector_db: document {_get_docs_info(docs)} {collection_name}"
    )
    log.info(f"save_docs_to_vector_db {collection_name}")

    metadata_list: Optional[List[dict]] = None
    if metadata and isinstance(metadata, Sequence) and not isinstance(metadata, dict):
        metadata_list = list(metadata)
    elif metadata and isinstance(metadata, dict):
        # Check if entries with the same hash (metadata.hash) already exist
        if "hash" in metadata:
            result = VECTOR_DB_CLIENT.query(
                collection_name=collection_name,
                filter={"hash": metadata["hash"]},
            )

            if result is not None:
                existing_doc_ids = result.ids[0]
                if existing_doc_ids:
                    log.debug(f"Document with hash {metadata['hash']} already exists")
                    raise ValueError(ERROR_MESSAGES.DUPLICATE_CONTENT)

    if split:
        if request.app.state.config.TEXT_SPLITTER in ["", "character"]:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=request.app.state.config.CHUNK_SIZE,
                chunk_overlap=request.app.state.config.CHUNK_OVERLAP,
                add_start_index=True,
            )
        elif request.app.state.config.TEXT_SPLITTER == "token":
            log.info(
                f"Using token text splitter: {request.app.state.config.TIKTOKEN_ENCODING_NAME}"
            )

            tiktoken.get_encoding(str(request.app.state.config.TIKTOKEN_ENCODING_NAME))
            text_splitter = TokenTextSplitter(
                encoding_name=str(request.app.state.config.TIKTOKEN_ENCODING_NAME),
                chunk_size=request.app.state.config.CHUNK_SIZE,
                chunk_overlap=request.app.state.config.CHUNK_OVERLAP,
                add_start_index=True,
            )
        else:
            raise ValueError(ERROR_MESSAGES.DEFAULT("Invalid text splitter"))

        # docs = text_splitter.split_documents(docs)
        # ENH MOD : Process each original document separately.
        split_docs = []
        for doc in docs:
            # Determine the header based on metadata.
            header = ""
            if doc.metadata.get("page_label"):
                header = f"# [Page {doc.metadata['page_label']}]:\n\n"
            elif doc.metadata.get("page_number") is not None:
                header = f"# [Page {doc.metadata['page_number'] + 1}]:\n\n"
            elif doc.metadata.get("page") is not None:
                header = f"# [Page {doc.metadata['page'] + 1}]:\n\n"

            # Split the current document into chunks.
            chunks = text_splitter.split_documents([doc])
            for chunk in chunks:
                content = chunk.page_content.strip()
                # If the chunk already begins with the header, remove it to avoid duplication.
                if header and content.startswith(header):
                    content = content[len(header) :].strip()
                # Prepend the header if defined.
                if header:
                    chunk.page_content = header + content
                else:
                    chunk.page_content = content
                split_docs.append(chunk)
                # Log debug output to verify the chunk's header inclusion.
                log.debug(
                    f"Processed chunk (first 200 chars): {chunk.page_content[:200]}"
                )
        docs = split_docs

    if len(docs) == 0:
        raise ValueError(ERROR_MESSAGES.EMPTY_CONTENT)

    texts = [doc.page_content for doc in docs]
    metadatas = []
    if metadata_list is not None:
        if len(metadata_list) != len(docs):
            raise ValueError(ERROR_MESSAGES.DEFAULT("Metadata length mismatch"))
        for doc, meta in zip(docs, metadata_list):
            combined_meta = {**doc.metadata, **meta}
            combined_meta = {k: v for k, v in combined_meta.items() if v is not None}
            combined_meta["embedding_config"] = json.dumps(
                {
                    "engine": request.app.state.config.RAG_EMBEDDING_ENGINE,
                    "model": request.app.state.config.RAG_EMBEDDING_MODEL,
                }
            )
            metadatas.append(combined_meta)
    else:
        for doc in docs:
            combined_meta = {**doc.metadata, **(metadata if metadata else {})}
            combined_meta = {k: v for k, v in combined_meta.items() if v is not None}
            combined_meta["embedding_config"] = json.dumps(
                {
                    "engine": request.app.state.config.RAG_EMBEDDING_ENGINE,
                    "model": request.app.state.config.RAG_EMBEDDING_MODEL,
                }
            )
            metadatas.append(combined_meta)

    # ChromaDB does not like datetime formats
    # for meta-data so convert them to string.
    for metadata in metadatas:
        for key, value in metadata.items():
            if (
                isinstance(value, datetime)
                or isinstance(value, list)
                or isinstance(value, dict)
            ):
                metadata[key] = str(value)

    try:
        if VECTOR_DB_CLIENT.has_collection(collection_name=collection_name):
            log.info(f"collection {collection_name} already exists")

            if overwrite:
                VECTOR_DB_CLIENT.delete_collection(collection_name=collection_name)
                log.info(f"deleting existing collection {collection_name}")
            elif add is False:
                log.info(
                    f"collection {collection_name} already exists, overwrite is False and add is False"
                )
                return True

        log.info(f"adding to collection {collection_name}")
        embedding_function = get_embedding_function(
            request.app.state.config.RAG_EMBEDDING_ENGINE,
            request.app.state.config.RAG_EMBEDDING_MODEL,
            request.app.state.ef,
            (
                request.app.state.config.RAG_OPENAI_API_BASE_URL
                if request.app.state.config.RAG_EMBEDDING_ENGINE == "openai"
                else request.app.state.config.RAG_OLLAMA_BASE_URL
            ),
            (
                request.app.state.config.RAG_OPENAI_API_KEY
                if request.app.state.config.RAG_EMBEDDING_ENGINE == "openai"
                else request.app.state.config.RAG_OLLAMA_API_KEY
            ),
            request.app.state.config.RAG_EMBEDDING_BATCH_SIZE,
        )

        embeddings = embedding_function(
            list(map(lambda x: x.replace("\n", " "), texts)),
            prefix=RAG_EMBEDDING_CONTENT_PREFIX,
            user=user,
        )

        items = [
            {
                "id": str(uuid.uuid4()),
                "text": text,
                "vector": embeddings[idx],
                "metadata": metadatas[idx],
            }
            for idx, text in enumerate(texts)
        ]
        """
        MOD: AMER-HOTFIX-1: Addressing vectordb Load performance issue
        with batch processing        
        """
        batch_size = get_dynamic_batch_size()
        log.info(f"Using dynamic batch size: {batch_size}")

        # ENH ASYNC-IMPROVEMENT   Batch insert synchronously
        batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
        max_workers = min(4, len(batches)) if batches else 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_safe_insert, collection_name, batch)
                for batch in batches
            ]
            for future in as_completed(futures):
                future.result()

        """
        MOD: AMER-HOTFIX-1: End    of Mod    
        """
        return True
    except Exception as e:
        log.exception(e)
        raise e


class ProcessFileForm(BaseModel):
    file_id: str
    content: Optional[str] = None
    collection_name: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/process/file")
def process_file(
    request: Request,
    form_data: ProcessFileForm,
    user: UserModel = Depends(get_verified_user),
) -> Dict[str, Any]:
    """Process a single file and update its associated vector embeddings.

    Args:
        request (Request): The incoming request instance.
        form_data (ProcessFileForm): Parameters for file processing, including
            file identifier, optional content, and target collection.
        user (UserModel): The authenticated user performing the operation.

    Returns:
        dict: Result details containing status, collection name, filename, and content.
    """
    try:
        file = Files.get_file_by_id(form_data.file_id)

        collection_name = form_data.collection_name

        if collection_name is None:
            collection_name = build_user_collection_name(user.id)

        log.info("Updating collection %s for file %s", collection_name, file.id)

        if form_data.content:
            # Update the content in the file
            # Usage: /files/{file_id}/data/content/update

            try:
                # /files/{file_id}/data/content/update
                VECTOR_DB_CLIENT.delete(
                    collection_name=build_user_collection_name(user.id),
                    filter={"file_id": file.id},
                )
            except Exception:
                # Audio file upload pipeline
                pass

            docs = [
                Document(
                    page_content=form_data.content.replace("<br/>", "\n"),
                    metadata={
                        **file.meta,
                        "name": file.filename,
                        "created_by": file.user_id,
                        "file_id": file.id,
                        "source": file.filename,
                        **(
                            {"session_id": form_data.session_id}
                            if form_data.session_id
                            else {}
                        ),
                    },
                )
            ]

            text_content = form_data.content
        elif form_data.collection_name:
            # Check if the file has already been processed and save the content
            # Usage: /knowledge/{id}/file/add, /knowledge/{id}/file/update

            result = VECTOR_DB_CLIENT.query(
                collection_name=build_user_collection_name(user.id),
                filter={"file_id": file.id},
            )

            if result is not None and len(result.ids[0]) > 0:
                docs = [
                    Document(
                        page_content=result.documents[0][idx],
                        metadata={
                            **result.metadatas[0][idx],
                            **(
                                {"session_id": form_data.session_id}
                                if form_data.session_id
                                else {}
                            ),
                        },
                    )
                    for idx, id in enumerate(result.ids[0])
                ]
            else:
                docs = [
                    Document(
                        page_content=file.data.get("content", ""),
                        metadata={
                            **file.meta,
                            "name": file.filename,
                            "created_by": file.user_id,
                            "file_id": file.id,
                            "source": file.filename,
                            **(
                                {"session_id": form_data.session_id}
                                if form_data.session_id
                                else {}
                            ),
                        },
                    )
                ]

            text_content = file.data.get("content", "")
        else:
            # Process the file and save the content
            # Usage: /files/
            file_path = file.path
            if file_path:
                file_path = Storage.get_file(file_path)
                loader = Loader(
                    engine=request.app.state.config.CONTENT_EXTRACTION_ENGINE,
                    TIKA_SERVER_URL=request.app.state.config.TIKA_SERVER_URL,
                    DOCLING_SERVER_URL=request.app.state.config.DOCLING_SERVER_URL,
                    PDF_EXTRACT_IMAGES=request.app.state.config.PDF_EXTRACT_IMAGES,
                    DOCUMENT_INTELLIGENCE_ENDPOINT=request.app.state.config.DOCUMENT_INTELLIGENCE_ENDPOINT,
                    DOCUMENT_INTELLIGENCE_KEY=request.app.state.config.DOCUMENT_INTELLIGENCE_KEY,
                )
                docs = loader.load(
                    file.filename, file.meta.get("content_type"), file_path
                )

                docs = [
                    Document(
                        page_content=doc.page_content,
                        metadata={
                            **doc.metadata,
                            "name": file.filename,
                            "created_by": file.user_id,
                            "file_id": file.id,
                            "source": file.filename,
                            **(
                                {"session_id": form_data.session_id}
                                if form_data.session_id
                                else {}
                            ),
                        },
                    )
                    for doc in docs
                ]
            else:
                docs = [
                    Document(
                        page_content=file.data.get("content", ""),
                        metadata={
                            **file.meta,
                            "name": file.filename,
                            "created_by": file.user_id,
                            "file_id": file.id,
                            "source": file.filename,
                            **(
                                {"session_id": form_data.session_id}
                                if form_data.session_id
                                else {}
                            ),
                        },
                    )
                ]
            text_content = " ".join([doc.page_content for doc in docs])

        log.debug(f"text_content: {text_content}")
        Files.update_file_data_by_id(
            file.id,
            {"content": text_content},
        )

        hash = calculate_sha256_string(text_content)
        Files.update_file_hash_by_id(file.id, hash)

        if not request.app.state.config.BYPASS_EMBEDDING_AND_RETRIEVAL:
            try:
                result = save_docs_to_vector_db(
                    request,
                    docs=docs,
                    collection_name=collection_name,
                    metadata={
                        "file_id": file.id,
                        "name": file.filename,
                        "hash": hash,
                        **(
                            {"session_id": form_data.session_id}
                            if form_data.session_id
                            else {}
                        ),
                    },
                    add=(True if form_data.collection_name else False),
                    user=user,
                )

                if result:
                    Files.update_file_metadata_by_id(
                        file.id,
                        {
                            "collection_name": collection_name,
                        },
                    )

                    return {
                        "status": True,
                        "collection_name": collection_name,
                        "filename": file.filename,
                        "content": text_content,
                    }
            except Exception as e:
                raise e
        else:
            return {
                "status": True,
                "collection_name": None,
                "filename": file.filename,
                "content": text_content,
            }

    except Exception as e:
        log.exception(e)
        if "No pandoc was found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.PANDOC_NOT_INSTALLED,
            )
        else:
            # MOD TAG CWE-209 Generation of Error Message Containing Sensitive Information
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=getErrorMsg(e),
            )


class ProcessTextForm(BaseModel):
    name: str
    content: str
    collection_name: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/process/text")
def process_text(
    request: Request,
    form_data: ProcessTextForm,
    user=Depends(get_verified_user),
) -> Dict[str, Any]:
    """Embed provided text into the user's collection."""
    collection_name = (
        form_data.collection_name
        if form_data.collection_name
        else build_user_collection_name(user.id)
    )

    docs = [
        Document(
            page_content=form_data.content,
            metadata={
                "name": form_data.name,
                "created_by": user.id,
                **(
                    {"session_id": form_data.session_id} if form_data.session_id else {}
                ),
            },
        )
    ]
    text_content = form_data.content
    log.debug(f"text_content: {text_content}")

    result = save_docs_to_vector_db(request, docs, collection_name, user=user)
    if result:
        return {
            "status": True,
            "collection_name": collection_name,
            "content": text_content,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(),
        )


@router.post("/process/youtube")
def process_youtube_video(
    request: Request, form_data: ProcessUrlForm, user=Depends(get_verified_user)
) -> Dict[str, Any]:
    """Process a YouTube video and store its transcript."""
    try:
        collection_name = form_data.collection_name
        if not collection_name:
            collection_name = build_user_collection_name(user.id)

        loader = YoutubeLoader(
            form_data.url,
            language=request.app.state.config.YOUTUBE_LOADER_LANGUAGE,
            proxy_url=request.app.state.config.YOUTUBE_LOADER_PROXY_URL,
        )

        docs = loader.load()
        if form_data.session_id:
            for doc in docs:
                doc.metadata["session_id"] = form_data.session_id
        content = " ".join([doc.page_content for doc in docs])
        log.debug(f"text_content: {content}")

        save_docs_to_vector_db(
            request, docs, collection_name, overwrite=True, user=user
        )

        return {
            "status": True,
            "collection_name": collection_name,
            "filename": form_data.url,
            "file": {
                "data": {
                    "content": content,
                },
                "meta": {
                    "name": form_data.url,
                    **(
                        {"session_id": form_data.session_id}
                        if form_data.session_id
                        else {}
                    ),
                },
            },
        }
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


@router.post("/process/web")
def process_web(
    request: Request, form_data: ProcessUrlForm, user=Depends(get_verified_user)
) -> Dict[str, Any]:
    """Fetch web content and optionally index it."""
    try:
        collection_name = form_data.collection_name
        if not collection_name:
            collection_name = build_user_collection_name(user.id)

        loader = get_web_loader(
            form_data.url,
            verify_ssl=request.app.state.config.ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION,
            requests_per_second=request.app.state.config.RAG_WEB_SEARCH_CONCURRENT_REQUESTS,
        )
        docs = loader.load()
        if form_data.session_id:
            for doc in docs:
                doc.metadata["session_id"] = form_data.session_id
        content = " ".join([doc.page_content for doc in docs])

        log.debug(f"text_content: {content}")

        if not request.app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL:
            save_docs_to_vector_db(
                request, docs, collection_name, overwrite=True, user=user
            )
        else:
            collection_name = None

        return {
            "status": True,
            "collection_name": collection_name,
            "filename": form_data.url,
            "file": {
                "data": {
                    "content": content,
                },
                "meta": {
                    "name": form_data.url,
                    "source": form_data.url,
                    **(
                        {"session_id": form_data.session_id}
                        if form_data.session_id
                        else {}
                    ),
                },
            },
        }
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


def search_web(request: Request, engine: str, query: str) -> list[SearchResult]:
    """Search the web using a search engine and return the results as a list of SearchResult objects.
    Will look for a search engine API key in environment variables in the following order:
    - SEARXNG_QUERY_URL
    - GOOGLE_PSE_API_KEY + GOOGLE_PSE_ENGINE_ID
    - BRAVE_SEARCH_API_KEY
    - KAGI_SEARCH_API_KEY
    - MOJEEK_SEARCH_API_KEY
    - BOCHA_SEARCH_API_KEY
    - SERPSTACK_API_KEY
    - SERPER_API_KEY
    - SERPLY_API_KEY
    - TAVILY_API_KEY
    - EXA_API_KEY
    - PERPLEXITY_API_KEY
    - SEARCHAPI_API_KEY + SEARCHAPI_ENGINE (by default `google`)
    - SERPAPI_API_KEY + SERPAPI_ENGINE (by default `google`)
    Args:
        query (str): The query to search for
    """

    # TODO: add playwright to search the web
    if engine == "searxng":
        if request.app.state.config.SEARXNG_QUERY_URL:
            return search_searxng(
                request.app.state.config.SEARXNG_QUERY_URL,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No SEARXNG_QUERY_URL found in environment variables")
    elif engine == "google_pse":
        if (
            request.app.state.config.GOOGLE_PSE_API_KEY
            and request.app.state.config.GOOGLE_PSE_ENGINE_ID
        ):
            return search_google_pse(
                request.app.state.config.GOOGLE_PSE_API_KEY,
                request.app.state.config.GOOGLE_PSE_ENGINE_ID,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception(
                "No GOOGLE_PSE_API_KEY or GOOGLE_PSE_ENGINE_ID found in environment variables"
            )
    elif engine == "brave":
        if request.app.state.config.BRAVE_SEARCH_API_KEY:
            return search_brave(
                request.app.state.config.BRAVE_SEARCH_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No BRAVE_SEARCH_API_KEY found in environment variables")
    elif engine == "kagi":
        if request.app.state.config.KAGI_SEARCH_API_KEY:
            return search_kagi(
                request.app.state.config.KAGI_SEARCH_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No KAGI_SEARCH_API_KEY found in environment variables")
    elif engine == "mojeek":
        if request.app.state.config.MOJEEK_SEARCH_API_KEY:
            return search_mojeek(
                request.app.state.config.MOJEEK_SEARCH_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No MOJEEK_SEARCH_API_KEY found in environment variables")
    elif engine == "bocha":
        if request.app.state.config.BOCHA_SEARCH_API_KEY:
            return search_bocha(
                request.app.state.config.BOCHA_SEARCH_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No BOCHA_SEARCH_API_KEY found in environment variables")
    elif engine == "serpstack":
        if request.app.state.config.SERPSTACK_API_KEY:
            return search_serpstack(
                request.app.state.config.SERPSTACK_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
                https_enabled=request.app.state.config.SERPSTACK_HTTPS,
            )
        else:
            raise Exception("No SERPSTACK_API_KEY found in environment variables")
    elif engine == "serper":
        if request.app.state.config.SERPER_API_KEY:
            return search_serper(
                request.app.state.config.SERPER_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No SERPER_API_KEY found in environment variables")
    elif engine == "serply":
        if request.app.state.config.SERPLY_API_KEY:
            return search_serply(
                request.app.state.config.SERPLY_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No SERPLY_API_KEY found in environment variables")
    elif engine == "duckduckgo":
        return search_duckduckgo(
            query,
            request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
            request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
        )
    elif engine == "tavily":
        if request.app.state.config.TAVILY_API_KEY:
            return search_tavily(
                request.app.state.config.TAVILY_API_KEY,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No TAVILY_API_KEY found in environment variables")
    elif engine == "searchapi":
        if request.app.state.config.SEARCHAPI_API_KEY:
            return search_searchapi(
                request.app.state.config.SEARCHAPI_API_KEY,
                request.app.state.config.SEARCHAPI_ENGINE,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No SEARCHAPI_API_KEY found in environment variables")
    elif engine == "serpapi":
        if request.app.state.config.SERPAPI_API_KEY:
            return search_serpapi(
                request.app.state.config.SERPAPI_API_KEY,
                request.app.state.config.SERPAPI_ENGINE,
                query,
                request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
                request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
            )
        else:
            raise Exception("No SERPAPI_API_KEY found in environment variables")
    elif engine == "jina":
        return search_jina(
            request.app.state.config.JINA_API_KEY,
            query,
            request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
        )
    elif engine == "bing":
        return search_bing(
            request.app.state.config.BING_SEARCH_V7_SUBSCRIPTION_KEY,
            request.app.state.config.BING_SEARCH_V7_ENDPOINT,
            str(DEFAULT_LOCALE),
            query,
            request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
            request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
        )
    elif engine == "exa":
        return search_exa(
            request.app.state.config.EXA_API_KEY,
            query,
            request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
            request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
        )
    elif engine == "perplexity":
        return search_perplexity(
            request.app.state.config.PERPLEXITY_API_KEY,
            query,
            request.app.state.config.RAG_WEB_SEARCH_RESULT_COUNT,
            request.app.state.config.RAG_WEB_SEARCH_DOMAIN_FILTER_LIST,
        )
    else:
        raise Exception("No search engine API key found in environment variables")


@router.post("/process/web/search")
async def process_web_search(
    request: Request, form_data: SearchForm, user=Depends(get_verified_user)
) -> Dict[str, Any]:
    """Search the web and index retrieved pages."""
    try:
        logging.info(
            f"trying to web search with {request.app.state.config.RAG_WEB_SEARCH_ENGINE, form_data.query}"
        )
        web_results = search_web(
            request, request.app.state.config.RAG_WEB_SEARCH_ENGINE, form_data.query
        )
    except GooglePSEError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google PSE credentials",
        )
    except Exception as e:
        log.exception(e)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.WEB_SEARCH_ERROR(e),
        )

    log.debug(f"web_results: {web_results}")

    try:
        collection_name = form_data.collection_name
        if not collection_name:
            collection_name = build_user_collection_name(user.id)

        urls = [result.link for result in web_results]
        loader = get_web_loader(
            urls,
            verify_ssl=request.app.state.config.ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION,
            requests_per_second=request.app.state.config.RAG_WEB_SEARCH_CONCURRENT_REQUESTS,
            trust_env=request.app.state.config.RAG_WEB_SEARCH_TRUST_ENV,
        )
        docs = await loader.aload()
        if form_data.session_id:
            for doc in docs:
                doc.metadata["session_id"] = form_data.session_id

        if request.app.state.config.BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL:
            return {
                "status": True,
                "collection_name": None,
                "filenames": urls,
                "docs": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                    for doc in docs
                ],
                "loaded_count": len(docs),
            }
        else:
            await run_in_threadpool(
                save_docs_to_vector_db,
                request,
                docs,
                collection_name,
                overwrite=True,
                user=user,
            )

            return {
                "status": True,
                "collection_name": collection_name,
                "filenames": urls,
                "loaded_count": len(docs),
            }
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


class QueryDocForm(BaseModel):
    collection_name: str
    query: str
    k: Optional[int] = None
    k_reranker: Optional[int] = None
    r: Optional[float] = None
    hybrid: Optional[bool] = None
    filter: Optional[dict] = None
    filter_expr: Optional[str] = None


@router.post("/query/doc")
def query_doc_handler(
    request: Request,
    form_data: QueryDocForm,
    user=Depends(get_verified_user),
) -> Dict[str, Any]:
    """Query a single collection for relevant documents."""
    try:
        if request.app.state.config.ENABLE_RAG_HYBRID_SEARCH:
            return query_doc_with_hybrid_search(
                collection_name=form_data.collection_name,
                query=form_data.query,
                embedding_function=lambda query, prefix: request.app.state.EMBEDDING_FUNCTION(
                    query, prefix=prefix, user=user
                ),
                k=form_data.k if form_data.k else request.app.state.config.TOP_K,
                reranking_function=request.app.state.rf,
                k_reranker=form_data.k_reranker
                or request.app.state.config.TOP_K_RERANKER,
                r=(
                    form_data.r
                    if form_data.r
                    else request.app.state.config.RELEVANCE_THRESHOLD
                ),
                query_filter=form_data.filter,
                filter_expr=form_data.filter_expr,
                user=user,
            )
        else:
            return query_doc(
                collection_name=form_data.collection_name,
                query_embedding=request.app.state.EMBEDDING_FUNCTION(
                    form_data.query, prefix=RAG_EMBEDDING_QUERY_PREFIX, user=user
                ),
                k=form_data.k if form_data.k else request.app.state.config.TOP_K,
                query_filter=form_data.filter,
                filter_expr=form_data.filter_expr,
                user=user,
            )
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


class QueryCollectionForm(BaseModel):
    collection_name: str
    query: str
    filters: Optional[list[dict]] = None  ## MOD: RAG-FILTERS: optional metadata filters
    k: Optional[int] = None
    k_reranker: Optional[int] = None
    r: Optional[float] = None
    hybrid: Optional[bool] = None


@router.post("/query/collection")
def query_collection_handler(
    request: Request,
    form_data: QueryCollectionForm,
    user=Depends(get_verified_user),
) -> Dict[str, Any]:
    """Query multiple documents within a collection."""
    try:
        if request.app.state.config.ENABLE_RAG_HYBRID_SEARCH:
            return query_collection_with_hybrid_search(
                collection_name=form_data.collection_name,
                queries=[form_data.query],
                embedding_function=lambda query, prefix: request.app.state.EMBEDDING_FUNCTION(
                    query, prefix=prefix, user=user
                ),
                k=form_data.k if form_data.k else request.app.state.config.TOP_K,
                reranking_function=request.app.state.rf,
                k_reranker=form_data.k_reranker
                or request.app.state.config.TOP_K_RERANKER,
                r=(
                    form_data.r
                    if form_data.r
                    else request.app.state.config.RELEVANCE_THRESHOLD
                ),
                query_filters=form_data.filters,  ## MOD: RAG-FILTERS
            )
        else:
            return query_collection(
                collection_name=form_data.collection_name,
                queries=[form_data.query],
                embedding_function=lambda query, prefix: request.app.state.EMBEDDING_FUNCTION(
                    query, prefix=prefix, user=user
                ),
                k=form_data.k if form_data.k else request.app.state.config.TOP_K,
                query_filters=form_data.filters,  ## MOD: RAG-FILTERS
            )

    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


####################################
#
# Vector DB operations
#
####################################


class DeleteForm(BaseModel):
    collection_name: str
    file_id: str


@router.post("/delete")
def delete_entries_from_collection(
    form_data: DeleteForm, user=Depends(get_admin_user)
) -> Dict[str, Any]:
    """Remove file entries from a collection."""
    try:
        if VECTOR_DB_CLIENT.has_collection(collection_name=form_data.collection_name):
            # Remove only vectors associated with the specified file
            VECTOR_DB_CLIENT.delete(
                collection_name=form_data.collection_name,
                filter={"file_id": form_data.file_id},
            )
            log.info(
                "Vector DB entries deleted",
                extra={
                    "admin_activity": True,
                    "admin_email": user.email,
                    "action": "delete_vector_entries",
                    "payload": form_data.model_dump(),
                },
            )
            return {"status": True}
        else:
            log.info(
                "Vector DB collection not found",
                extra={
                    "admin_activity": True,
                    "admin_email": user.email,
                    "action": "delete_vector_entries",
                    "payload": form_data.model_dump(),
                },
            )
            return {"status": False}
    except Exception as e:
        log.exception(e)
        log.info(
            "Vector DB deletion error",
            extra={
                "admin_activity": True,
                "admin_email": user.email,
                "action": "delete_vector_entries",
                "payload": form_data.model_dump(),
            },
        )
        return {"status": False}


@router.post("/reset/db")
def reset_vector_db(user=Depends(get_admin_user)) -> Dict[str, bool]:
    """Clear the vector database and knowledge records."""
    VECTOR_DB_CLIENT.reset()
    Knowledges.delete_all_knowledge()
    log.info(
        "Vector DB reset",
        extra={
            "admin_activity": True,
            "admin_email": user.email,
            "action": "reset_vector_db",
        },
    )
    return {"status": True}


@router.post("/reset/uploads")
def reset_upload_dir(user=Depends(get_admin_user)) -> bool:
    """Remove all files from the uploads directory."""
    folder = f"{UPLOAD_DIR}"
    try:
        # Check if the directory exists
        if os.path.exists(folder):
            # Iterate over all the files and directories in the specified directory
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Remove the file or link
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove the directory
                except Exception as e:
                    log.exception(f"Failed to delete {file_path}. Reason: {e}")
        else:
            log.warning(f"The directory {folder} does not exist")
        log.info(
            "Upload directory reset",
            extra={
                "admin_activity": True,
                "admin_email": user.email,
                "action": "reset_upload_dir",
            },
        )
        return True
    except Exception as e:
        log.exception(f"Failed to process the directory {folder}. Reason: {e}")
        log.info(
            "Upload directory reset failed",
            extra={
                "admin_activity": True,
                "admin_email": user.email,
                "action": "reset_upload_dir",
            },
        )
        return False


if ENV == "dev":

    @router.get("/ef/{text}")
    async def get_embeddings(
        request: Request, text: Optional[str] = "Hello World!"
    ) -> Dict[str, Any]:
        """Return raw embeddings for debugging."""
        return {
            "result": request.app.state.EMBEDDING_FUNCTION(
                text, prefix=RAG_EMBEDDING_QUERY_PREFIX
            )
        }


class BatchProcessFilesForm(BaseModel):
    files: List[FileModel]
    collection_name: str
    session_id: Optional[str] = None


class BatchProcessFilesResult(BaseModel):
    file_id: str
    status: str
    error: Optional[str] = None


class BatchProcessFilesResponse(BaseModel):
    results: List[BatchProcessFilesResult]
    errors: List[BatchProcessFilesResult]


@router.post("/process/files/batch")
def process_files_batch(
    request: Request,
    form_data: BatchProcessFilesForm,
    user=Depends(get_verified_user),
) -> BatchProcessFilesResponse:
    """Process multiple files and batch-save their documents to the vector DB.

    Args:
        request (Request): The incoming request instance.
        form_data (BatchProcessFilesForm): Uploaded files and target collection.
        user (UserModel): The authenticated user performing the operation.

    Returns:
        BatchProcessFilesResponse: Summary of processing results and errors.
    """
    results: List[BatchProcessFilesResult] = []
    errors: List[BatchProcessFilesResult] = []
    collection_name = (
        form_data.collection_name
        if form_data.collection_name
        else build_user_collection_name(user.id)
    )

    all_docs: List[Document] = []
    all_metadata: List[dict] = []
    processed_count = 0
    skipped_count = 0

    for file in form_data.files:
        try:
            text_content = file.data.get("content", "")
            hash = calculate_sha256_string(text_content)
            Files.update_file_hash_by_id(file.id, hash)
            Files.update_file_data_by_id(file.id, {"content": text_content})

            # Check for duplicate content
            is_duplicate = False
            try:
                existing = VECTOR_DB_CLIENT.query(
                    collection_name=collection_name, filter={"hash": hash}
                )
                if existing is not None and existing.ids[0]:
                    is_duplicate = True
            except Exception as e:
                log.error(
                    f"process_files_batch: Error checking duplicate for {file.id}: {str(e)}"
                )

            if is_duplicate:
                skipped_count += 1
                log.info(f"process_files_batch: Skipping duplicate file {file.id}")
                results.append(
                    BatchProcessFilesResult(file_id=file.id, status="skipped_duplicate")
                )
                continue

            doc_type = (file.meta.get("doc_type") if file.meta else None) or (
                file.meta.get("content_type") if file.meta else None
            )
            if not doc_type:
                doc_type = mimetypes.guess_type(file.filename)[0]

            docs: List[Document] = [
                Document(
                    page_content=text_content.replace("<br/>", "\n"),
                    metadata={
                        **file.meta,
                        "name": file.filename,
                        "created_by": file.user_id,
                        "file_id": file.id,
                        "source": file.filename,
                        **(
                            {"session_id": form_data.session_id}
                            if form_data.session_id
                            else {}
                        ),
                    },
                )
            ]

            metadata = {
                "file_id": file.id,
                "name": file.filename,
                "hash": hash,
                "doc_type": doc_type,
                **(
                    {"session_id": form_data.session_id} if form_data.session_id else {}
                ),
            }

            all_docs.extend(docs)
            all_metadata.extend([metadata.copy() for _ in docs])
            processed_count += len(docs)
            results.append(BatchProcessFilesResult(file_id=file.id, status="prepared"))

        except Exception as e:
            log.error(f"process_files_batch: Error processing file {file.id}: {str(e)}")
            errors.append(
                BatchProcessFilesResult(
                    file_id=file.id, status="failed", error=getErrorMsg(e)
                )
            )

    if all_docs:
        try:
            save_docs_to_vector_db(
                request=request,
                docs=all_docs,
                collection_name=collection_name,
                metadata=all_metadata,
                add=True,
                user=user,
            )

            for result in results:
                if result.status == "prepared":
                    Files.update_file_metadata_by_id(
                        result.file_id, {"collection_name": collection_name}
                    )
                    result.status = "completed"

        except Exception as e:
            log.error(
                f"process_files_batch: Error saving documents to vector DB: {str(e)}"
            )
            for result in results:
                if result.status == "prepared":
                    result.status = "failed"
                    errors.append(
                        BatchProcessFilesResult(
                            file_id=result.file_id, error=getErrorMsg(e)
                        )
                    )

    log.info(
        "process_files_batch: processed %s document(s), skipped %s duplicates",
        processed_count,
        skipped_count,
    )

    return BatchProcessFilesResponse(results=results, errors=errors)
