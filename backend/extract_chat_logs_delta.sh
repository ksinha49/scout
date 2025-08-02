#!/bin/bash
PATH=$PATH:/usr/local/bin/
#=====================================================
# Script Name: extract_chat_metrics.sh
# Description: This script extracts chat metrics,
#              runs topic modeling, and uploads outputs to S3.
# Author: Koushik Sinha
# Edited : Sean Olson
# Date: 01/28/2025
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
PYTHON="$VENV_PATH/$VENV_DIR/bin/python"
# Delay to allow IAM role association
echo "Getting AWS credentials"
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
OUTPUT_FILE="${OUTPUT_FILE_PARAM}_${CURR_DT}.csv"   # Set the output file with timestamp
LOG_FILE="${LOG_FILE_PARAM}"                        # Set the log file


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
DB_TABLE3=feedback

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

#QUERY="SELECT info FROM public.user LIMIT 20;"

#export TEST=$($PSQL -h "$RDS_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "\dt public.*")
#export TEST=$($PSQL -h "$RDS_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "\d public.user")
#$PSQL -h "$RDS_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "$QUERY"
#echo "$TEST"


log_message "Connection validated. Proceeding with query."


# Run the psql query and export result to a CSV file
$PSQL -h $RDS_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -o $OUTPUT_FILE --csv <<EOF
WITH messages AS (
    SELECT
        chat_data.id AS chat_id,
        chat_data.user_id,
        chat_user.email,
        regexp_replace(                                           -- Add quotes around title
        regexp_replace(                                           -- Remove any existing quotes from title
            regexp_replace(chat_data.title, '[\r\n]', '', 'g'),   -- Remove CRLF from title
            '"', '', 'g'
        ), '[\U0001F000-\U0001FFFF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U00002600-\U000026FF\U00002700-\U000027BF]', '', 'g'                                    -- Remove emojis
    )  AS title,
        TO_TIMESTAMP(chat_data.created_at) AS chat_created_at,
        TO_TIMESTAMP(chat_data.updated_at) AS chat_updated_at,
        msgs.message_id,
                msgs.model_used,
        msgs.parent_id,
        msgs.role,
        msgs.content,
        msgs.message_timestamp,
        COALESCE((msgs.rating)::int, 0) AS rating,
        COALESCE(msgs.comment, '') AS comment
    FROM $DB_SCHEMA.$DB_TABLE AS chat_data
    JOIN $DB_SCHEMA.$DB_TABLE2 AS chat_user ON chat_data.user_id = chat_user.id
    CROSS JOIN LATERAL (
        SELECT
            msg_element.key AS message_id,
            (msg_element.value->>'model') AS model_used,
            msg_element.value->>'parentId' AS parent_id,
            msg_element.value->>'role' AS role,
            msg_element.value->>'content' AS content,
            (msg_element.value->>'timestamp')::bigint AS message_timestamp,
            (msg_element.value->'annotation'->>'rating') AS rating,
            (msg_element.value->'annotation'->>'comment') AS comment
        FROM jsonb_each(chat_data.chat::jsonb->'history'->'messages') AS msg_element
    ) AS msgs
        WHERE TO_TIMESTAMP(chat_data.created_at) >= NOW() - INTERVAL '7 days'
),
exchanges AS (
    SELECT
        a.chat_id,
        a.user_id,
        a.email,
        a.title,
        a.chat_created_at,
        a.chat_updated_at,
        a.model_used,
        u.message_id AS user_message_id,
        u.content AS user_content,
        u.message_timestamp AS user_timestamp,
        a.message_id AS assistant_message_id,
        a.content AS assistant_content,
        a.message_timestamp AS assistant_timestamp,
        a.rating AS assistant_rating,
        a.comment AS assistant_comment
    FROM messages a
    JOIN messages u ON a.parent_id = u.message_id
    WHERE a.role = 'assistant' AND u.role = 'user'
)
SELECT
    chats.chat_id,
    chats.model_used,
    chats.user_id,
    chats.email,
    chats.title,
    chats.chat_created_at,
    chats.chat_updated_at,
    json_build_object(
        'chosen', chosen_conversation.chosen_text,
        'neutral', neutral_conversation.neutral_text,
        'rejected', rejected_conversation.rejected_text
    ) AS conversation_json
