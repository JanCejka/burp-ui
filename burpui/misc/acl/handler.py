# -*- coding: utf8 -*-
import os

from .interface import BUIacl, BUIaclLoader

from importlib import import_module
from six import iteritems
from collections import OrderedDict


class ACLloader(BUIaclLoader):
    def __init__(self, app=None):
        """See :func:`burpui.misc.acl.interface.BUIaclLoader.__init__`

        :param app: Application context
        :type app: :class:`burpui.server.BUIServer`
        """
        self.app = app
        self._acl = ACLhandler(self)
        backends = []
        self.errors = {}
        if self.app.acl_engine and 'none' not in self.app.acl_engine:
            me, _ = os.path.splitext(os.path.basename(__file__))
            back = self.app.acl_engine
            for au in back:
                if au == me:
                    self.app.logger.critical('Recursive import not permitted!')
                    continue
                try:
                    (modpath, _) = __name__.rsplit('.', 1)
                    mod = import_module('.' + au, modpath)
                    obj = mod.ACLloader(self.app)
                    backends.append(obj)
                except:
                    import traceback
                    self.errors[au] = traceback.format_exc()
        for name, plugin in iteritems(self.app.plugin_manager.get_plugins_by_type('acl')):
            try:
                obj = plugin.ACLloader(self.app)
                backends.append(obj)
            except:
                import traceback
                self.errors[name] = traceback.format_exc()
        backends.sort(key=lambda x: x.priority, reverse=True)
        if not backends:
            raise ImportError(
                'No backend found for \'{}\':\n{}'.format(self.app.auth,
                                                          self.errors)
            )
        for name, err in iteritems(self.errors):
            self.app.logger.error(
                'Unable to load module {}:\n{}'.format(repr(name), err)
            )
        self.backends = OrderedDict()
        for obj in backends:
            self.backends[obj.name] = obj

    @property
    def acl(self):
        return self._acl


class ACLhandler(BUIacl):
    """See :class:`burpui.misc.acl.interface.BUIacl`"""
    def __init__(self, loader=None):
        """:func:`burpui.misc.acl.interface.BUIacl.__init__` instanciate ACL
        engine.

        :param loader: ACL loader
        :type loader: :class:`burpui.misc.acl.handler.ACLloader`
        """
        self.loader = loader

    def _iterate_through_loader(self, method, *args, **kwargs):
        ret = None
        for _, acl_engine in iteritems(self.loader.backends):
            func = getattr(acl_engine.acl, method)
            ret = func(*args, **kwargs)
            if ret:
                break
        return ret

    def is_admin(self, username=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_admin`"""
        ret = self._iterate_through_loader('is_admin', username) or False
        return ret

    def is_moderator(self, username=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_moderator`"""
        ret = self._iterate_through_loader('is_moderator', username) or False
        return ret

    def is_client_allowed(self, username=None, client=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_client_allowed`"""
        ret = self._iterate_through_loader(
            'is_client_allowed',
            username,
            client,
            server
        ) or False
        return ret

    def is_server_allowed(self, username=None, server=None):
        """See :func:`burpui.misc.acl.interface.BUIacl.is_server_allowed`"""
        ret = self._iterate_through_loader(
            'is_server_allowed',
            username,
            server
        ) or False
        return ret
