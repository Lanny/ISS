import SocketServer
import threading
import time

from django.core.management.base import BaseCommand, CommandError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ISS.contrib.telnet_interface import server

class FileModifiedHandler(FileSystemEventHandler):
    def __init__(self, server_runner):
        super(FileModifiedHandler, self).__init__()
        self._server_runner = server_runner

    def on_modified(self, event):
        if not event.src_path.endswith('.py'):
            return

        print '%s modified, reloading server' % event.src_path
        self._server_runner.reload()

class ServerRunner(threading.Thread):
    _server = None
    _continue = True

    def _create_server(self):
        host, port = '0.0.0.0', 1337

        from ISS.contrib.telnet_interface import server
        server = reload(server)
        from ISS.contrib.telnet_interface import server
        self._server = SocketServer.TCPServer((host, port), server.TIRequestHandler)

        print 'Starting telnet server on %s:%d' % (host, port)
        self._server.serve_forever()

    def reload(self):
        self.shutdown()

    def stop(self):
        self._continue = False
        self.shutdown()

    def shutdown(self):
        print 'Shutting down server...'
        self._server.shutdown()

    def run(self):
        while self._continue:
            self._create_server()
            self._server.server_close()
            print 'Server closed.'

class Command(BaseCommand):
    help = 'Runs the Telnet interface with automatic reloading.'

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        server_runner = ServerRunner()
        fs_event_handler = FileModifiedHandler(server_runner)

        path = 'ISS/contrib/telnet_interface'
        observer = Observer()
        observer.schedule(fs_event_handler, path, recursive=True)
        observer.start()

        server_runner.start()

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, Exception):
            observer.stop()
            server_runner.stop()

        print 'Waiting for Watchdog thread to conclude...'
        observer.join()
        print 'done.'

        print 'Waiting for server runner thread to conclude...'
        server_runner.join()
        print 'done. Script complete.'
