## Usage

```bash
python main.py -s /path/to/service-account.json -l /path/to/local/folder -p parent-folder-id -k
```

**Arguments:**

- `-s /path/to/service-account.json`  
    Path to your Google service account JSON file.
- `-l /path/to/local/folder`  
    Path to the local directory you want to sync.
- `-p parent-folder-id`  
    The ID of the parent folder in Google Drive where the new folder will be created.
- `-k` *(Optional)*  
    Keep the script running to monitor changes.

> If you omit the `-k` flag, the script will perform the initial sync and then exit.  
> If you include the `-k` flag, the script will continue running and monitor the specified local folder for changes.

---

## How to Start Syncing Your Images

1. **Install required dependencies:**
     ```bash
     pip install -r requirements.txt
     ```

2. **Download the service account file:**  
     [abb_gd_share_service_account.json](https://drive.google.com/file/d/1S5oCHbBP8_vv1QVxZVrDj3tvrpnwu_pU/view?usp=drive_link)  
     Save it to this folder.

3. **Run the sync script:**
     ```bash
     python main.py -s abb_gd_share_service_account.json -l ./your_images -p 1LKTZVjMbinYsrqDYe-g-VHbpLQqNM33K -k
     ```

4. **Add images to `./your_images`**  
     The app will automatically sync them to Google Drive for processing as long as it is running.

