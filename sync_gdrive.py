import os
import sys
import subprocess
import json

# ==============================================================================
# CONFIGURATION: Paste your public Google Drive folder link here
# If left empty, the script will prompt you for the link and save it in a config file.
FOLDER_URL = "https://drive.google.com/drive/folders/1U-garCevPHcPXjq5km_uibA7E07KkpMZ?usp=sharing"
# ==============================================================================

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        # Install using current python environment pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def main():
    # Make sure gdown is installed
    install_and_import("gdown")
    import gdown
    
    config_file = "gdrive_config.json"
    folder_url = FOLDER_URL.strip()
    
    if not folder_url:
        # Load existing config if available
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                try:
                    config = json.load(f)
                    folder_url = config.get("folder_url", "")
                except:
                    pass
                
    if not folder_url:
        print("="*60)
        print("NGENAI GOOGLE DRIVE GALLERY SYNC SETUP")
        print("="*60)
        print("Instructions:")
        print("1. Open Google Drive and create your main Workshops folder.")
        print("2. Inside it, create subfolders for each college (e.g. 'COEP', 'VIT').")
        print("3. Put your workshop images in those college folders.")
        print("4. Share the main folder as 'Anyone with the link can view' (Viewer access).")
        print("5. Paste the link to the main folder below:")
        print("="*60)
        folder_url = input("Enter Google Drive Folder Link: ").strip()
        if not folder_url:
            print("No link provided. Exiting.")
            return
        # Save link to config
        with open(config_file, "w") as f:
            json.dump({"folder_url": folder_url}, f, indent=2)
            
    dest_dir = "workshops_gallery"
    if os.path.exists(dest_dir):
        print(f"Cleaning {dest_dir} directory before syncing to remove deleted files...")
        import shutil
        for item in os.listdir(dest_dir):
            item_path = os.path.join(dest_dir, item)
            if item != "README.txt":
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    print(f"Error cleaning {item}: {e}")
                    
    os.makedirs(dest_dir, exist_ok=True)
    
    print("\nSyncing with Google Drive. Downloading new subfolders and images...")
    
    try:
        # Download the Google Drive folder recursively
        gdown.download_folder(url=folder_url, output=dest_dir, quiet=False, use_cookies=False)
        print("\nDownload completed successfully.")
    except Exception as e:
        print(f"\nError during Google Drive sync: {e}")
        print("Make sure the folder sharing is set to 'Anyone with the link can view'.")
        # Clear config so user can re-enter link next time
        if os.path.exists(config_file):
            os.remove(config_file)
        return
        
    print("\nRegenerating website gallery index...")
    try:
        import sync_gallery
        sync_gallery.generate_gallery_data()
    except ImportError:
        # If imported in different way, call via system
        subprocess.check_call([sys.executable, "sync_gallery.py"])
    except Exception as e:
        print(f"Error compiling gallery data: {e}")

if __name__ == "__main__":
    main()
