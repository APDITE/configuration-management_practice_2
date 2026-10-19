"""Локальный HTTP-сервер с тестовым репозиторием Maven.

Раздаёт файлы из tests/fixtures/maven, чтобы тесты не зависели от сети.
"""

import functools
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "maven")
LOCALHOST = "127.0.0.1"
ANY_PORT = 0


class QuietHandler(SimpleHTTPRequestHandler):
    """Обработчик запросов без вывода журнала в консоль."""

    def log_message(self, *args):
        """Не выводить журнал запросов."""


class MavenServer:
    """Сервер, запускаемый в отдельном потоке на свободном порту."""

    def __init__(self):
        """Создать сервер для каталога с тестовыми POM."""
        handler = functools.partial(QuietHandler, directory=FIXTURES)
        self.httpd = ThreadingHTTPServer((LOCALHOST, ANY_PORT), handler)
        self.thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True)

    @property
    def url(self):
        """URL-адрес корня репозитория."""
        host, port = self.httpd.server_address[:2]
        return f"http://{host}:{port}"

    def start(self):
        """Запустить сервер."""
        self.thread.start()

    def stop(self):
        """Остановить сервер и освободить порт."""
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
