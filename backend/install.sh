#!/usr/bin/env bash
source /etc/environment

VENV_DIR="chatAmeritas_venv"
SERVICE_NAME="chatameritas.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
SCRIPT_PATH=$(pwd)  # Path to the current Git repository
USER=$(whoami)  # Current user running the script
dnf groupinstall "Development Tools"
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
tar xzf Python-3.12.0.tgz
cd Python-3.12.0
./configure --enable-optimizations
make altinstall
dnf install python3.12-pip -y
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
dnf install -y nodejs
dnf install git -y
dnf install cronie -y
dnf install tmux -y
dnf install mesa-libGL -y


# Step 1: Create a Python virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3.12 -m venv $VENV_DIR
fi

# Step 2: Activate the virtual environment and install requirements
echo "Activating virtual environment and installing dependencies..."
source ./$VENV_DIR/bin/activate

# Install Python dependencies, if you have a requirements.txt
pip install --upgrade pip
mkdir -p $SCRIPT_PATH/tmp
if [ -f "requirements.txt" ]; then
    TMPDIR=$SCRIPT_PATH/tmp pip install -r requirements.txt
fi

mkdir -p $SCRIPT_PATH/data
mkdir -p $SCRIPT_PATH/data/s3_uploads
mkdir -p $SCRIPT_PATH/logs

# Make the script executable
chmod +x $SCRIPT_PATH/start.sh
chmod +x $SCRIPT_PATH/start_session.sh
chmod +x $SCRIPT_PATH/extract_chat_metrics.sh
chmod +x $SCRIPT_PATH/stop_session.sh
chmod +x $SCRIPT_PATH/cleanup.sh

