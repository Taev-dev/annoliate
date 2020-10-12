import dataclasses
import string

from annoliate.exceptions import MissingRoute


_FORMATTER = string.Formatter()
# Come with me if you want to live
TERMINATOR = object()
CAPTURE_SEGMENT = object()


class Router:
    '''The router is responsible for, well, routing requests to the
    appropriate handler, or raising when they don't exist. It also
    manages matching static paths from incoming requests to dynamic
    paths from declared routes, and extracting path parameters from them
    to be used by handlers.

    See the router docs for an exploration of the tree powering the
    dynamic routing algorithm.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # NOTE: the lookups here are not the same! In dynamic routes, we need
        # to hold on to the actual route object, so that we can recover the
        # capture segment names, so we have a secondary attribute for the
        # handler. In the static lookup, that isn't necessary, so we preserve
        # just the handler, to eliminate the extra instance lookup.
        self._static_lookup = {}
        self._dynamic_lookup = {}

    def dispatch(self, incoming_route):
        if incoming_route in self._static_lookup:
            return self._static_lookup[incoming_route]
        else:
            return self._dispatch_dynamic(incoming_route).handler

    def _dispatch_dynamic(self, incoming_route):
        '''Finds a match in the dynamic lookup, or raises MissingRoute.
        '''
        current_lookup = self._dynamic_lookup

        # Recursion in python is pretty slow compared to looping, so just do
        # this the iterative way
        for segment in incoming_route.segments:
            # A direct match means this is a static path component; proceed
            # down the routing tree
            if segment in current_lookup:
                current_lookup = current_lookup[segment]

            # No direct match, but a capture segment available to "swallow" it;
            # proceed down the routing tree
            elif CAPTURE_SEGMENT in current_lookup:
                current_lookup = current_lookup[CAPTURE_SEGMENT]

            # There's no way to recover from here; if we were at the end of
            # the route segments, we wouldn't be in the for loop
            else:
                raise MissingRoute(
                    'Route not found in router', route=incoming_route)

        # We could use a for/else here, but there's no real reason to, because
        # we **raise** on misses. The important thing is to verify that we do
        # have a route that ends at this segment
        if TERMINATOR in current_lookup:
            return current_lookup[TERMINATOR]
        else:
            raise MissingRoute(
                'Route not found in router', route=incoming_route)

    def register(self, route_str, handler, allow_overwrite=False):
        route = _Route.make(route_str)

        if isinstance(route, _StaticRoute):
            if route in self._static_lookup and not allow_overwrite:
                raise ValueError('Route already found in router!', route_str)

            self._static_lookup[route] = handler

        else:
            route.handler = handler
            # Construct the match tree. Note that we need *both* sentinels
            # (TERMINATOR and CAPTURE_SEGMENT), or we could accidentally match
            # on a partial route.
            current_lookup = self._dynamic_lookup

            for segment in route.segments:
                if isinstance(segment, _CaptureSegment):
                    segment = CAPTURE_SEGMENT

                # Keep in mind this is a tree, so we might have multiple
                # branches; ex, /foo/bar and /foo/baz. Note that defaultdict
                # wouldn't help us here, because this isn't a recursive
                # function and we have an arbitrary tree depth.
                if segment in current_lookup:
                    current_lookup = current_lookup[segment]
                else:
                    # This is equivalent to, but more readable than,
                    # current_lookup[segment] = current_lookup = {}
                    new_lookup = {}
                    current_lookup[segment] = new_lookup
                    current_lookup = new_lookup

            # See router docs for a better explanation, but we need the
            # terminator to distinguish between
            # '/api/{foo}' and '/api/{foo}/{bar}'
            if TERMINATOR in current_lookup and not allow_overwrite:
                raise ValueError('Route already found in router!', route_str)

                current_lookup[TERMINATOR] = route


class _Route:
    # __slots__ use here is (premature) optimization for lookup speed
    __slots__ = [
        # Underscored not to make "private", but rather to avoid shadowing the
        # builtin hash() function
        '_hash',
        # Tuple of ordered route components
        # example: '/foo/bar/baz' -> ('foo', 'bar', 'baz')
        'segments'
    ]

    def __init__(self, segments, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Precalculate this ASAP
        self._hash = hash(tuple(segments))

    def __hash__(self):
        # We cache this for fast lookup on static routes
        return self._hash

    def __eq__(self, other):
        '''Compare to other Paths. Returns True if both paths are equal,
        including the naming of capture groups, but not including query
        strings, etc. Returns False otherwise.
        '''
        try:
            return self.segments == other.segments
        except (AttributeError, TypeError, ValueError):
            return NotImplemented

    def __repr__(self):
        '''While technically we should try and make the repr capable of
        being fed directly to __init__, this is much, much more useful
        for debugging.
        '''
        route_str = '/' + '/'.join(str(segment) for segment in self.segments)
        return f'<{type(self).__name__} ({route_str})>'

    @classmethod
    def make(cls, path_str):
        '''Takes a annoliate-style route (ie, string.format-syle),
        extracts any named parameters, and returns a concrete _Route
        subclass (either dynamic or static) based on the presence of
        capture segments.

        This is only meant to be called when *creating* routes. Incoming
        requests will **always** be static routes, so they should be
        created directly through _StaticRoute.parse(request_path).
        '''
        is_dynamic = False
        components = path_str.split('/')
        segments = []

        # This normalizes the path, ignoring the leading slash
        if components[0] == '':
            components = components[1:]

        # TODO: some amount of sanity checks here on values. This won't detect
        # invalid URLs or anything, so misspelled routes are harder to debug,
        # and I have no idea what this would look like with url quoting
        for component in components:
            # fr reals, the stdlib has an annoying API for this
            stdlib_tuples = list(_FORMATTER.parse(component))
            if len(stdlib_tuples) > 1:
                raise ValueError(
                    'Annoliate routes cannot have multiple captures per '
                    + 'segment!')

            stdlib_tuple, = stdlib_tuples
            literal_text, field_name, fmt_spec, conversion = stdlib_tuple

            # Note: format spec is something like float formatting to <x>
            # sigfigs, and conversion is str/repr/ascii. Neither are
            # supported. Also note that it seems format_spec is usually a
            # str (even if empty) but conversion can be None? weird. not a
            # fan.
            if fmt_spec or conversion:
                raise ValueError(
                    'Annoliate routes support no spec nor conversion!')
            elif field_name == '':
                raise ValueError(
                    'Annoliate route capture segments must be named!')
            # This would mean there were two capture segments in the same
            # path segment
            elif literal_text == '':
                raise ValueError(
                    'Annoliate routes can only have a single capture '
                    + 'per path segment!')

            if field_name is None:
                segments.append(literal_text)
            else:
                is_dynamic = True
                segments.append(_CaptureSegment(name=field_name))

        if is_dynamic:
            return _DynamicRoute(segments)
        else:
            return _StaticRoute(segments)


class _DynamicRoute(_Route):

    __slots__ = [
        'capture_map',
        'handler'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        capture_map = {}
        for index, segment in self.segments:
            if isinstance(segment, _CaptureSegment):
                capture_map[index] = segment.name

        self.capture_map = capture_map

    def extract_captures(self, static_route):
        '''For a given static_route, converts the capture segments into
        a dictionary and returns it.

        IMPORTANT: the static_route **must** already match the
        _DynamicRoute instance (ie, must match self). This performs no
        checks on that, so behavior in that case is undefined.
        '''
        # Variable assignment is a tiny, tiny amount of bytecode overhead, but
        # lookups on the other instance are slow, so memoize in case there's
        # more than one capture group.
        static_segments = static_route.segments
        return {
            name: static_segments[index]
            for index, name in self.capture_map.items()
        }


class _StaticRoute(_Route):

    @classmethod
    def parse(cls, well_formed_path):
        '''Shortcut for creating _StaticRoutes directly from a
        known-well-formed path, as would be expected from an ASGI
        gateway during request processing.
        '''
        # This normalizes the path, ignoring the leading slash
        if well_formed_path[0] == '/':
            segments = well_formed_path[1:].split('/')
        else:
            segments = well_formed_path.split('/')

        return cls(segments)


@dataclasses.dataclass(frozen=True)
class _CaptureSegment:
    '''Instances of this class very simply keep track of the
    _CaptureSegment and provide various utilities (like hashing)
    '''
    name: str

    def __str__(self):
        # Trust me, this looks better than an f-string (triple braces XD)
        return '{' + self.name + '}'
