#!/usr/bin/env bash
PATH=$PATH:/usr/local/bin/
source /etc/environment

SERVICE_NAME="chatameritas.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
SCRIPT_PATH=$(pwd)  # Path to the current Git repository
BACKEND_PATH=$SCRIPT_PATH/backend
VENV_DIR=$BACKEND_PATH/chatAmeritas_venv
USER=$(whoami)  # Current user running the script
dnf groupinstall "Development Tools" -y
dnf install mesa-libGL -y

$BACKEND_PATH/stop_session.sh

chmod +x $SCRIPT_PATH/micropip_install.sh
chmod +x $SCRIPT_PATH/pull_latest.sh

rm -rf $BACKEND_PATH/topic_models

echo "Github Refresh in Progress"
$SCRIPT_PATH/pull_latest.sh

# $SCRIPT_PATH/micropip_install.sh

export NODE_OPTIONS="--max-old-space-size=8192"

echo "Application Build Started.."
rm -rf node_modules  build

npm install onnxruntime-node --onnxruntime-node-install-cuda=skip --verbose
npm run build


# Step 1: Create a Python virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3.12 -m venv $VENV_DIR
fi

# Step 2: Activate the virtual environment and install requirements
echo "Activating virtual environment and installing dependencies..."
source $VENV_DIR/bin/activate

# Install Python dependencies, if you have a requirements.txt
pip install --upgrade pip
mkdir -p $BACKEND_PATH/tmp


if [ -f $BACKEND_PATH/"requirements.txt" ]; then
    TMPDIR=$BACKEND_PATH/tmp pip install -r $BACKEND_PATH/requirements.txt
fi

mkdir -p $BACKEND_PATH/data
mkdir -p $BACKEND_PATH/data/s3_uploads
mkdir -p $BACKEND_PATH/logs

# Make the script executable
chmod +x $BACKEND_PATH/start.sh
chmod +x $BACKEND_PATH/start_session.sh
chmod +x $BACKEND_PATH/extract_chat_metrics.sh
chmod +x $BACKEND_PATH/stop_session.sh
chmod +x $BACKEND_PATH/cleanup.sh


$BACKEND_PATH/start_session.sh

