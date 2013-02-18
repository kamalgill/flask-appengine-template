# -*- coding: utf-8 -*-
"""
    flask.ext.cache
    ~~~~~~~~~~~~~~

    Adds cache support to your application.

    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details
"""

__version__ = '0.10.1'
__versionfull__ = __version__

import uuid
import hashlib
import inspect
import exceptions
import functools
import warnings

from types import NoneType

from werkzeug import import_string
from flask import request, current_app

def function_namespace(f, args=None):
    """
    Attempts to returns unique namespace for function
    """
    m_args = inspect.getargspec(f)[0]

    if len(m_args) and args:
        if m_args[0] == 'self':
            return '%s.%s.%s' % (f.__module__, args[0].__class__.__name__, f.__name__)
        elif m_args[0] == 'cls':
            return '%s.%s.%s' % (f.__module__, args[0].__name__, f.__name__)

    if hasattr(f, 'im_func'):
        return '%s.%s.%s' % (f.__module__, f.im_class.__name__, f.__name__)
    elif hasattr(f, '__class__'):
        return '%s.%s.%s' % (f.__module__, f.__class__.__name__, f.__name__)
    else:
        return '%s.%s' % (f.__module__, f.__name__)

#: Cache Object
################

class Cache(object):
    """
    This class is used to control the cache objects.
    """

    def __init__(self, app=None, with_jinja2_ext=True, config=None):
        self.with_jinja2_ext = with_jinja2_ext
        self.config = config

        self.app = app
        if app is not None:
            self.init_app(app, config)

    def init_app(self, app, config=None):
        "This is used to initialize cache with your app object"
        if not isinstance(config, (NoneType, dict)):
            raise ValueError("`config` must be an instance of dict or NoneType")

        if config is None:
            config = self.config
        if config is None:
            config = app.config

        config.setdefault('CACHE_DEFAULT_TIMEOUT', 300)
        config.setdefault('CACHE_THRESHOLD', 500)
        config.setdefault('CACHE_KEY_PREFIX', None)
        config.setdefault('CACHE_MEMCACHED_SERVERS', None)
        config.setdefault('CACHE_DIR', None)
        config.setdefault('CACHE_OPTIONS', None)
        config.setdefault('CACHE_ARGS', [])
        config.setdefault('CACHE_TYPE', 'null')

        if config['CACHE_TYPE'] == 'null':
            warnings.warn("Flask-Cache: CACHE_TYPE is set to null, "
                          "caching is effectively disabled.")

        if self.with_jinja2_ext:
            from .jinja2ext import CacheExtension, JINJA_CACHE_ATTR_NAME

            setattr(app.jinja_env, JINJA_CACHE_ATTR_NAME, self)
            app.jinja_env.add_extension(CacheExtension)

        self._set_cache(app, config)

    def _set_cache(self, app, config):
        import_me = config['CACHE_TYPE']
        if '.' not in import_me:
            import backends

            try:
                cache_obj = getattr(backends, import_me)
            except AttributeError:
                raise ImportError("%s is not a valid FlaskCache backend" % (
                                  import_me))
        else:
            cache_obj = import_string(import_me)

        cache_args = config['CACHE_ARGS'][:]
        cache_options = dict(default_timeout= \
                             config['CACHE_DEFAULT_TIMEOUT'])

        if config['CACHE_OPTIONS']:
            cache_options.update(config['CACHE_OPTIONS'])

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['cache'] = cache_obj(
                app, config, cache_args, cache_options)

    @property
    def cache(self):
        app = self.app or current_app
        return app.extensions['cache']

    def get(self, *args, **kwargs):
        "Proxy function for internal cache object."
        return self.cache.get(*args, **kwargs)

    def set(self, *args, **kwargs):
        "Proxy function for internal cache object."
        self.cache.set(*args, **kwargs)

    def add(self, *args, **kwargs):
        "Proxy function for internal cache object."
        self.cache.add(*args, **kwargs)

    def delete(self, *args, **kwargs):
        "Proxy function for internal cache object."
        self.cache.delete(*args, **kwargs)

    def delete_many(self, *args, **kwargs):
        "Proxy function for internal cache object."
        self.cache.delete_many(*args, **kwargs)

    def get_many(self, *args, **kwargs):
        "Proxy function for internal cache object."
        return self.cache.get_many(*args, **kwargs)

    def set_many(self, *args, **kwargs):
        "Proxy function for internal cache object."
        self.cache.set_many(*args, **kwargs)

    def cached(self, timeout=None, key_prefix='view/%s', unless=None):
        """
        Decorator. Use this to cache a function. By default the cache key
        is `view/request.path`. You are able to use this decorator with any
        function by changing the `key_prefix`. If the token `%s` is located
        within the `key_prefix` then it will replace that with `request.path`

        Example::

            # An example view function
            @cache.cached(timeout=50)
            def big_foo():
                return big_bar_calc()

            # An example misc function to cache.
            @cache.cached(key_prefix='MyCachedList')
            def get_list():
                return [random.randrange(0, 1) for i in range(50000)]

            my_list = get_list()

        .. note::

            You MUST have a request context to actually called any functions
            that are cached.

        .. versionadded:: 0.4
            The returned decorated function now has three function attributes
            assigned to it. These attributes are readable/writable.

                **uncached**
                    The original undecorated function

                **cache_timeout**
                    The cache timeout value for this function. For a custom value
                    to take affect, this must be set before the function is called.

                **make_cache_key**
                    A function used in generating the cache_key used.

        :param timeout: Default None. If set to an integer, will cache for that
                        amount of time. Unit of time is in seconds.
        :param key_prefix: Default 'view/%(request.path)s'. Beginning key to .
                           use for the cache key.

                           .. versionadded:: 0.3.4
                               Can optionally be a callable which takes no arguments
                               but returns a string that will be used as the cache_key.

        :param unless: Default None. Cache will *always* execute the caching
                       facilities unless this callable is true.
                       This will bypass the caching entirely.
        """

        def decorator(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                #: Bypass the cache entirely.
                if callable(unless) and unless() is True:
                    return f(*args, **kwargs)

                cache_key = decorated_function.make_cache_key(*args, **kwargs)

                rv = self.get(cache_key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    self.cache.set(cache_key, rv,
                                   timeout=decorated_function.cache_timeout)
                return rv

            def make_cache_key(*args, **kwargs):
                if callable(key_prefix):
                    cache_key = key_prefix()
                elif '%s' in key_prefix:
                    cache_key = key_prefix % request.path
                else:
                    cache_key = key_prefix

                cache_key = cache_key.encode('utf-8')

                return cache_key

            decorated_function.uncached = f
            decorated_function.cache_timeout = timeout
            decorated_function.make_cache_key = make_cache_key

            return decorated_function
        return decorator

    def _memvname(self, funcname):
        return funcname + '_memver'

    def memoize_make_version_hash(self):
        return uuid.uuid4().bytes.encode('base64')[:6]

    def memoize_make_cache_key(self, make_name=None):
        """
        Function used to create the cache_key for memoized functions.
        """
        def make_cache_key(f, *args, **kwargs):
            fname = function_namespace(f, args)

            version_key = self._memvname(fname)
            version_data = self.get(version_key)

            if version_data is None:
                version_data = self.memoize_make_version_hash()
                self.cache.set(version_key, version_data)

            cache_key = hashlib.md5()

            #: this should have to be after version_data, so that it
            #: does not break the delete_memoized functionality.
            if callable(make_name):
                altfname = make_name(fname)
            else:
                altfname = fname

            if callable(f):
                keyargs, keykwargs = self.memoize_kwargs_to_args(f,
                                                                 *args,
                                                                 **kwargs)
            else:
                keyargs, keykwargs = args, kwargs

            try:
                updated = "{0}{1}{2}".format(altfname, keyargs, keykwargs)
            except AttributeError:
                updated = "%s%s%s" % (altfname, keyargs, keykwargs)

            cache_key.update(updated)
            cache_key = cache_key.digest().encode('base64')[:16]
            cache_key += version_data

            return cache_key
        return make_cache_key

    def memoize_kwargs_to_args(self, f, *args, **kwargs):
        #: Inspect the arguments to the function
        #: This allows the memoization to be the same
        #: whether the function was called with
        #: 1, b=2 is equivilant to a=1, b=2, etc.
        new_args = []
        arg_num = 0
        argspec = inspect.getargspec(f)

        args_len = len(argspec.args)
        for i in range(args_len):
            if i == 0 and argspec.args[i] in ('self', 'cls'):
                #: use the id of the class instance
                #: this supports instance methods for
                #: the memoized functions.
                arg = id(args[0])
                arg_num += 1
            elif argspec.args[i] in kwargs:
                arg = kwargs[argspec.args[i]]
            elif arg_num < len(args):
                arg = args[arg_num]
                arg_num += 1
            elif abs(i-args_len) <= len(argspec.defaults):
                arg = argspec.defaults[i-args_len]
                arg_num += 1
            else:
                arg = None
                arg_num += 1

            #: Attempt to convert all arguments to a
            #: hash/id or a representation?
            #: Not sure if this is necessary, since
            #: using objects as keys gets tricky quickly.
            # if hasattr(arg, '__class__'):
            #     try:
            #         arg = hash(arg)
            #     except:
            #         arg = repr(arg)

            #: Or what about a special __cacherepr__ function
            #: on an object, this allows objects to act normal
            #: upon inspection, yet they can define a representation
            #: that can be used to make the object unique in the
            #: cache key. Given that a case comes across that
            #: an object "must" be used as a cache key
            # if hasattr(arg, '__cacherepr__'):
            #     arg = arg.__cacherepr__

            new_args.append(arg)

        return tuple(new_args), {}

    def memoize(self, timeout=None, make_name=None, unless=None):
        """
        Use this to cache the result of a function, taking its arguments into
        account in the cache key.

        Information on
        `Memoization <http://en.wikipedia.org/wiki/Memoization>`_.

        Example::

            @cache.memoize(timeout=50)
            def big_foo(a, b):
                return a + b + random.randrange(0, 1000)

        .. code-block:: pycon

            >>> big_foo(5, 2)
            753
            >>> big_foo(5, 3)
            234
            >>> big_foo(5, 2)
            753

        .. versionadded:: 0.4
            The returned decorated function now has three function attributes
            assigned to it.

                **uncached**
                    The original undecorated function. readable only

                **cache_timeout**
                    The cache timeout value for this function. For a custom value
                    to take affect, this must be set before the function is called.

                    readable and writable

                **make_cache_key**
                    A function used in generating the cache_key used.

                    readable and writable


        :param timeout: Default None. If set to an integer, will cache for that
                        amount of time. Unit of time is in seconds.
        :param make_name: Default None. If set this is a function that accepts
                          a single argument, the function name, and returns a
                          new string to be used as the function name. If not set
                          then the function name is used.
        :param unless: Default None. Cache will *always* execute the caching
                       facilities unelss this callable is true.
                       This will bypass the caching entirely.

        .. versionadded:: 0.5
            params ``make_name``, ``unless``
        """

        def memoize(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                #: bypass cache
                if callable(unless) and unless() is True:
                    return f(*args, **kwargs)

                cache_key = decorated_function.make_cache_key(f, *args, **kwargs)

                rv = self.get(cache_key)
                if rv is None:
                    rv = f(*args, **kwargs)
                    self.cache.set(cache_key, rv,
                                   timeout=decorated_function.cache_timeout)
                return rv

            decorated_function.uncached = f
            decorated_function.cache_timeout = timeout
            decorated_function.make_cache_key = self.memoize_make_cache_key(make_name)
            decorated_function.delete_memoized = lambda: self.delete_memoized(f)

            return decorated_function
        return memoize

    def delete_memoized(self, f, *args, **kwargs):
        """
        Deletes the specified functions caches, based by given parameters.
        If parameters are given, only the functions that were memoized with them
        will be erased. Otherwise all versions of the caches will be forgotten.

        Example::

            @cache.memoize(50)
            def random_func():
                return random.randrange(1, 50)

            @cache.memoize()
            def param_func(a, b):
                return a+b+random.randrange(1, 50)

        .. code-block:: pycon

            >>> random_func()
            43
            >>> random_func()
            43
            >>> cache.delete_memoized('random_func')
            >>> random_func()
            16
            >>> param_func(1, 2)
            32
            >>> param_func(1, 2)
            32
            >>> param_func(2, 2)
            47
            >>> cache.delete_memoized('param_func', 1, 2)
            >>> param_func(1, 2)
            13
            >>> param_func(2, 2)
            47


        :param fname: Name of the memoized function, or a reference to the function.
        :param \*args: A list of positional parameters used with memoized function.
        :param \**kwargs: A dict of named parameters used with memoized function.

        .. note::

            Flask-Cache uses inspect to order kwargs into positional args when
            the function is memoized. If you pass a function reference into ``fname``
            instead of the function name, Flask-Cache will be able to place
            the args/kwargs in the proper order, and delete the positional cache.

            However, if ``delete_memozied`` is just called with the name of the
            function, be sure to pass in potential arguments in the same order
            as defined in your function as args only, otherwise Flask-Cache
            will not be able to compute the same cache key.

        .. note::

            Flask-Cache maintains an internal random version hash for the function.
            Using delete_memoized will only swap out the version hash, causing
            the memoize function to recompute results and put them into another key.

            This leaves any computed caches for this memoized function within the
            caching backend.

            It is recommended to use a very high timeout with memoize if using
            this function, so that when the version has is swapped, the old cached
            results would eventually be reclaimed by the caching backend.
        """
        if not callable(f):
            raise exceptions.DeprecationWarning("Deleting messages by relative name is no longer"
                          " reliable, please switch to a function reference"
                          " or use the full function import name")

        _fname = function_namespace(f, args)

        if not args and not kwargs:
            version_key = self._memvname(_fname)
            version_data = self.memoize_make_version_hash()
            self.cache.set(version_key, version_data)
        else:
            cache_key = f.make_cache_key(f.uncached, *args, **kwargs)
            self.cache.delete(cache_key)
