"""Markdown-to-paper mapping, shared by study reports and supporting documents."""
from html import escape, unescape
from pathlib import Path
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit, urlencode

from markdown_subset import blocks, render, safe_url


def document_sources(root, studies):
    """Explicit source allowlist, including the documents linked by study READMEs."""
    names = {'README.md', 'SECURITY.md', 'THIRD_PARTY_NOTICES.md', 'LICENSE-CC-BY-4.0.md'}
    for study in studies:
        prefix = 'studies/' + study['slug'] + '/'
        names.add(prefix + 'README.md')
        names.update(prefix + 'docs/' + n for n in
                     ('METHODS.md', 'LIMITATIONS.md', 'DATA_DICTIONARY.md', 'PROVENANCE.md', 'RESULTS.md'))
    return {name: str(Path(name).with_suffix('.html')).replace('/docs/', '/')
            if name.startswith('studies/') else str(Path(name).with_suffix('.html')) for name in sorted(names)}


def source_routes(root, studies):
    routes = document_sources(root, studies)
    for study in studies:
        prefix = 'studies/' + study['slug'] + '/'
        routes.update({prefix + 'report/REPORT.md': prefix + 'index.html',
                       prefix + 'web/index.html': prefix + 'index.html',
                       prefix + 'web/explore.html': prefix + 'explore.html',
                       prefix + 'data/results.json': prefix + 'results.json',
                       prefix + 'data/answers.json': prefix + 'answers.json',
                       prefix + 'config.json': prefix + 'results.json'})
    return routes


def link_mapper(source, output, routes, case_links=None):
    def link(url, label):
        parsed = urlsplit(safe_url(url))
        if parsed.scheme or not parsed.path:
            return url
        target = posixpath.normpath(posixpath.join(posixpath.dirname(source), parsed.path))
        if target.startswith(('../', '/')):
            raise ValueError('Link escapes publication tree: ' + url)
        if target == 'data/cases.json' and case_links and label in case_links:
            return 'explore.html?' + urlencode({'case': label, 'configuration': case_links[label]})
        if target in {'data/cases.json', 'data/visibility.json'} and output.startswith('studies/'):
            target = posixpath.dirname(output) + '/' + posixpath.basename(target)
        elif target in routes:
            target = routes[target]
        elif target.endswith('.md'):
            raise ValueError('No generated HTML route for Markdown link: ' + target)
        # Font links in the shared notice are deliberately written for the built site.
        path = posixpath.relpath(target, posixpath.dirname(output) or '.')
        return urlunsplit(('', '', path, parsed.query, parsed.fragment))
    return link


def load_figures(path):
    source = path.read_text()
    matches = list(re.finditer(r'<figure id="([a-z0-9-]+)"[^>]*>.*?</figure>', source, re.S))
    if re.sub(r'<figure id="([a-z0-9-]+)"[^>]*>.*?</figure>', '', source, flags=re.S).strip():
        raise ValueError('Unexpected content outside figure partials')
    figures = {m[1]: m[0] for m in matches}
    if len(figures) != len(matches): raise ValueError('Duplicate figure partial ID')
    if not figures: raise ValueError('Missing figure partials')
    return figures


def paper_page(template, content, output, study_slug, scripts=''):
    if template.count('<!--CONTENT-->') != 1:
        raise ValueError('Paper template must contain exactly one content slot')
    title = re.search(r'<h1\b[^>]*>(.*?)</h1>', content, re.S)
    if not title: raise ValueError('Paper page requires an H1 title')
    title = unescape(re.sub('<[^>]+>', '', title[1]))
    base = posixpath.dirname(output) or '.'
    root_path = posixpath.relpath('.', base)
    root = '' if root_path == '.' else root_path + '/'
    study_path = posixpath.relpath('studies/' + study_slug, base)
    study = '' if study_path == '.' else study_path + '/'
    page = template.replace('{{title}}', escape(title)).replace('{{root}}', root).replace('{{study}}', study)
    if output == 'studies/' + study_slug + '/index.html':
        page = page.replace('href="' + study + 'index.html"',
                            'href="' + study + 'index.html" aria-current="page"', 1)
    page = page.replace('<!--PAGE-SCRIPTS-->', scripts)
    # Substitute content last: document text must never be interpreted as a template.
    return page.replace('<!--CONTENT-->', content)


def back_to_report(output, study_slug):
    """Link line placed above a study document's own title; the document HTML itself is unchanged."""
    href = posixpath.relpath('studies/' + study_slug + '/index.html', posixpath.dirname(output) or '.')
    return '<p class="doc-back"><a href="' + escape(href, quote=True) + '">← Back to the report</a></p>\n'


def report_content(source, figures, link):
    rendered = blocks(source, link=link, figures=figures)
    if [kind for kind, _ in rendered[:3]] != ['h1', 'p', 'p']:
        raise ValueError('Report must begin with a title, affiliation and abstract')
    title, affiliation, abstract = (body for _, body in rendered[:3])
    affiliation = affiliation.replace('<p data-report>', '<p class="affiliation" data-report>', 1)
    return ('<div class="title-block"><p class="eyebrow">d20 Bench · Study 1</p>' + title +
            affiliation + '<hr></div>\n<div class="abstract">' + abstract + '</div>\n' +
            '\n'.join(body for _, body in rendered[3:]))


def rewrite_html_links(page, output, generated):
    """Map copied explorer/root links without interpreting any of their scripts."""
    def rewrite(match):
        url = unescape(match[2]); parsed = urlsplit(url)
        if parsed.scheme or not parsed.path.endswith('.md'): return match[0]
        target = posixpath.normpath(posixpath.join(posixpath.dirname(output), parsed.path))
        html_target = str(Path(target).with_suffix('.html'))
        if html_target not in generated: raise ValueError('Missing HTML target: ' + target)
        path = posixpath.relpath(html_target, posixpath.dirname(output) or '.')
        dest = urlunsplit(('', '', path, parsed.query, parsed.fragment))
        return 'href=' + match[1] + escape(dest, quote=True) + match[1]
    return re.sub(r'href=([\'"])(.*?)\1', rewrite, page)
