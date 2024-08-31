import os
import json
import shutil
from datetime import datetime

def cw(text):
    print(text)

def sanitize_path(path):
    # Remove any invalid characters from the path
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        path = path.replace(char, '')
    return path

def run():
    # Read configuration
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    
    vscode_history_directory = config['AppSettings']['VSCodeHistoryDirectory']
    vscode_recovery_directory = config['AppSettings']['VSCodeRecoveryDirectory']

    cw(f"VSCode History Directory: {vscode_history_directory}")
    cw(f"VSCode Recovery Directory: {vscode_recovery_directory}")

    if vscode_recovery_directory:
        try:
            restored_file_count = 0
            if os.path.exists(vscode_recovery_directory):
                shutil.rmtree(vscode_recovery_directory)
            os.makedirs(vscode_recovery_directory)

            if vscode_history_directory and os.path.exists(vscode_history_directory):
                snapshot_directories = sorted(
                    [d for d in os.listdir(vscode_history_directory) if os.path.isdir(os.path.join(vscode_history_directory, d))],
                    key=lambda x: os.path.getmtime(os.path.join(vscode_history_directory, x))
                )

                for snapshot_directory in snapshot_directories:
                    snapshot_directory_full_path = os.path.join(vscode_history_directory, snapshot_directory)
                    cw(f"Processing directory: {snapshot_directory_full_path}")

                    json_file = os.path.join(snapshot_directory_full_path, 'entries.json')
                    if os.path.exists(json_file):
                        with open(json_file, 'r') as f:
                            entries_json_file = json.load(f)

                        resource = entries_json_file.get('resource', '')
                        original_file_path = resource.replace('file://', '')
                        entries = entries_json_file.get('entries', [])

                        if entries:
                            latest_entry = max(entries, key=lambda x: x.get('timestamp', 0))
                            file_id = latest_entry.get('id')
                            
                            if file_id:
                                snapshot_file_full_path = os.path.join(snapshot_directory_full_path, file_id)
                                relative_path = sanitize_path(original_file_path.lstrip('/'))
                                restore_to_file_path = os.path.join(vscode_recovery_directory, relative_path)
                                
                                cw(f"Attempting to restore: {restore_to_file_path}")
                                
                                try:
                                    os.makedirs(os.path.dirname(restore_to_file_path), exist_ok=True)
                                    
                                    if os.path.exists(restore_to_file_path):
                                        os.remove(restore_to_file_path)
                                    
                                    shutil.copy2(snapshot_file_full_path, restore_to_file_path)
                                    restored_file_count += 1
                                    cw(f"Successfully restored: {restore_to_file_path}")
                                except Exception as e:
                                    cw(f"Failed to restore {restore_to_file_path}: {str(e)}")

            cw(f"{restored_file_count} files restored to \n{vscode_recovery_directory}")

        except IOError as ioex:
            cw(f"IO Exception: {str(ioex)}")
        except Exception as ex:
            cw(f"Exception: {str(ex)}")
    else:
        cw("VSCode Recovery Directory is not set in the config file.")

if __name__ == "__main__":
    run()