FROM (
    SELECT DISTINCT
        chat_id,
        model_used,
        user_id,
        email,
        title,
        chat_created_at,
        chat_updated_at
    FROM messages
    WHERE model_used IS NOT NULL
) AS chats
LEFT JOIN (
    SELECT
        e.chat_id,
        STRING_AGG(
            'Human: ' || e.user_content || E'\n\nAssistant: ' || e.assistant_content || E'\n\nFeedback: ' || e.assistant_comment,
            E'\n\n' ORDER BY e.user_timestamp
        ) AS chosen_text
    FROM exchanges e
    WHERE e.assistant_rating > 0
    GROUP BY e.chat_id
) AS chosen_conversation ON chosen_conversation.chat_id = chats.chat_id
LEFT JOIN (
    SELECT
        e.chat_id,
        STRING_AGG(
            'Human: ' || e.user_content || E'\n\nAssistant: ' || e.assistant_content || E'\n\nFeedback: ' || e.assistant_comment,
            E'\n\n' ORDER BY e.user_timestamp
        ) AS neutral_text
    FROM exchanges e
    WHERE e.assistant_rating = 0
    GROUP BY e.chat_id
) AS neutral_conversation ON neutral_conversation.chat_id = chats.chat_id
LEFT JOIN (
    SELECT
        e.chat_id,
        STRING_AGG(
            'Human: ' || e.user_content || E'\n\nAssistant: ' || e.assistant_content || E'\n\nFeedback: ' || e.assistant_comment,
            E'\n\n' ORDER BY e.user_timestamp
        ) AS rejected_text
    FROM exchanges e
    WHERE e.assistant_rating = -1
    GROUP BY e.chat_id
) AS rejected_conversation ON rejected_conversation.chat_id = chats.chat_id;
EOF

sed -i 's/$/\r/' $OUTPUT_FILE

if [[ $? -eq 0 ]]; then
  log_message "Data extraction complete. Output saved to $OUTPUT_FILE."

  # ---------------------------
  # Run the Python Script
  # ---------------------------
  PYTHON_SCRIPT="$SCRIPT_DIR/topic_modeling_and_analysis.py"
  OUTPUT_DIR="data/"
  OUTPUT1_PREFIX="chat_log_analysis_"
  OUTPUT2_PREFIX="bertopic_topics_"
  MOST_RECENT_LOG=$(ls -t ${OUTPUT_DIR}${OUTPUT1_PREFIX}* 2>/dev/null | head -n 1)
  MOST_RECENT_TOPICS=$(ls -t ${OUTPUT_DIR}${OUTPUT2_PREFIX}* 2>/dev/null | head -n 1)

  if [[ -f "$PYTHON_SCRIPT" ]]; then
    log_message "Running topic modeling script."
    $PYTHON "$PYTHON_SCRIPT" "$OUTPUT_FILE"

    if [[ $? -eq 0 ]]; then
      log_message "Topic modeling completed successfully."

      # Upload the most recent log file
      if [[ -f "$MOST_RECENT_LOG" ]]; then
        log_message "Uploading $MOST_RECENT_LOG to S3."
        $PYTHON $SCRIPT_DIR/file_s3upload.py $MOST_RECENT_LOG $TARGET_LOCATION $TARGET_DIR
        if [[ $? -eq 0 ]]; then
          log_message "$MOST_RECENT_LOG uploaded successfully."
        else
          log_message "Error: Failed to upload $MOST_RECENT_LOG to S3."
        fi
      else
        log_message "Error: $MOST_RECENT_LOG not found."
      fi

      # Upload the most recent topics file
      if [[ -f "$MOST_RECENT_TOPICS" ]]; then
        log_message "Uploading $MOST_RECENT_TOPICS to S3."
        $PYTHON $SCRIPT_DIR/file_s3upload.py $MOST_RECENT_TOPICS $TARGET_LOCATION $TARGET_DIR
        if [[ $? -eq 0 ]]; then
          log_message "$MOST_RECENT_TOPICS uploaded successfully."
        else
          log_message "Error: Failed to upload $MOST_RECENT_TOPICS to S3."
        fi
      else
        log_message "Error: $MOST_RECENT_TOPICS not found."
      fi

      # Upload the original conversation CSV
      if [[ -f "$OUTPUT_FILE" ]]; then
        log_message "Uploading $OUTPUT_FILE to S3."
        $PYTHON $SCRIPT_DIR/file_s3upload.py $OUTPUT_FILE $TARGET_LOCATION $TARGET_DIR
        if [[ $? -eq 0 ]]; then
          log_message "$OUTPUT_FILE uploaded successfully."
        else
          log_message "Error: Failed to upload $OUTPUT_FILE to S3."
        fi
      fi

    else
      log_message "Error: Topic analysis script failed."
      exit 1
    fi
  else
    log_message "Error: Python script '$PYTHON_SCRIPT' not found."
    exit 1
  fi
else
  log_message "Error: Data extraction failed."
  exit 1
fi
