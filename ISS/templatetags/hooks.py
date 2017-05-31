from django import template
from django.template import Template, Variable, TemplateSyntaxError, loader

from ISS.hooks import HookManager

register = template.Library()

class HookNode(template.Node):
    def __init__(self, hook_name, manager=HookManager):
        self.hook_name = hook_name
        self.manager = manager

    def render(self, context):
        catch_outputs = []

        for catch in self.manager.get_catches(self.hook_name):
            template = loader.get_template(catch.template)
            c_ctx = context['_hooks_%s' % self.hook_name][catch._id]
            output = template.render(c_ctx)
            catch_outputs.append(output)

        return ''.join(catch_outputs)

def render_hook(parser, token):
    _, hook_name = token.split_contents()
    return HookNode(hook_name)

render_hook = register.tag(render_hook)
