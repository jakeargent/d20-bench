"""Strict, offline Markdown subset for publication sources (standard library only).

Supported: ATX headings, paragraphs, emphasis/strong, backtick code, inline
links and URL autolinks, flat lists with wrapped items, pipe tables, blockquotes,
fenced code and standalone HTML comments. Raw tags are displayed as text.
Unsupported Markdown syntax raises ValueError instead of losing source text.
"""
from html import escape
import re
from urllib.parse import urlsplit

FIGURE = re.compile(r'<!-- figure: ([a-z0-9]+(?:-[a-z0-9]+)*)(?: — [^\n]*)? -->')
LIST = re.compile(r'^( *)([-+*]|\d+[.)]) (.+)$')
HEADING = re.compile(r'^(#{1,6}) (.+)$')


def safe_url(url):
    if any(ord(c) < 32 or c.isspace() for c in url) or url.startswith('//'):
        raise ValueError('Unsupported link destination: ' + url)
    if urlsplit(url).scheme.lower() not in {'', 'http', 'https', 'mailto'}:
        raise ValueError('Unsupported link scheme: ' + url)
    return url


def inline(source, link=lambda url, label: url):
    """Render inline syntax, escaping text and attribute values independently."""
    out = []
    i = 0
    while i < len(source):
        rest = source[i:]
        if rest.startswith('![') or rest.startswith(('~~', '[^')):
            raise ValueError('Unsupported inline Markdown: ' + rest)
        if source[i] == '\\':
            if i + 1 == len(source) or source[i + 1].isalnum():
                raise ValueError('Unsupported Markdown escape: ' + rest)
            out.append(escape(source[i + 1])); i += 2; continue
        if source[i] == '`':
            ticks = re.match(r'`+', rest)[0]
            end = source.find(ticks, i + len(ticks))
            if end < 0:
                raise ValueError('Unclosed inline code: ' + source)
            out.append('<code>' + escape(source[i + len(ticks):end]) + '</code>')
            i = end + len(ticks); continue
        if source[i] == '[':
            end = source.find(']', i + 1)
            if end >= 0 and source[end + 1:end + 2] == '(':
                start = end + 2; close = start; depth = 1
                while close < len(source) and depth:
                    if source[close] == '(': depth += 1
                    if source[close] == ')': depth -= 1
                    close += 1
                if depth:
                    raise ValueError('Unclosed link: ' + source)
                label = source[i + 1:end]; url = source[start:close - 1]
                if '[' in label:
                    raise ValueError('Nested link labels are unsupported')
                url = safe_url(link(safe_url(url), label))
                # A bare number linking within the page is a citation marker: show it as [n].
                # Adjacent markers to the same anchor ("[2](#r), [3](#r)") merge into one: [2, 3].
                if re.fullmatch(r'\d+', label) and url.startswith('#'):
                    labels = [label]; same = re.compile(r', \[(\d+)\]\(' + re.escape(source[start:close - 1]) + r'\)')
                    while True:
                        more = same.match(source, close)
                        if not more: break
                        labels.append(more[1]); close = more.end()
                    out.append('<a class="cite" href="' + escape(url, quote=True) + '">[' + ', '.join(labels) + ']</a>')
                else:
                    out.append('<a href="' + escape(url, quote=True) + '">' + inline(label) + '</a>')
                i = close; continue
            if end >= 0 and (source[end + 1:end + 2] in {'[', ':'}):
                raise ValueError('Reference links are unsupported: ' + rest)
        auto = re.match(r'<(https?://[^<>\s]+|mailto:[^<>\s]+)>', rest)
        if auto:
            url = safe_url(link(auto[1], auto[1]))
            out.append('<a href="' + escape(url, quote=True) + '">' + escape(auto[1]) + '</a>')
            i += auto.end(); continue
        if source[i] in '*_' and not (source[i] == '_' and i and source[i - 1].isalnum()):
            marker = source[i] * (2 if rest.startswith(source[i] * 2) else 1)
            if rest.startswith(source[i] * 3):
                raise ValueError('Triple emphasis is unsupported: ' + rest)
            end = source.find(marker, i + len(marker))
            if end < 0 or not source[i + len(marker):end].strip():
                raise ValueError('Unclosed emphasis: ' + source)
            tag = 'strong' if len(marker) == 2 else 'em'
            out.append('<' + tag + '>' + inline(source[i + len(marker):end], link) + '</' + tag + '>')
            i = end + len(marker); continue
        out.append(escape(source[i])); i += 1
    return ''.join(out)


def table_cells(line):
    if not line.startswith('|') or not line.endswith('|'):
        raise ValueError('Pipe tables require outer pipes: ' + line)
    # Pipes within code or escaped text are not separators.
    cells = []; cell = ''; ticks = ''; i = 1
    while i < len(line) - 1:
        if line[i:i + 2] == '\\|':
            cell += '\\|'; i += 2; continue
        if line[i] == '`':
            token = re.match(r'`+', line[i:])[0]
            if not ticks: ticks = token
            elif ticks == token: ticks = ''
            cell += token; i += len(token); continue
        if line[i] == '|' and not ticks:
            cells.append(cell.strip()); cell = ''
        else:
            cell += line[i]
        i += 1
    cells.append(cell.strip())
    return cells


