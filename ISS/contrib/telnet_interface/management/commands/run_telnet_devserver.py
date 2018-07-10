import SocketServer

from django.core.management.base import BaseCommand, CommandError

class TIException(Exception):
    handled = False

    def __init__(self, *args, **kwargs):
        self.handled = kwargs.pop('handled', False)
        super(TIException, self).__init__(self, *args, **kwargs)

class TIResponse(object):
    message = ""

    def __init__(self, message):
        self.message = message + '\n'

    def respond(self, request):
        request.sendall(self.message)

class TIView(object):
    def _respond_to_line(self, req, line):
        try:
            response = self.respond_to_line(req, line)
            if not isinstance(response, TIResponse):
                raise ValueError('Responses must subclass TIResponse.')

            response.respond(req)

        except TIException as e:
            req.sendall(e.message + '\n')

    def respond_to_line(self, req, line):
        raise NotImplemented()

class TICommandView(TIView):
    def _parse_line(self, line):
        parts = line.split(' ')
        return parts

    def respond_to_line(self, req, line):
        parts = self._parse_line(line)
        cmd = parts[0]
        params = parts[1:]
        handler = getattr(self, 'handle_' + cmd.lower(), None)

        if not handler:
            raise TIException('Command not recognized: %s' % cmd)

        return handler(req, params)

class TILatestThreadsView(TICommandView):
    def handle_echo(self, req, params):
        return TIResponse('You said: %s\n' % ' '.join(params))

class TIRequestHandler(SocketServer.StreamRequestHandler):
    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        self._view = TILatestThreadsView()

    def handle(self):
        while 1:
            line = self.rfile.readline().strip()
            self._view._respond_to_line(self.request, line)

class Command(BaseCommand):
    help = 'Runs the Telnet interface with automatic reloading.'

    def add_arguments(self, parser):
        pass

    def handle(self, **kwargs):
        host, port = '0.0.0.0', 1337
        server = SocketServer.TCPServer((host, port), TIRequestHandler)
        print 'Starting telnet server on %s:%d' % (host, port)
        server.serve_forever()
