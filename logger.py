import os
from datetime import datetime

def create_log_directory() -> str:
    log_dir = "conversation_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def create_log_file(log_dir: str, prefix: str) -> str:
    timestamp = get_timestamp()
    return os.path.join(log_dir, f"{prefix}_{timestamp}.txt")

def log_message(file_path: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")