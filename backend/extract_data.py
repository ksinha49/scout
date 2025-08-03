import os
import sys
import boto3
import psycopg2
import requests
import logging
from datetime import datetime


STANDARD_LOG_FORMAT = (
    "timestamp: %(asctime)s, name: %(name)s, levelname: %(levelname)s, message: %(message)s"
)


# Set up logging
def setup_logging(log_file):
    handler = logging.FileHandler(log_file, mode="a")
    handler.setFormatter(logging.Formatter(STANDARD_LOG_FORMAT))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


# Function to log messages
def log_message(message):
    logging.info(message)


# Fetch AWS Metadata Token and Region
def get_aws_region():
    try:
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        ).text
        aws_region = requests.get(
            "http://169.254.169.254/latest/meta-data/placement/region",
            headers={"X-aws-ec2-metadata-token": token}
        ).text
        return aws_region
    except Exception as e:
        log_message(f"Error fetching AWS region: {e}")
        sys.exit(1)


# Fetch Parameters from AWS SSM
def get_ssm_parameter(ssm_client, parameter_name, region):
    try:
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        log_message(f"Error fetching SSM parameter {parameter_name}: {e}")
        sys.exit(1)


# Validate PostgreSQL connection
def validate_postgresql_connection(connection_params):
    try:
        connection = psycopg2.connect(**connection_params)
        connection.close()
        log_message("PostgreSQL connection validated successfully.")
    except Exception as e:
        log_message(f"Error: Unable to connect to PostgreSQL database: {e}")
        sys.exit(1)


# Execute the query and export data to a CSV file
def export_query_to_csv(connection_params, output_file, query):
    try:
        connection = psycopg2.connect(**connection_params)
        cursor = connection.cursor()
        with open(output_file, 'w') as f:
            cursor.copy_expert(f"COPY ({query}) TO STDOUT WITH CSV HEADER", f)
        cursor.close()
        connection.close()
        log_message(f"Data extraction complete. Output saved to {output_file}.")
    except Exception as e:
        log_message(f"Error executing query: {e}")
        sys.exit(1)


# Main function to run the module
def main(output_file, log_file):
    setup_logging(log_file)

    # Fetch AWS Region
    aws_region = get_aws_region()
    log_message(f"Fetched AWS Region: {aws_region}")

    # Initialize Boto3 SSM client
    ssm_client = boto3.client('ssm', region_name=aws_region)

    # Fetch necessary environment parameters from SSM
    env = get_ssm_parameter(ssm_client, f"/parameters/aio/ameritasAI/SERVER_ENV", aws_region) 
    rds_host = get_ssm_parameter(ssm_client, f"/parameters/aio/ameritasAI/{env}/POSTGRESQL_ENDPT", aws_region)
    db_password = get_ssm_parameter(ssm_client, f"/parameters/aio/ameritasAI/{env}/POSTGRESQL_PASSCODE", aws_region)
    db_port = get_ssm_parameter(ssm_client, f"/parameters/aio/ameritasAI/{env}/POSTGRESQL_PORT", aws_region)
    db_user = get_ssm_parameter(ssm_client, f"/parameters/aio/ameritasAI/{env}/POSTGRESQL_USERID", aws_region)
    db_name = "postgres"
    db_schema = "open_webui"
    db_table = "chat"

    # Connection parameters for PostgreSQL
    connection_params = {
        "host": rds_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_password
    }

    # Validate PostgreSQL connection
    validate_postgresql_connection(connection_params)

    # SQL query to run
    query = f"""
    SELECT
        id,
        user_id,
        title,
        (jsonb_array_elements(chat::jsonb->'messages')->>'id') AS message_id,
        (jsonb_array_elements(chat::jsonb->'messages')->'info'->>'total_duration')::bigint AS total_duration,
        (jsonb_array_elements(chat::jsonb->'messages')->'info'->>'load_duration')::bigint AS load_duration,
        (jsonb_array_elements(chat::jsonb->'messages')->'info'->>'prompt_eval_count')::int AS prompt_eval_count,
        (jsonb_array_elements(chat::jsonb->'messages')->'info'->>'prompt_eval_duration')::bigint AS prompt_eval_duration,
        (jsonb_array_elements(chat::jsonb->'messages')->'info'->>'eval_count')::int AS eval_count,
        (jsonb_array_elements(chat::jsonb->'messages')->'info'->>'eval_duration')::bigint AS eval_duration
    FROM {db_schema}.{db_table}
    WHERE chat::jsonb->'messages' IS NOT NULL;
    """

    # Run the query and save the result to a CSV file
    export_query_to_csv(connection_params, output_file, query)


if __name__ == "__main__":
    # Ensure script is run with the correct number of arguments
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <output_file> <log_file>")
        sys.exit(1)

    output_file = os.path.abspath(sys.argv[1])
    log_file = os.path.abspath(sys.argv[2])

    main(output_file, log_file)
