# Annoliate

Annoliate is an annotation-fueled python web framework for people who have other shit to do. Its top three goals, in no particular order:

+   Minimize the learning curve. If you understand Python, you should intuitively understand Annoliate.
+   Massively streamline the process of creating a production-grade API, including input validation and route documentation.
+   Encourage coding best practices, including minimization of global state.

```python
from annoliate import Http
from annoliate import Response
from annoliate import RouteGroup

# Use whichever asgi and loop you'd like
from functools import partial
from hypercorn.trio import serve as asgi_serve
from hypercorn.config import Config as AsgiConfig
from trio import run


# Apps are created within nestable RouteGroup classes
class HelloWorldApp(RouteGroup):

    # The barest of barebones 'hello world' responses
    @Http.get('/')
    async def hello_world(self) -> Response.text():
        '''Somewhere, over the rainbow...'''
        return Response(200, 'Hello? World?')


# The startup incantations will depend on your choice of asgi server and loop
if __name__ == '__main__':
    config = AsgiConfig()
    config.bind = ['localhost:8080']
    app = HelloWorldApp()
    run(partial(serve, app, config))
```

### Minimize the learning curve

First and foremost: learning curves are accessibility issues. Someone from a non-coding background has to learn a whole lot before they can even get to ``hello world``. Forcing them to also learn a handful of gotchas, special route declarations, and hidden magic, is just adding work to the pile. Even switching Python domains can be problematic; someone could be an expert data analyst living in the scipy/numpy world, writing excellent, pythonic code, and be completely taken aback by Django's breadth or Flask's magical global state. And even if you're an expert *web* developer coming to Python from a different language, time spent learning your web framework, is time you aren't spending making your app. So annoliate focuses heavily on making its API as simple, and pythonic, as possible.

### Streamline making production-grade APIs

Let's say you're making a webapp for Widgets, Inc, who has zero existing code. Going from zero to production is a long, iterative process. Being able to ship bits and pieces along the way can be a crucial tool to maintain momentum and get early feedback. But iterative development should *just work*; you shouldn't need to spend time planning out a particular blueprint structure or be fighting with app initialization and middleware. Simple is best.

Simultaneously, there are a lot of things that really should be hard requirements for any production software, but are frequently overlooked in the rush to an MVP. They're slow, tedious things, and the emphasis is on shipping features. Input validation is often treated as an afterthought, when it can be one of the most consequential ways to reduce error rates and deter malicious behavior. API documentation is frequently lacking, even though it can be a vital resource to bridge the frontend/backend divide. And so on, and so forth.

Annoliate ships with as many of those production bells and whistles as possible, and makes it as straightforward as possible to add your own.

### Encourage best practices

Pop quiz: what's the best approach to sharing a database pool amongst all connections in a Flask or Django app? What about runtime-mutable configuration options, like you might source from Zookeeper? What's the best way to avoid import side effects?

In many web frameworks, all of these things take careful effort and planning to get "right", but are relatively straightforward to be "meh, good enough for now". Annoliate tries to make Python best practices as simple as possible, and lets you put all of your runtime application state into the application instance itself, instead of storing it at module-level.

It also makes ``async`` app init operations simple and intuitive, even when they need to establish shared state for all connections: run the async setup after starting the event loop, but before starting the server, and then pass references into the app's ``__init__`` call.

### Oh, and one other thing

Annoliate is pure python and loop-agnostic. Use it on asyncio, asyncio+uvloop, trio, curio, whatever. Sky's the limit! Just supply your own ``asgi`` server (we recommend hypercorn) and you're off to the races.

## Additional planned features

+   Middleware support through additional route decorators
+   Inheritance support (use sparingly!) for ``RouteGroup``s
+   Automatic OpenAPI documentation generation
+   Websockets support
+   Automatic generation of API clients based on the server definition

## A note on "automagic"

In general, *explicit is better than implicit*. To that end, annoliate tries its best to avoid automagically doing things. There is one exception to that, which is at the core of how annoliate works: using signature introspection to "automagically" plumb up parameter sources and sinks. It does this in three places:

+   Handler method argument signatures are used to automatically process and validate input parameters from the request and deliver them to the handler
+   Handler method return signatures are used to automatically process and validate responses and return them to the client
+   ``RouteGroup`` ``__init__`` signatures are used to automatically collect which setup parameters are needed to instantiate the app object and start the server. This is especially relevant for nested ``RouteGroup``s.

Note that the second point includes a tiny bit of magic in the ``Response`` object, which uses a ``ContextVar`` to tie the global ``Response`` name to the specific subclass created by the handler method's return signature.
