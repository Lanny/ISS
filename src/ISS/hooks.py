import uuid
import collections

def _default_ctx_generator(*args, **kwargs):
    return {}

class Catch(object):
    def __init__(self, hook_name, ctx_generator=_default_ctx_generator,
                 template='empty_template.html'):
        self.hook_name = hook_name
        self.ctx_generator = ctx_generator
        self.template = template

        self._id = uuid.uuid4()

class _HookManager(object):
    catches = collections.defaultdict(list)

    def get_catches(self, hook_name):
        return self.catches[hook_name]

    def register_catch(self, catch):
        self.catches[catch.hook_name].append(catch)

    def get_ctx_for_hook(self, name, *args, **kwargs):
        ctxs = {}

        for catch in self.catches[name]:
            ctxs[catch._id] = catch.ctx_generator(*args, **kwargs)

        return ctxs

    def add_ctx_for_hook(self, ctx, hook_name, *args, **kwargs):
        ctx['_hooks_%s' % hook_name] = self.get_ctx_for_hook(
                hook_name,
                *args,
                **kwargs)

HookManager = _HookManager()
