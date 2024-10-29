# Install necessary system packages

sudo apt update
sudo apt-get install portaudio19-dev -y
sudo apt install ffmpeg -y

# Ensure Python 3 is installed
sudo apt install python3-pip -y

# Install required Python packages using pip
pip install -r requirements.txt

# Hugging Face authentication
huggingface-cli login --token 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