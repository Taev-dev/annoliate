'''This contains all the custom exceptions used by annoliate. They're in
a separate file to minimize the chances of circular imports.
'''


class AnnoliateException(Exception):
    '''Base class for all custom exceptions raised by Annoliate.
    '''


class RequestorError(AnnoliateException):
    '''Subclasses of this are raised when there are problems that
    originated with the client. You could do a catchall for this to turn
    all client problems into 400s, for example.
    '''


class MissingRoute(RequestorError, LookupError):
    '''Raised by the router when a route is missing.
    '''

    def __init__(self, *args, route, **kwargs):
        super().__init__(*args, **kwargs)
        self.route = route
