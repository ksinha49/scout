#!/usr/bin/env bash
PATH=$PATH:/usr/local/bin/
source /etc/environment


VENV_DIR="chatAmeritas_venv"
USER=$(whoami)  # Current user running the script
VENV_PATH=$(pwd) 
AWS_DEFAULT_REGION=us-east-2

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR" || exit

echo "current dir:" $SCRIPT_DIR
echo "venv dir:"$VENV_PATH/$VENV_DIR/bin/activate


#Step 1: Activate the virtual environment and install requirements
echo "Activating virtual environment"
source $VENV_PATH/$VENV_DIR/bin/activate

if [ -z "$AWS_REGION" ]; then
    echo "Getting AWS region tokens"
    MAX_RETRIES=10
    SLEEP_INTERVAL=5

    for i in $(seq 1 $MAX_RETRIES); do
        # Try to ping metadata service to ensure networking is up
        if curl -s http://169.254.169.254/latest/meta-data/ >/dev/null; then
            break
        else
            echo "Metadata service not available, retrying in $SLEEP_INTERVAL seconds..."
            sleep $SLEEP_INTERVAL
        fi
    done

    TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

    # Use the token to access the metadata service and get AWS_REGION
    AWS_REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/region)
fi

#if no value returned by AWS
if [ -z "$AWS_REGION" ]; then
    export AWS_REGION=$AWS_DEFAULT_REGION
fi
# Step 2: Use the token to access the metadata service
export ENV=$(aws ssm get-parameter --name "/parameters/aio/ameritasAI/SERVER_ENV" --with-decryption --query "Parameter.Value" --output text  --region $AWS_REGION)
echo "Loading Env variables" $ENV

export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64:$LD_LIBRARY_PATH

if [[ "$*" == *"--debug"* ]]; then
    export GLOBAL_LOG_LEVEL="DEBUG"
    export LOG_LVL="debug"
    echo "Debug mode enabled: GLOBAL_LOG_LEVEL is set to Debug"
else
    export GLOBAL_LOG_LEVEL=$(aws ssm get-parameter --name "/parameters/aio/ameritasAI/$ENV/GLOBAL_LOG_LEVEL" --with-decryption --query "Parameter.Value" --output text  --region $AWS_REGION)
    export LOG_LVL="info"
    echo "GLOBAL_LOG_LEVEL is set from parameter store"
fi

# Helper to fetch multiple SSM parameters at once
fetch_params() {
    local result
    result=$(aws ssm get-parameters \
        --names "$@" \
        --with-decryption \
        --region "$AWS_REGION" \
        --output json)

    # Output retrieved name/value pairs as tab-separated lines
    echo "$result" | jq -r '.Parameters[] | [.Name, .Value] | @tsv'

    # Log parameters that were not found without failing
    echo "$result" | jq -r '.InvalidParameters[]?' | while read -r missing; do
        if [ -n "$missing" ]; then
            echo "Warning: SSM parameter not found: $missing" >&2
        fi
    done
}

