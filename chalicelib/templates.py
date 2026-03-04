import os
from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateRenderer:
	def __init__(self):
		template_dir = os.path.join(os.path.dirname(__file__), "templates")
		self._env = Environment(
			loader=FileSystemLoader(template_dir),
			autoescape=select_autoescape(["html", "xml"]),
		)

	def render(self, name, **context):
		return self._env.get_template(name).render(**context)
