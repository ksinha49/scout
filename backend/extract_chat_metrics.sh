#!/bin/bash
PATH=$PATH:/usr/local/bin/
#=====================================================
# Script Name: extract_chat_metrics.sh
# Description: This script terminates a tmux session
#              if it is running.
# Author: Koushik Sinha
# Date: 9/11/2024
# Version: 1.0
#=====================================================
# Check if the correct number of arguments are provided
if [[ $# -ne 6 ]]; then
  echo "Usage: $0 <output_file> <log_file> <target_loc_prefix>  <target_loc_suffix>  <target_dir> <schema>"
  exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$0")
VENV_DIR="chatAmeritas_venv"
VENV_PATH=$(pwd)

source $VENV_PATH/$VENV_DIR/bin/activate

# Load environment variables (cron runs with limited env)
source /etc/profile
source /etc/environment
export AWS_METADATA_SERVICE_NUM_ATTEMPTS=1
export AWS_METADATA_SERVICE_TIMEOUT=60


# Define full paths to binaries used in the script
AWS_CLI="/usr/local/bin/aws"
PSQL="/usr/bin/psql"

# Delay to allow IAM role association
echo "getting aws creds"
$AWS_CLI configure list
$AWS_CLI sts get-caller-identity

# Get the output and log file from command-line arguments
OUTPUT_FILE_PARAM="$1"
LOG_FILE_PARAM="$2"
TARGET_LOCATION_PREFIX="$3"
TARGET_LOCATION_SUFFIX="$4"
TARGET_DIR="$5"
DB_SCHEMA="$6"

# Default current directory
CURR_DT=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="$OUTPUT_FILE_PARAM"_$CURR_DT.csv   # Set the output file to the current directory
LOG_FILE="$LOG_FILE_PARAM"        # Set the log file to the current directory


TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
# Use the token to access the metadata service and get AWS_REGION
AWS_REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/region)
echo $AWS_REGION
export ENV=$($AWS_CLI ssm get-parameter --name "/parameters/aio/ameritasAI/SERVER_ENV" --with-decryption --query "Parameter.Value" --output text  --region $AWS_REGION)

# Allocate env variables

export RDS_HOST=$($AWS_CLI ssm get-parameter --name "/parameters/aio/ameritasAI/$ENV/POSTGRESQL_ENDPT" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
export DB_PASSWORD=$($AWS_CLI ssm get-parameter --name "/parameters/aio/ameritasAI/$ENV/POSTGRESQL_PASSCODE" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
export DB_PORT=$($AWS_CLI ssm get-parameter --name "/parameters/aio/ameritasAI/$ENV/POSTGRESQL_PORT" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
export DB_USER=$($AWS_CLI ssm get-parameter --name "/parameters/aio/ameritasAI/$ENV/POSTGRESQL_USERID" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
export DB_NAME=postgres

#export DB_SCHEMA=open_webui
DB_TABLE=chat
DB_TABLE2=user


if [[ "$ENV" == "development" ]]; then
  TARGET_ENV="d"
elif [[ "$ENV" == "model" ]]; then
  TARGET_ENV="m"
elif [[ "$ENV" == "production" ]]; then
  TARGET_ENV="p" 
fi

TARGET_LOCATION="${TARGET_LOCATION_PREFIX}-${TARGET_ENV}-${TARGET_LOCATION_SUFFIX}"

echo $TARGET_LOCATION

# Function to log messages
log_message()
{  
   echo "$(date '+%Y-%m-%d %H:%M:%S') - $1">>$LOG_FILE
}


# If values are empty, log and exit
if [ -z "$RDS_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ] || [ -z "$DB_PORT" ]; then
  log_message "Error: One or more parameters not retrieved. Check AWS CLI and IAM role." 
  exit 1
fi

echo "All environment variables extracted"

# Export PostgreSQL password so it can be used by psql without prompting
export PGPASSWORD="$DB_PASSWORD"


# Validate the PostgreSQL connection
echo "Validating PostgreSQL connection..."
$PSQL -h "$RDS_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "\q"

if [[ $? -ne 0 ]]; then
  log_message "Error: Unable to connect to PostgreSQL database.$RDS_HOST-$DB_NAME"
  exit 1
fi

log_message "Connection validated. Proceeding with query."

# Run the psql query and export result to a CSV file
$PSQL -h $RDS_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -o $OUTPUT_FILE --csv <<EOF
SELECT
    chat_data.id,                                                 -- Extract the chat's unique identifier
    chat_data.user_id,                                            -- Extract the user_id
    chat_user.email,
    regexp_replace(                                               -- Add quotes around title
        regexp_replace(                                           -- Remove any existing quotes from title
            regexp_replace(chat_data.title, '[\r\n]', '', 'g'),   -- Remove CRLF from title
            '"', '', 'g'
        ), '[\U0001F000-\U0001FFFF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U00002600-\U000026FF\U00002700-\U000027BF]', '', 'g'                                    -- Remove emojis
    )  AS title,                                                  -- Concatenate double quotes around the title
    TO_TIMESTAMP(chat_data.created_at) AS chat_created_at,        -- Extract the created_at timestamp
    TO_TIMESTAMP(chat_data.updated_at) AS chat_updated_at,        -- Extract the updated_at timestamp 
    messages.model_used,
    messages.message_id,
    messages.total_duration,
    messages.load_duration,
    messages.prompt_eval_count,
    messages.prompt_eval_duration,
    messages.eval_count,
    messages.eval_duration,
    messages.user_rating,
    regexp_replace(messages.comment, '[\r\n]', '', 'g') AS comment,
    regexp_replace(messages.feedback_reason, '[\r\n]', '', 'g') AS feedback_reason,
    COALESCE(
    TO_CHAR(ROUND((messages.eval_count::float / (messages.eval_duration / 1000000000.0)) * 100.0) / 100,'FM999999999.00'), 
    'N/A') AS response_tokens_per_second,  
-- Prompt tokens per second calculation
    COALESCE(
    TO_CHAR(ROUND((messages.prompt_eval_count::float / (messages.prompt_eval_duration / 1000000000.0)) * 100.0) / 100,'FM999999999.00'), 
    'N/A') AS prompt_tokens_per_second,
    TO_TIMESTAMP(messages.message_timestamp) AS message_timestamp
FROM $DB_SCHEMA.$DB_TABLE AS chat_data
JOIN $DB_SCHEMA.$DB_TABLE2 AS chat_user ON chat_data.user_id = chat_user.id  -- Join to get the user email by user_id
CROSS JOIN LATERAL (
    SELECT
        (message->>'model') AS model_used,
        (message->>'id') AS message_id,
        (message->'info'->>'total_duration')::bigint AS total_duration,
        (message->'info'->>'load_duration')::bigint AS load_duration,
        (message->'info'->>'prompt_eval_count')::int AS prompt_eval_count,
        (message->'info'->>'prompt_eval_duration')::bigint AS prompt_eval_duration,
        (message->'info'->>'eval_count')::int AS eval_count,
        (message->'info'->>'eval_duration')::bigint AS eval_duration,
        (message->'annotation'->>'rating')::bigint AS user_rating,
        (message->'annotation'->>'comment') AS comment,
        (message->'annotation'->>'reason') AS feedback_reason,
        (message->>'timestamp')::bigint AS message_timestamp
    FROM jsonb_array_elements(chat_data.chat::jsonb->'messages') AS message
    WHERE message->>'id' IS NOT NULL  -- Filter out blank rows where the message_id is NULL
    AND message->>'model' IS NOT NULL  -- Filter out rows where model_used is NULL
    AND message->'info'->>'total_duration' IS NOT NULL  -- Filter out rows where total_duration is NULL
) AS messages;
EOF

sed -i 's/$/\r/' $OUTPUT_FILE

if [[ $? -eq 0 ]]; then
  log_message "Data extraction complete. Output saved to $OUTPUT_FILE."
  python $SCRIPT_DIR/file_s3upload.py $OUTPUT_FILE $TARGET_LOCATION $TARGET_DIR 
else
  log_message "Error: Data extraction failed."
  exit 1
fi
