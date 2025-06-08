import cv2
import threading

class StreamAdapter:
    def __init__(self, src_url):
        self.cap = cv2.VideoCapture(src_url, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            raise RuntimeError(f"Не удалось открыть {src_url}")
        self.grabbed, self.frame = self.cap.read()
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        """Запускает фоновые таски по непрерывному чтению кадров"""
        self.running = True
        t = threading.Thread(target=self._update, daemon=True)
        t.start()

    def _update(self):
        while self.running:
            grabbed, frame = self.cap.read()
            with self.lock:
                self.grabbed, self.frame = grabbed, frame

    def read(self):
        """Возвращает последний прочитанный кадр"""
        with self.lock:
            return self.grabbed, self.frame

    def stop(self):
        """Останавливает фоновые задачи и освобождает ресурс"""
        self.running = False
        self.cap.release()
