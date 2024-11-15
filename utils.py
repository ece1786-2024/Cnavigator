import os
from datetime import datetime

def create_log_directory():
    log_dir = "conversation_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir