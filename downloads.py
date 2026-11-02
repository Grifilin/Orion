import os, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from network import is_metered

CHUNK = 1024 * 1024
DEFAULT_THREADS = 4
MOBILE_WARN_BYTES = 20 * 1024 * 1024

class DownloadTask:
    def __init__(self, url, dest_path, threads=DEFAULT_THREADS, on_progress=None, on_done=None, on_error=None):
        self.url, self.dest_path, self.threads = url, dest_path, threads
        self.on_progress, self.on_done, self.on_error = on_progress, on_done, on_error
        self.cancelled, self.downloaded, self.total = False, 0, 0
        self._lock = threading.Lock()

    def _head(self):
        r = requests.head(self.url, allow_redirects=True, timeout=15)
        return int(r.headers.get('Content-Length', 0)), r.headers.get('Accept-Ranges', '').lower() == 'bytes'

    def _add_progress(self, n):
        with self._lock:
            self.downloaded += n
            if self.on_progress: self.on_progress(self.downloaded, self.total)

    def _download_chunk(self, start, end, idx):
        headers = {'Range': f'bytes={start}-{end}'}
        part_path = f'{self.dest_path}.part{idx}'
        with requests.get(self.url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(part_path, 'wb') as f:
                for chunk in r.iter_content(CHUNK):
                    if self.cancelled: return False
                    f.write(chunk)
                    self._add_progress(len(chunk))
        return True

    def _merge(self):
        with open(self.dest_path, 'wb') as out:
            for i in range(self.threads):
                p = f'{self.dest_path}.part{i}'
                if os.path.exists(p):
                    with open(p, 'rb') as f: out.write(f.read())
                    os.remove(p)

    def start(self):
        try:
            self.total, supports_ranges = self._head()
            if not supports_ranges or self.total == 0:
                self._single()
            else:
                self._multi()
            if self.on_done and not self.cancelled: self.on_done(self.dest_path)
        except Exception as e:
            if self.on_error: self.on_error(str(e))

    def _single(self):
        with requests.get(self.url, stream=True, timeout=30) as r:
            r.raise_for_status()
            self.total = int(r.headers.get('Content-Length', 0))
            with open(self.dest_path, 'wb') as f:
                for chunk in r.iter_content(CHUNK):
                    if self.cancelled: return
                    f.write(chunk)
                    self._add_progress(len(chunk))

    def _multi(self):
        chunk_size = self.total // self.threads
        ranges = [(i * chunk_size, self.total - 1 if i == self.threads - 1 else (i + 1) * chunk_size - 1) for i in range(self.threads)]
        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = [ex.submit(self._download_chunk, s, e, i) for i, (s, e) in enumerate(ranges)]
            for f in as_completed(futures): f.result()
        if not self.cancelled: self._merge()

def needs_mobile_permission(size_bytes):
    return is_metered() and size_bytes >= MOBILE_WARN_BYTES
