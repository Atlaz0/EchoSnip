import os
import yaml

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def scan_snippets(config):
    folder_path = config["folder_path"]
    identifier = config["identifier"]
    extensions = config["extensions"]

    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, start=1):
                            if identifier in line:
                                print(f"{file_path}:{i}: {line.strip()}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    config = load_config()
    scan_snippets(config)