# Map of SSM parameter names to environment variables
declare -A PARAM_MAP=(
    [AIOHTTP_CLIENT_TIMEOUT]=AIOHTTP_CLIENT_TIMEOUT
    [HTTP_TIMEOUT]=HTTP_TIMEOUT
    [ANONYMIZED_TELEMETRY]=ANONYMIZED_TELEMETRY
    [CORS_ALLOW_ORIGIN]=CORS_ALLOW_ORIGIN
    [CUSTOM_NAME]=CUSTOM_NAME
    [DEFAULT_MODELS]=DEFAULT_MODELS
    [MODEL_FALLBACK_PRIORITIES]=MODEL_FALLBACK_PRIORITIES
    [DEFAULT_USER_ROLE]=DEFAULT_USER_ROLE
    [DO_NOT_TRACK]=DO_NOT_TRACK
    [ENABLE_ADMIN_CHAT_ACCESS]=ENABLE_ADMIN_CHAT_ACCESS
    [ENABLE_ADMIN_EXPORT]=ENABLE_ADMIN_EXPORT
    [ENABLE_CITATION]=ENABLE_CITATION
    [ENABLE_COMMUNITY_SHARING]=ENABLE_COMMUNITY_SHARING
    [ENABLE_LOGIN_FORM]=ENABLE_LOGIN_FORM
    [ENABLE_MESSAGE_RATING]=ENABLE_MESSAGE_RATING
    [ENABLE_MODEL_FILTER]=ENABLE_MODEL_FILTER
    [ENABLE_OAUTH_SIGNUP]=ENABLE_OAUTH_SIGNUP
    [ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION]=ENABLE_RAG_WEB_LOADER_SSL_VERIFICATION
    [ENV]=OPENWEBUI_ENV
    [JWT_EXPIRES_IN]=JWT_EXPIRES_IN
    [MICROSOFT_CLIENT_ID]=MICROSOFT_CLIENT_ID
    [MICROSOFT_CLIENT_SECRET]=MICROSOFT_CLIENT_SECRET
    [MICROSOFT_CLIENT_TENANT_ID]=MICROSOFT_CLIENT_TENANT_ID
    [MICROSOFT_OAUTH_SCOPE]=MICROSOFT_OAUTH_SCOPE
    [MICROSOFT_REDIRECT_URI]=MICROSOFT_REDIRECT_URI
    [OLLAMA_API_BASE_URL]=OLLAMA_API_BASE_URL
    [OLLAMA_BASE_URL]=OLLAMA_BASE_URL
    [POSTGRESQL_ENDPT]=POSTGRESQL_ENDPT
    [POSTGRESQL_PASSCODE]=POSTGRESQL_PASSCODE
    [POSTGRESQL_PORT]=POSTGRESQL_PORT
    [POSTGRESQL_USERID]=POSTGRESQL_USERID
    [SCARF_NO_ANALYTICS]=SCARF_NO_ANALYTICS
    [SHOW_ADMIN_DETAILS]=SHOW_ADMIN_DETAILS
    [STATIC_DIR]=STATIC_DIR
    [USER_PERMISSIONS_CHAT_DELETION]=USER_PERMISSIONS_CHAT_DELETION
    [USER_PERMISSIONS_CHAT_EDITING]=USER_PERMISSIONS_CHAT_EDITING
    [USER_PERMISSIONS_CHAT_TEMPORARY]=USER_PERMISSIONS_CHAT_TEMPORARY
    [WEBUI_NAME]=WEBUI_NAME
    [OLLAMA_SERVER_CERT]=OLLAMA_SERVER_CERT
    [VECTOR_DB]=VECTOR_DB
    [MILVUS_URI]=MILVUS_URI
    [MILVUS_USER]=MILVUS_USER
    [MILVUS_PASSWORD]=MILVUS_PASSWORD
    [MILVUS_DB_NAME]=MILVUS_DB_NAME
    [USE_CUDA]=USE_CUDA_DOCKER
    [BATCH_SIZE]=BATCH_SIZE
    [DPI]=DPI
    [MAX_GPU_RETRIES]=MAX_GPU_RETRIES
    [PYTORCH_CUDA_ALLOC_CONF]=PYTORCH_CUDA_ALLOC_CONF
    [OCR_ENGINE]=OCR_ENGINE
    [STORAGE_PROVIDER]=STORAGE_PROVIDER
    [S3_BUCKET_NAME]=S3_BUCKET_NAME
    [S3_ENDPOINT_URL]=S3_ENDPOINT_URL
    [RAG_INSERT_BATCH_SIZE]=RAG_INSERT_BATCH_SIZE
    [RAG_EMBEDDING_BATCH_SIZE]=RAG_EMBEDDING_BATCH_SIZE
    [IS_CERT_REQ]=IS_CERT_REQ
    [AUTHORIZED_URLS]=AUTHORIZED_URLS
    [CHAT_AMERITAS_FRONT_END_URL]=CHAT_AMERITAS_FRONT_END_URL
    [FILE_PROCESSING_FUNCTIONAL_USER]=FILE_PROCESSING_FUNCTIONAL_USER
    [FUNCTIONAL_USER_ROLE]=FUNCTIONAL_USER_ROLE
    [FILE_TIMEOUT]=FILE_TIMEOUT
    [BEDROCK_SERVER_CERT]=BEDROCK_SERVER_CERT
    [OCR_CONCURRENCY]=OCR_CONCURRENCY
    [OCR_MAX_CONCURRENCY]=OCR_MAX_CONCURRENCY
    [CLEAR_CUDA_CACHE_EACH_PAGE]=CLEAR_CUDA_CACHE_EACH_PAGE
    [OAUTH_MERGE_ACCOUNTS_BY_EMAIL]=OAUTH_MERGE_ACCOUNTS_BY_EMAIL
    [OPENID_PROVIDER_URL]=OPENID_PROVIDER_URL
    [REDIS_URL]=REDIS_URL
    [REDIS_SENTINEL_HOSTS]=REDIS_SENTINEL_HOSTS
    [REDIS_SENTINEL_PORT]=REDIS_SENTINEL_PORT
    [WEBUI_AUTH]=WEBUI_AUTH
    [WEBUI_AUTH_TRUSTED_EMAIL_HEADER]=WEBUI_AUTH_TRUSTED_EMAIL_HEADER
    [WEBUI_AUTH_TRUSTED_NAME_HEADER]=WEBUI_AUTH_TRUSTED_NAME_HEADER
    [ENABLE_OTEL]=ENABLE_OTEL
    [OTEL_EXPORTER_OTLP_ENDPOINT]=OTEL_EXPORTER_OTLP_ENDPOINT
    [OTEL_SERVICE_NAME]=OTEL_SERVICE_NAME
    [OTEL_RESOURCE_ATTRIBUTES]=OTEL_RESOURCE_ATTRIBUTES
    [OTEL_TRACES_SAMPLER]=OTEL_TRACES_SAMPLER
    [UVICORN_WORKERS]=UVICORN_WORKERS
)
# Build full parameter paths using ENV
PARAM_PATHS=()
for key in "${!PARAM_MAP[@]}"; do
    PARAM_PATHS+=("/parameters/aio/ameritasAI/$ENV/$key")
