import argparse, os, time, hashlib, mimetypes
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def authenticate(sa_json):
    creds = Credentials.from_service_account_file(
        sa_json, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

def get_mime_type(path):
    return mimetypes.guess_type(path)[0] or 'application/octet-stream'

def hash_file(path):
    try:
        h = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        print(f"[ERROR] Cannot hash {path}: {e}")
        return None

def create_folder(service, parent_id, name):
    md = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(
        body=md,
        fields='id',
        supportsAllDrives=True
    ).execute()
    print(f"[CREATE] New Drive folder '{name}' → {folder['id']}")
    return folder['id']

class SyncHandler(FileSystemEventHandler):
    def __init__(self, svc, local_root, drive_folder_id):
        self.svc = svc
        self.local_root = os.path.abspath(local_root)
        self.drive_folder_id = drive_folder_id
        self.cache = {}
        print("[INIT] Full initial sync…")
        self.initial_sync()
        print("[INIT] Watching for changes…\n")

    def initial_sync(self):
        for root, _, files in os.walk(self.local_root):
            for fn in files:
                self.sync(os.path.join(root, fn))

    def on_created(self, e):   self.handle_event(e, "New")
    def on_modified(self, e):  self.handle_event(e, "Modified")
    def handle_event(self, e, tag):
        if not e.is_directory:
            print(f"[EVENT] {tag}: {e.src_path}")
            self.sync(e.src_path)

    def sync(self, path):
        if not os.path.exists(path):
            return
        rel = os.path.relpath(path, self.local_root).replace("\\", "/")
        h = hash_file(path)
        if not h or self.cache.get(rel) == h:
            return
        print(f"[UPLOAD] {rel} …")
        media = MediaFileUpload(path, mimetype=get_mime_type(path), resumable=False)
        md = {'name': rel, 'parents': [self.drive_folder_id]}
        existing = self.find(rel)
        try:
            if existing:
                self.svc.files().update(
                    fileId=existing['id'],
                    media_body=media,
                    supportsAllDrives=True
                ).execute()
                print(f"[UPDATE] {rel}")
            else:
                self.svc.files().create(
                    body=md,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                print(f"[CREATE] {rel}")
            self.cache[rel] = h
        except Exception as e:
            print(f"[ERROR] Sync failed for {rel}: {e}")

    def find(self, name):
        q = f"'{self.drive_folder_id}' in parents and name='{name}' and trashed=false"
        res = self.svc.files().list(
            q=q,
            fields='files(id,name)',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        files = res.get('files', [])
        return files[0] if files else None

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-s', '--service-account-json', required=True, help="Service account JSON file")
    p.add_argument('-l', '--local-folder',       required=True, help="Local folder to sync")
    p.add_argument('-p', '--parent-folder-id',   required=True, help="Google Drive parent folder ID")
    p.add_argument('-k', '--keep-running', action='store_true', help="Keep running to monitor changes")
    a = p.parse_args()

    svc = authenticate(a.service_account_json)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    new_id = create_folder(svc, a.parent_folder_id, ts)

    handler = SyncHandler(svc, a.local_folder, new_id)
    obs = Observer()
    obs.schedule(handler, path=a.local_folder, recursive=True)
    obs.start()
    print(f"[WATCH] {a.local_folder} → Drive folder ID: {new_id}\n")

    if a.keep_running:
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            obs.stop()
        obs.join()
        print("[EXIT] Stopped.")
    else:
        obs.stop()
        print("[INFO] Exiting after initial sync.")

if __name__ == '__main__':
    main()
