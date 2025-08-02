#!/usr/bin/env bash
PATH=$PATH:/usr/local/bin/
source /etc/environment

#Step 1: Activate the virtual environment and install requirements
echo "Activating virtual environment"


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
    export AWS_REGION=$AWS_DEFUALT_REGION
fi

# Step 2: Use the token to access the metadata service
export ENV=$(aws ssm get-parameter --name "/parameters/aio/ameritasAI/SERVER_ENV" --with-decryption --query "Parameter.Value" --output text  --region $AWS_REGION)
echo "Loading Env variables" $ENV

# Step 3: Load ROLLBACK_REQ flag
export ROLLBACK_REQ=$(aws ssm get-parameter \
    --name "/parameters/aio/ameritasAI/ROLLBACK_REQ" \
    --with-decryption \
    --query "Parameter.Value" \
    --output text \
    --region $AWS_REGION)
echo "Loaded ROLLBACK_REQ = $ROLLBACK_REQ"

export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH


#Github repo clone
export GHP_TOKEN=$(aws ssm get-parameter --name "/parameters/devops/ameritasAI/$ENV/github-password" --with-decryption --query "Parameter.Value" --region "us-east-2" --output text)
export GHP_ACTOR=$(aws ssm get-parameter --name "/parameters/devops/ameritasAI/$ENV/github-username" --with-decryption --query "Parameter.Value" --region "us-east-2" --output text)
export GHP_REPOSITORY_1="ameritascorp/chatAmeritas-ui"

git restore .

git remote set-url origin "https://${GHP_ACTOR}:${GHP_TOKEN}@github.com/${GHP_REPOSITORY_1}.git"

git fetch origin

# Step 5: Determine which branch to check out
if [[ "$ROLLBACK_REQ" == "true" ]]; then
    TARGET_ENV="pre-prod"
    echo "ROLLBACK_REQ is true → using branch: $TARGET_ENV"
else
    case "$ENV" in
      development) TARGET_ENV="develop" ;;
      model)       TARGET_ENV="model"   ;;
      production)  TARGET_ENV="main"    ;;
      *)           TARGET_ENV="$ENV"    ;;  # fallback to ENV itself if unmapped
    esac
    echo "ENV is '$ENV' → using branch: $TARGET_ENV"
fi

git checkout $TARGET_ENV

git pull origin