done
# Fetch and export parameters in batches of 10
batch_size=10
for ((i=0; i<${#PARAM_PATHS[@]}; i+=batch_size)); do
    batch=("${PARAM_PATHS[@]:i:batch_size}")
    while read -r name value; do
        param=${name##*/}
        var=${PARAM_MAP[$param]}
        export "$var"="$value"
    done < <(fetch_params "${batch[@]}")
done
# Construct database connection string from retrieved values
export DATABASE_URL="postgresql://${POSTGRESQL_USERID}:${POSTGRESQL_PASSCODE}@${POSTGRESQL_ENDPT}:${POSTGRESQL_PORT}/postgres"

# Additional non-SSM environment variables
export ALLOWED_MODULES_FILE="ALLOWED_MODULES.json"
export SENTENCE_TRANSFORMERS_HOME=$SCRIPT_DIR/data/cache/embedding/models
export XDG_CACHE_HOME=$SCRIPT_DIR/data/cache
export TORCH_HOME=$SCRIPT_DIR/data/cache/torch
export HF_HOME=$SCRIPT_DIR/data/cache/huggingface
export HF_DATASETS_CACHE=$SCRIPT_DIR/data/cache/huggingface/datasets
export TRANSFORMERS_CACHE=$SCRIPT_DIR/data/cache/huggingface
export S3_REGION_NAME="$AWS_REGION"

mkdir -p "$XDG_CACHE_HOME" "$TORCH_HOME" "$HF_HOME" "$HF_DATASETS_CACHE" "$SENTENCE_TRANSFORMERS_HOME"

LOGS_DIR="$SCRIPT_DIR"/logs

export AMERITAS_PROXY_URL="http://$http_proxy"

KEY_FILE=.webui_secret_key
export LOG_CONFIG="$LOGS_DIR"/uvicorn-logconfig.ini

if [ -f "$LOG_CONFIG" ]; then
   rm "$LOG_CONFIG"
fi

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
if test "$WEBUI_SECRET_KEY $WEBUI_JWT_SECRET_KEY" = " "; then
  echo "Loading WEBUI_SECRET_KEY from file, not provided as an environment variable."

  if ! [ -e "$KEY_FILE" ]; then
    echo "Generating WEBUI_SECRET_KEY"
    # Generate a random value to use as a WEBUI_SECRET_KEY in case the user didn't provide one.
    echo $(head -c 12 /dev/random | base64) > "$KEY_FILE"
  fi

  echo "Loading WEBUI_SECRET_KEY from $KEY_FILE"
  WEBUI_SECRET_KEY=$(cat "$KEY_FILE")
fi

if [[ "${USE_OLLAMA_DOCKER,,}" == "true" ]]; then
    echo "USE_OLLAMA is set to true, starting ollama serve."
    ollama serve &
fi

if [[ "${USE_CUDA_DOCKER,,}" == "true" ]]; then
  echo "CUDA is enabled, appending LD_LIBRARY_PATH to include torch/cudnn & cublas libraries."
  export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/python3.11/site-packages/torch/lib:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib"
fi

# Check if SPACE_ID is set, if so, configure for space
if [ -n "$SPACE_ID" ]; then
  echo "Configuring for HuggingFace Space deployment"
  if [ -n "$ADMIN_USER_EMAIL" ] && [ -n "$ADMIN_USER_PASSWORD" ]; then
    echo "Admin user configured, creating"
    WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" uvicorn open_webui.main:app --host "$HOST" --port "$PORT" --forwarded-allow-ips '*' &
    webui_pid=$!
    echo "Waiting for webui to start..."
    while ! curl -s http://localhost:8080/health > /dev/null; do
      sleep 1
    done
    echo "Creating admin user..."
    curl \
      -X POST "http://localhost:8080/api/v1/auths/signup" \
      -H "accept: application/json" \
      -H "Content-Type: application/json" \
      -d "{ \"email\": \"${ADMIN_USER_EMAIL}\", \"password\": \"${ADMIN_USER_PASSWORD}\", \"name\": \"Admin\" }"
    echo "Shutting down webui..."
    kill $webui_pid
  fi

  export WEBUI_URL=${SPACE_HOST}
fi


if [ ! -d "$LOGS_DIR" ]; then
  mkdir -p "$LOGS_DIR"
fi

echo "Starting Scout"

current_date=$(date +"%m_%d_%y")
export LOG_FILENAME="$LOGS_DIR/backendlog_${current_date}.log"
export APP_ERROR_LOG_PATH="$LOGS_DIR/backendlog_error_${current_date}.log"
export APP_ADMIN_ACTIVITY_LOG_PATH="$LOGS_DIR/backendlog_admin_activity_${current_date}.log"
# Set default crash log path if not provided
export GUNICORN_CRASH_LOG_PATH=${GUNICORN_CRASH_LOG_PATH:-"$LOGS_DIR/backendlog_gunicorn_crash_${current_date}.log"}

# Preprocess the log_config_template.yaml to replace placeholders with actual values
sed "s|__GLOBAL_LOG_LEVEL__|$GLOBAL_LOG_LEVEL|g; s|__LOG_FILENAME__|$LOG_FILENAME|g" uvicorn_logconfig_template.ini > "$LOG_CONFIG"

WORKERS="${UVICORN_WORKERS:-1}"
echo "Starting Scout with $WORKERS gunicorn worker(s)"
gunicorn open_webui.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "$HOST:$PORT" \
    --workers "$WORKERS" \
    --log-config "$LOG_CONFIG" \
    --access-logfile - \
    --timeout "${GUNICORN_TIMEOUT:-600}" \
    --log-level "$LOG_LVL" \
    --error-logfile "$GUNICORN_CRASH_LOG_PATH"
