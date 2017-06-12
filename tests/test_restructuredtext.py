# vim: ts=8:sts=8:sw=8:noexpandtab

# This file is part of python-markups test suite
# License: BSD
# Copyright: (C) Dmitry Shachnev, 2012-2014

from os import unlink
from os.path import exists
import re
import subprocess
from tempfile import NamedTemporaryFile
import unittest
from markups import ReStructuredTextMarkup

try:
	import sphinx
except ImportError:
	sphinx = None

try:
	dot_version = subprocess.check_output(['dot', '-V'], stderr=subprocess.STDOUT)
except OSError:
	dot_version = None

dot_available = dot_version and dot_version.startswith(b'dot - graphviz')

basic_text = \
'''Hello, world!
=============

Some subtitle
~~~~~~~~~~~~~

This is an example **reStructuredText** document.'''

filename_re = re.compile(r'<(?:object data|img src)="([a-zA-Z0-9/_-]+\.svg)"')

@unittest.skipUnless(ReStructuredTextMarkup.available(), 'Docutils not available')
class ReStructuredTextTest(unittest.TestCase):
	def test_basic(self):
		markup = ReStructuredTextMarkup()
		converted = markup.convert(basic_text)
		text = converted.get_document_body()
		title = converted.get_document_title()
		stylesheet = converted.get_stylesheet()
		text_expected = ('<div class="document" id="hello-world">\n'
			'<h1 class="title">Hello, world!</h1>\n'
			'<h2 class="subtitle" id="some-subtitle">Some subtitle</h2>\n'
			'<p>This is an example <strong>reStructuredText</strong> document.</p>\n'
			'</div>\n')
		title_expected = 'Hello, world!'
		self.assertEqual(text_expected, text)
		self.assertEqual(title_expected, title)
		self.assertIn('.code', stylesheet)

	def test_mathjax_loading(self):
		markup = ReStructuredTextMarkup()
		self.assertEqual('', markup.convert('Hello, world!').get_javascript())
		js = markup.convert('Hello, :math:`2+2`!').get_javascript()
		self.assertIn('<script', js)
		body = markup.convert('Hello, :math:`2+2`!').get_document_body()
		self.assertIn('<span class="math">', body)
		self.assertIn(r'\(2+2\)</span>', body)

	def test_errors(self):
		markup = ReStructuredTextMarkup('/dev/null',
		                                settings_overrides = {'warning_stream': False})
		body = markup.convert('`').get_document_body() # unclosed role
		self.assertIn('system-message', body)
		self.assertIn('/dev/null', body)

	def test_errors_overridden(self):
		markup = ReStructuredTextMarkup('/dev/null',
		                                settings_overrides = {'report_level': 4})
		body = markup.convert('`').get_document_body() # unclosed role
		self.assertNotIn('system-message', body)

	@unittest.skipUnless(sphinx, 'Sphinx not available')
	@unittest.skipUnless(dot_available, 'dot not available')
	def test_sphinx_digraph(self):
		markup = ReStructuredTextMarkup()
		converted = markup.convert('.. digraph:: GraphName\n\n   a -> b;')
		body = converted.get_document_body()
		self.assertRegexpMatches(body, filename_re)
		filename = filename_re.search(body).group(1)
		self.assertTrue(exists(filename))
		with open(filename) as svgfile:
			contents = svgfile.read(256)
		self.assertIn('<!-- Generated by graphviz', contents)
		self.assertIn('<!-- Title: GraphName', contents)

	@unittest.skipUnless(sphinx, 'Sphinx not available')
	@unittest.skipUnless(dot_available, 'dot not available')
	def test_sphinx_digraph_from_file(self):
		dotfile = NamedTemporaryFile(mode='w', delete=False,
		                             prefix='pymarkups-', suffix='.dot')
		dotfile.write('digraph GraphFromFile { a -> b; }')
		dotfile.close()
		markup = ReStructuredTextMarkup()
		converted = markup.convert('.. graphviz:: %s' % dotfile.name)
		body = converted.get_document_body()
		self.assertRegexpMatches(body, filename_re)
		filename = filename_re.search(body).group(1)
		self.assertTrue(exists(filename))
		with open(filename) as svgfile:
			contents = svgfile.read(256)
		self.assertIn('<!-- Generated by graphviz', contents)
		self.assertIn('<!-- Title: GraphFromFile', contents)
		unlink(dotfile.name)


if __name__ == '__main__':
	unittest.main()