def blocks(source, link=lambda url, label: url, figures=None):
    """Return (kind, HTML) blocks. Each supplied figure must occur exactly once."""
    figures = {} if figures is None else figures
    seen = set(); ids = {}; result = []; lines = source.splitlines(); i = 0
    def add(kind, body): result.append((kind, body))
    def special(line):
        return (HEADING.match(line) or LIST.match(line) or
                line.startswith(('<!--', '>', '```', '~~~', '|')))
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        if line != line.lstrip():
            raise ValueError(f'Unsupported indentation at line {i + 1}: {line}')
        if line.startswith('<!--'):
            comment = [line]; i += 1
            while '-->' not in comment[-1] and i < len(lines):
                comment.append(lines[i]); i += 1
            text = '\n'.join(comment)
            if not text.endswith('-->') or '--' in text[4:-3] or '>' == text[4:5]:
                raise ValueError('Malformed HTML comment')
            match = FIGURE.fullmatch(text)
            if match:
                name = match[1]
                if name not in figures: raise ValueError('Unknown figure placeholder: ' + name)
                if name in seen: raise ValueError('Duplicate figure placeholder: ' + name)
                seen.add(name); add('figure', figures[name])
            elif re.search(r'figure\s*:', text):
                raise ValueError('Malformed figure placeholder: ' + text)
            else: add('comment', text)
            continue
        fence = re.fullmatch(r'(`{3,}|~{3,})([\w+-]*)', line)
        if fence:
            code = []; i += 1
            while i < len(lines) and lines[i] != fence[1]: code.append(lines[i]); i += 1
            if i == len(lines): raise ValueError('Unclosed code fence')
            css = ' class="language-' + escape(fence[2], quote=True) + '"' if fence[2] else ''
            add('code', '<pre><code' + css + '>' + escape('\n'.join(code) + '\n') + '</code></pre>')
            i += 1; continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading[1]); text = heading[2]
            if re.search(r'\s#+$|\{#[^}]+\}$', text): raise ValueError('Unsupported heading suffix')
            ident = re.sub(r'[^\w\s-]', '', text.lower()); ident = re.sub(r'\s+', '-', ident)
            ids[ident] = ids.get(ident, 0) + 1
            ident += '-' + str(ids[ident]) if ids[ident] > 1 else ''
            add('h' + str(level), f'<h{level} id="{escape(ident, quote=True)}" data-report>{inline(text, link)}</h{level}>')
            i += 1; continue
        if line.startswith('|'):
            header = table_cells(line); i += 1
            if i == len(lines): raise ValueError('Missing table separator')
            align = table_cells(lines[i]); i += 1
            if len(align) != len(header) or not all(re.fullmatch(r':?-{3,}:?', c) for c in align):
                raise ValueError('Invalid pipe table separator')
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                row = table_cells(lines[i]); i += 1
                if len(row) != len(header): raise ValueError('Inconsistent pipe table width')
                rows.append(row)
            def cells(row, tag):
                return ''.join('<' + tag + (' scope="col"' if tag == 'th' else '') +
                    (' class="num"' if a.endswith(':') and not a.startswith(':') else '') +
                    '>' + inline(c, link) + '</' + tag + '>' for c, a in zip(row, align))
            add('table', '<div class="report-table" data-report-table><div class="scroll" tabindex="0" role="region" aria-label="Data table"><table><thead><tr>' + cells(header, 'th') + '</tr></thead><tbody>' + ''.join('<tr>' + cells(r, 'td') + '</tr>' for r in rows) + '</tbody></table></div></div>')
            continue
        item = LIST.match(line)
        if item:
            ordered = item[2][0].isdigit(); items = []; start = int(re.match(r'\d+', item[2])[0]) if ordered else 1
            while i < len(lines):
                item = LIST.match(lines[i])
                if not item: break
                if item[1] or item[2][0].isdigit() != ordered: raise ValueError('Nested/mixed lists are unsupported')
                if re.match(r'\[[ xX]\] ', item[3]): raise ValueError('Task lists are unsupported')
                parts = [item[3]]; i += 1
                while i < len(lines) and lines[i].strip() and not special(lines[i]):
                    if lines[i].startswith('    '): raise ValueError('Nested lists/indented code are unsupported')
                    parts.append(lines[i].strip()); i += 1
                items.append('<li data-report>' + inline(' '.join(parts), link) + '</li>')
            tag = 'ol' if ordered else 'ul'
            attr = f' start="{start}"' if ordered and start != 1 else ''
            add('list', '<' + tag + attr + '>' + ''.join(items) + '</' + tag + '>'); continue
        if line.startswith('>'):
            quote = []
            while i < len(lines) and lines[i].startswith('>'):
                quote.append(lines[i][1:].removeprefix(' ')); i += 1
            add('quote', '<blockquote>' + '\n'.join(body for _, body in blocks('\n'.join(quote), link)) + '</blockquote>'); continue
        if re.match(r'^(?:[-*_]\s*){3,}$|^={3,}$|^#{1,6}(?:$|[^ ])|^```|^~~~', line):
            raise ValueError('Unsupported Markdown block: ' + line)
        para = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not special(lines[i]):
            if lines[i].startswith('    ') or re.fullmatch(r'[-=]{3,}', lines[i]):
                raise ValueError('Indented code/setext headings are unsupported')
            para.append(lines[i]); i += 1
        if any(x.endswith(('  ', '\\')) for x in para): raise ValueError('Hard line breaks are unsupported')
        add('p', '<p data-report>' + inline(' '.join(para), link) + '</p>')
    missing = set(figures) - seen
    if missing: raise ValueError('Missing figure placeholders: ' + ', '.join(sorted(missing)))
    return result


def render(source, **kwargs):
    return '\n'.join(body for _, body in blocks(source, **kwargs))
