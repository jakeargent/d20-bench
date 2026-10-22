"""Source preservation, strict failure and generated documentation routes."""
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from urllib.parse import urlsplit, urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from markdown_subset import render, inline
from paper_pages import blocks, report_content, link_mapper
spec = importlib.util.spec_from_file_location('publication', ROOT / 'scripts/publication.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.words = []; self.links = []
    def handle_data(self, data): self.words.append(data)
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'}: self.links.append(value)


class MarkdownTests(unittest.TestCase):
    def test_figure_position_and_all_placeholders_required_once(self):
        figure = '<figure id="sample"><figcaption>Caption</figcaption></figure>'
        for marker in ['<!-- figure: sample -->', '<!-- figure: sample — source description -->']:
            self.assertEqual(render('Before.\n\n' + marker + '\n\nAfter.', figures={'sample': figure}),
                             '<p data-report>Before.</p>\n' + figure + '\n<p data-report>After.</p>')
        for source, message in [('<!-- figure: unknown -->', 'Unknown figure'),
                                ('No marker.', 'Missing figure'),
                                ('<!-- figure: sample -->\n<!-- figure: sample -->', 'Duplicate figure'),
                                ('<!-- figure: sample-->', 'Malformed figure')]:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, message):
                render(source, figures={'sample': figure})

    def test_escaping_code_links_comments_and_unsafe_schemes(self):
        self.assertEqual(inline('<script> & "quoted"'), '&lt;script&gt; &amp; &quot;quoted&quot;')
        self.assertEqual(inline('`<b>&`'), '<code>&lt;b&gt;&amp;</code>')
        self.assertEqual(inline('[A & B](https://example.com/?a=1&b="2")'),
                         '<a href="https://example.com/?a=1&amp;b=&quot;2&quot;">A &amp; B</a>')
        self.assertEqual(render('<!-- harmless -->'), '<!-- harmless -->')
        self.assertIn('&lt;/script&gt;', render('```html\n</script>\n```'))
        for source in ['[x](javascript:alert(1))', '[x](data:text/html,test)', '[x](//example.com)',
                       '[x](https://example.com/ spaced)', '<!-- bad -- comment -->']:
            with self.subTest(source=source), self.assertRaises(ValueError): render(source)

    def test_numeric_in_page_links_are_bracketed_citation_markers(self):
        self.assertEqual(inline('speed [1](#references).'), 'speed <a class="cite" href="#references">[1]</a>.')
        self.assertEqual(inline('speed [2](#references), [3](#references), [5](#references).'),
                         'speed <a class="cite" href="#references">[2, 3, 5]</a>.')
        self.assertEqual(inline('[1](#references) and [2](#references)'),
                         '<a class="cite" href="#references">[1]</a> and <a class="cite" href="#references">[2]</a>')
        self.assertEqual(inline('[1](#references), [2](#other)'),
                         '<a class="cite" href="#references">[1]</a>, <a class="cite" href="#other">[2]</a>')
        self.assertEqual(inline('[1](https://example.com/)'), '<a href="https://example.com/">1</a>')
        self.assertEqual(inline('[Methods](#methods)'), '<a href="#methods">Methods</a>')

    def test_supported_blocks_preserve_structure(self):
        text = '# Title\n\n## Section\n\n**Strong** and *emphasis* and _more_ with `a_b`.\n\n2. Second\n3. Third\n\n- Item\n  continued\n- Next\n\n> Quoted **words**\n\n| Name | Value |\n|---|---:|\n| a | 2 |\n\n<https://example.com/>\n'
        html = render(text)
        for span in ['id="section"', '<strong>Strong</strong>', '<em>emphasis</em>', '<em>more</em>',
                     '<code>a_b</code>', '<ol start="2">', '<ul>', 'Item continued', '<blockquote>',
                     '<th scope="col" class="num">Value</th>', '<td class="num">2</td>',
                     'href="https://example.com/"']:
            self.assertIn(span, html)
        self.assertIn('<code>a|b</code>', render('| A |\n|---|\n| `a|b` |'))
        self.assertIn('a|b', render('| A |\n|---|\n| a\\|b |'))

    def test_unsupported_constructs_fail_loudly(self):
        for text in ['![alt](image.png)', '[text][ref]', '~~deleted~~', '[^note]: footnote',
                     '- [x] task', '- parent\n  - nested', '    indented code',
                     'Title\n===', '---', '***combined***', '```\nno end', '*unclosed',
                     '| A | B |\n|---|---|\n| missing |', 'line  \nbreak']:
            with self.subTest(text=text), self.assertRaises(ValueError): render(text)

    def test_unknown_internal_markdown_route_fails(self):
        with self.assertRaisesRegex(ValueError, 'No generated HTML route'):
            render('[Missing](MISSING.md)', link=link_mapper('docs/A.md', 'docs/A.html', {}))


class GeneratedPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.site = p.build(output=Path(cls.temp.name))
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_docs_sources_are_rendered_without_prose_changes(self):
        study = p.studies(ROOT)[0]; dest = p.study_path(ROOT, study)
        prefix = 'studies/' + study['slug'] + '/'
        for filename in sorted(p.STUDY_DOCS):
            output = self.site / prefix / filename.replace('.md', '.html')
            html = output.read_text()
            expected = render((dest / 'docs' / filename).read_text(),
                              link=p.link_mapper(prefix + 'docs/' + filename, prefix + output.name,
                                                 p.source_routes(ROOT, p.studies(ROOT))))
            self.assertIn(expected, html)
            for span in ['site-header', 'site-footer', 'theme-toggle', 'assets/paper.css']:
                self.assertIn(span, html)
            self.assertIn('<p class="doc-back"><a href="index.html">← Back to the report</a></p>', html)
        report = (self.site / prefix / 'index.html').read_text()
        self.assertNotIn('doc-back', report)
        self.assertIn('<a class="cite" href="#references">[1]</a>', report)
        for filename in ['METHODS.html', 'LIMITATIONS.html', 'DATA_DICTIONARY.html', 'PROVENANCE.html', 'README.html']:
            self.assertIn('href="' + filename + '"', report)
        readme = (self.site / prefix / 'README.html').read_text()
        self.assertIn('href="RESULTS.html"', readme)
        self.assertIn('href="index.html"', readme)
        explorer = (self.site / prefix / 'explore.html').read_text()
        self.assertIn('href="METHODS.html"', explorer)
        self.assertIn('href="DATA_DICTIONARY.html"', explorer)

    def test_all_built_pages_have_resolving_local_links_and_no_raw_markdown_links(self):
        for page in self.site.rglob('*.html'):
            parsed = Text(); parsed.feed(page.read_text())
            for url in parsed.links:
                parts = urlsplit(url)
                if parts.scheme or parts.netloc: continue  # External model-card URLs stay exact.
                with self.subTest(page=page.relative_to(self.site), url=url):
                    self.assertFalse(parts.path.endswith('.md'))
                    target = (page.parent / parts.path).resolve() if parts.path else page
                    self.assertTrue(target.is_relative_to(self.site))
                    self.assertTrue(target.is_file(), url)
                    if parts.fragment and target.suffix == '.html':
                        self.assertRegex(target.read_text(), r'id="' + re.escape(parts.fragment) + '"')

    def test_markdown_edits_drive_rebuild_and_sources_are_manifested(self):
        # A complete isolated fixture verifies the source-of-truth contract end to end.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for source in p.release_paths(ROOT):
                target = root / source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
            study = p.studies(root)[0]; dest = p.study_path(root, study)
            source = dest / 'report/REPORT.md'
            source.write_text(source.read_text().replace('## References', 'Operator edit survives <angle> & ampersand.\n\n## References'))
            out = p.build(root, root / 'site'); page = out / 'studies' / study['slug'] / 'index.html'
            self.assertIn('Operator edit survives &lt;angle&gt; &amp; ampersand.', page.read_text())
            manifest = p.read(page.parent / 'manifest.json')['source_files']
            for suffix in ['report/REPORT.md', 'web/index.html', 'web/figures.html', 'web/report-links.json']:
                path = 'studies/' + study['slug'] + '/' + suffix
                self.assertEqual(manifest[path], p.sha(root / path))
            self.assertEqual(manifest['scripts/markdown_subset.py'], p.sha(root / 'scripts/markdown_subset.py'))
            source.write_text(source.read_text().replace('<!-- figure: oracle-effect', '<!-- figure: unknown-effect'))
            with self.assertRaisesRegex(ValueError, 'Unknown figure placeholder'): p.build(root, root / 'site')


if __name__ == '__main__': unittest.main()
