"""Report publication contracts: Markdown sources, frozen arithmetic, local assets."""
import importlib.util
import re
import tempfile
import unittest
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT/'scripts/publication.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
STUDY = p.studies(ROOT)[0]
STUDY_ROOT = p.study_path(ROOT, STUDY)

class ReportTable(HTMLParser):
 def __init__(self):
  super().__init__(); self.active=False; self.rows=[]; self.cell=None; self.bold=[]
 def handle_starttag(self, tag, attrs):
  if tag=='div' and 'data-report-table' in dict(attrs):self.active=True
  if not self.active:return
  if tag=='tr':self.rows.append([]);self.bold.append(0)
  if tag=='strong':self.bold[-1]+=1
  if tag in {'td','th'}:self.cell=''
 def handle_data(self, text):
  if self.active and self.cell is not None:self.cell+=text
 def handle_endtag(self, tag):
  if tag in {'td','th'} and self.cell is not None:self.rows[-1].append(self.cell);self.cell=None
  if tag=='table':self.active=False

def rounded(value, places):
 return str(Decimal(str(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))

class ReportPageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.site_dir=tempfile.TemporaryDirectory()
  cls.site=p.build(output=Path(cls.site_dir.name))
 @classmethod
 def tearDownClass(cls):cls.site_dir.cleanup()
 def built_report(self):return (self.site/'studies'/STUDY['slug']/'index.html').read_text()

 def test_only_named_woff2_files_are_releasable(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'studies').mkdir();(root/'studies/registry.json').write_bytes((ROOT/'studies/registry.json').read_bytes())
   fonts=root/'web/fonts';fonts.mkdir(parents=True)
   font=fonts/'unexpected.woff2';font.write_bytes(b'wOF2extra')
   with self.assertRaisesRegex(ValueError,'Unexpected font asset'):p.scan_public(root,[])
   font.unlink();(fonts/'newsreader-normal.woff2').write_bytes(b'wrong format')
   with self.assertRaisesRegex(ValueError,'Invalid WOFF2'):p.scan_public(root,[])

 def test_display_rounding_uses_stored_decimals(self):
  for value,expected in [(892.55,'892.6'),(5193.15,'5,193.2'),(1832.55,'1,832.6')]:self.assertEqual(p.fmt(value),expected)
  self.assertEqual(p.fmt(99.075,2),'99.08')
  self.assertEqual(p.fmt(None),'unknown')

 def test_internal_documents_stay_out_of_generated_site(self):
  excluded={'NOW.html','PUBLICATION.html','docs/README.html','docs/INTERFACE_STYLE.html'}
  excluded.update('docs/decisions/'+path.stem+'.html' for path in (ROOT/'docs/decisions').glob('*.md'))
  allowed=p.generated_paths(ROOT)
  self.assertTrue(excluded.isdisjoint(allowed))
  self.assertTrue((self.site/'SECURITY.html').is_file())
  for name in excluded:self.assertFalse((self.site/name).exists(),name)
  manifest=p.read(self.site/'manifest.json')
  for name in ('NOW.md','PUBLICATION.md','docs/README.md','docs/INTERFACE_STYLE.md'):
   self.assertNotIn(name,manifest['source_files'])
  for page in self.site.rglob('*.html'):
   for href in re.findall(r'href=[\'"]([^\'"]+)',page.read_text()):
    self.assertNotIn('127.0.0.1',href)
    target=(page.parent/href.split('#')[0].split('?')[0]).resolve()
    self.assertNotIn(str(target.relative_to(self.site)) if target.is_relative_to(self.site) else '',excluded)

 def test_comparison_labels_precision_and_source_traceability(self):
  import csv
  study=self.site/'studies'/STUDY['slug']
  results=p.read(STUDY_ROOT/'data/results.json')
  comparison=(study/'comparison.html').read_text()
  expected={'qwen3.8-27b/on':'on (low)','k2-horizon-3.7b/low':'low','muse-glimmer/low':'low'}
  for cfg in results['configurations']:
   expected_mode=expected.get(cfg['id'],cfg['id'].split('/')[1])
   self.assertEqual(p.display_mode(cfg['id']),expected_mode)
   self.assertIn('<td>'+expected_mode+'</td>',comparison)
  with (study/'comparison.csv').open() as f:rows=list(csv.DictReader(f))
  parser=ReportTable();parser.feed(comparison)
  self.assertEqual(len(parser.rows),51)
  for cell,row,rendered in zip(sorted(results['cells'],key=lambda c:(p.configuration_order(next(g for g in results['configurations'] if g['id']==c['configuration'])),c['condition'])),rows,parser.rows[1:]):
   self.assertEqual(float(row['mean_seconds']),cell['timing']['mean_seconds'])
   for index,key in enumerate(('mean_seconds','median_seconds','p25_seconds','p75_seconds','p95_seconds'),7):
    self.assertEqual(rendered[index],p.fmt(cell['timing'][key],2))
  self.assertEqual((study/'results.json').read_bytes(),(STUDY_ROOT/'data/results.json').read_bytes())
  for text in ('An answer is fully correct when it satisfies every required claim and contains no material error.',
               'The p95 is the slower end of the distribution, where 1 request in 20 is slower.',
               'on (low) means thinking on at low effort'):
   self.assertIn(text,comparison)
   self.assertIn(text,(study/'explore.html').read_text())
  figures=p.load_figures(STUDY_ROOT/'web/figures.html')
  for figure in figures.values():self.assertIn('on (low)',figure)
  self.assertNotIn('Qwen3.8 27B · on</th>',self.built_report())

 def test_authored_oracle_table_matches_all_full_suite_cells(self):
  text=self.built_report();parser=ReportTable();parser.feed(text)
  results=p.read(STUDY_ROOT/'data/results.json');configs={c['id']:c for c in results['configurations']}
  cells=sorted([c for c in results['cells'] if c['condition']=='supplied_passage'],key=lambda c:(-c['quality']['fully_correct'],c['timing']['median_seconds']))
  self.assertEqual(len(parser.rows),26)
  for row,cell,bold in zip(parser.rows[1:],cells,parser.bold[1:]):
   cfg=configs[cell['configuration']];q=cell['quality'];t=cell['timing']
   with self.subTest(configuration=cfg['id']):
    self.assertEqual(row[0].lower(),cfg['size_class'])
    normalize=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
    self.assertEqual(re.sub(r'low$','',normalize(row[1])) if cfg['id']=='qwen3.8-27b/on' else normalize(row[1]),normalize(cfg['model']+' '+cfg['id'].split('/')[-1]))
    self.assertEqual([v.replace(',','') for v in row[2:]],[f"{q['fully_correct']}/{q['profile_assessed']}",rounded(t['median_seconds'],2),rounded(t['p95_seconds'],2),rounded(cell['output_tokens']['mean'],1)])
    self.assertEqual(bold,6 if t['median_seconds']<=5 else 0)
  qualified=[c for c in cells if c['timing']['median_seconds']<=5]
  self.assertEqual(len(qualified),10)
  self.assertEqual({c['configuration'] for c in qualified if c['quality']['fully_correct']>60},{'gemma4-26b-a4b/off','gemma4-e4b/off','gemma4-e2b/on'})
  self.assertEqual(min(qualified,key=lambda c:c['output_tokens']['mean'])['configuration'],'gemma4-26b-a4b/off')
  self.assertEqual(max(c['quality']['fully_correct'] for c in results['cells']),113)
  for cfg in configs:
   a=next(c for c in results['cells'] if c['configuration']==cfg and c['condition']=='no_source')
   b=next(c for c in cells if c['configuration']==cfg)
   self.assertGreater(b['quality']['mean_claim_score'],a['quality']['mean_claim_score'])
   for group,field in [('timing','median_seconds'),('output_tokens','mean'),('output_tokens','median')]:self.assertLess(b[group][field],a[group][field])

 def test_report_is_generated_with_four_figures_and_static_alternatives(self):
  text=self.built_report()
  self.assertNotIn('<!-- figure:',text)
  self.assertIn('href="index.html" aria-current="page"',text)
  self.assertIn('NUMERIC AUDIT',text)
  self.assertNotIn('<mark class="check"',text)
  self.assertIn('about 24–33 tokens per second for the dense roughly 30B models without speculative decoding',text)
  for name in ('oracle-effect','live-use-tradeoffs','thinking-returns','scores-and-errors'):
   self.assertIn(f'<figure id="{name}"',text)
   figure=text.split(f'<figure id="{name}"')[1].split('</figure>')[0]
   self.assertIn('<figcaption',figure)
   self.assertTrue('<table>' in figure or 'preceding' in figure or 'immediately above' in figure)
  for span in ('only three configurations met the 5-second median bar','The product question sets the speed target','The advantage of oracle passages in this study fits that pattern.','the rules passages the task authors used to write that question','the twenty-sided die'):
   self.assertIn(span,text)
  for merged in ('[2, 3]','[6, 7]'):self.assertIn(f'<a class="cite" href="#references">{merged}</a>',text)
  self.assertNotIn('excluded earlier',text)
  build_source=(ROOT/'scripts/publication.py').read_text()
  self.assertIn('report/REPORT.md',build_source)
  self.assertNotIn('[citation needed]',text)
  for ref in ['2101.03961','2401.04088','2005.11401','2412.21187']:
   self.assertIn('https://arxiv.org/abs/'+ref,text)
  self.assertEqual((STUDY_ROOT/'web/index.html').read_text().count('<!--CONTENT-->'),1)
  partials=p.load_figures(STUDY_ROOT/'web/figures.html')
  for figure in partials.values():self.assertIn(figure,text)
  js=(ROOT/'web/report-figures.js').read_text()
  self.assertEqual(js.count("fetch('results.json')"),1)
  self.assertNotIn('answers.json',js)
  for contract in ["addEventListener('focus'","addEventListener('mouseenter'",'q.profile_assessed','q.material_error_assessed','q.exact_claim_scores','t.recorded_cases','o.count','5 s target','30 s cutoff','60/120 (half)','reference half']:
   self.assertIn(contract,js)

 def test_no_native_tooltips_and_legend_matches_report_size_ranges(self):
  for page in (self.built_report(),(self.site/'studies'/STUDY['slug']/'explore.html').read_text()):
   self.assertIsNone(re.search(r'<[^>]+\stitle=',page))
  js=(ROOT/'web/report-figures.js').read_text()
  self.assertNotIn("'title'",js);self.assertIn('toPrecision(2)',js)
  results=p.read(STUDY_ROOT/'data/results.json')
  for size,expected in (('small','2.7–5.1'),('medium','8.0–9.7'),('large','24–31')):
   totals=[c['total_parameters']/1e9 for c in results['configurations'] if c['size_class']==size]
   two=lambda x:f'{x:#.2g}'.rstrip('.')  # JavaScript's toPrecision(2)
   self.assertEqual(two(min(totals))+'–'+two(max(totals)),expected)
  figures=(STUDY_ROOT/'web/figures.html').read_text()
  self.assertNotIn('circle, medium = square',figures);self.assertNotIn('Open markers are',figures)

 def test_fonts_licenses_styles_and_scripts_are_explicitly_hashed(self):
  with tempfile.TemporaryDirectory() as td:
   out=p.build(output=Path(td));manifest=p.read(out/'manifest.json');allowed=p.generated_paths(ROOT)
   for name in p.WEB_ASSETS:
    source=ROOT/'web'/name;target=out/'assets'/name
    self.assertEqual(source.read_bytes(),target.read_bytes())
    self.assertIn('assets/'+name,allowed)
    self.assertIn(source,p.release_paths(ROOT))
    self.assertEqual(manifest['files']['assets/'+name],p.sha(target))
    self.assertEqual(manifest['source_files']['web/'+name],p.sha(source))
   for name in ['Newsreader-LICENSE.txt','IBM-Plex-Mono-LICENSE.txt']:
    self.assertIn('SIL OPEN FONT LICENSE Version 1.1',(out/'assets/fonts'/name).read_text())
   css=(out/'assets/paper.css').read_text()
   asset_css=re.sub(r'url\("data:[^"]*"\)','',css)
   for url in re.findall(r'url\([\'"]?([^\)\'\"]+)',asset_css):
    if url.startswith('data:'):continue
    self.assertFalse(url.startswith('/'));self.assertNotIn('://',url)
    self.assertTrue((out/'assets'/url).is_file())
   for page in out.rglob('*.html'):
    text=page.read_text()
    self.assertIn('data-theme="dark"',text)
    self.assertIn('localStorage.theme',text)
    self.assertNotIn('prefers-color-scheme',text)
   for banned in ['system-ui','Inter,','position: sticky','border-radius: 9px','#253c32']:
    self.assertNotIn(banned,css)
   self.assertLess((out/'assets/paper.css').stat().st_size,22_000)
   self.assertLess((out/'assets/report-figures.js').stat().st_size,20_000)

 def test_case_links_are_public_and_target_the_lazy_explorer(self):
  html=self.built_report()
  queries=re.findall(r'href="explore.html\?([^"]+)"',html)
  links=[parse_qs(unescape(q))['case'][0] for q in queries]
  self.assertEqual(len(set(links)),5)
  self.assertTrue(set(links)<=set(p.read(ROOT/'data/visibility.json')['case_ids']))
  configs={c['id'] for c in p.read(STUDY_ROOT/'data/results.json')['configurations']}
  self.assertTrue(all(parse_qs(unescape(q))['configuration'][0] in configs for q in queries))
  explorer=(STUDY_ROOT/'web/explore.html').read_text()
  self.assertIn("new URLSearchParams(location.search).get('case')",explorer)
  self.assertIn('D.answerIndex[c.case_id]?.[cfg.id]',explorer)
  self.assertNotIn("loadJSON('answers.json')",explorer)

 def test_figures_dim_everything_but_the_focused_group(self):
  js=(ROOT/'web/report-figures.js').read_text();css=(ROOT/'web/paper.css').read_text()
  for contract in ['highlight(ctx, group)','unhighlight(ctx)','groupOf(cfg)',"addEventListener('mouseleave', hide)","addEventListener('blur', hide)"]:self.assertIn(contract,js)
  self.assertIn('svg.has-focus :is(.point, .trace, .track):not(.in-focus) { opacity: .2; }',css)
  reduced=css.index('prefers-reduced-motion: reduce) { .figure-chart');self.assertGreater(reduced,css.index('transition: opacity'))

 def test_supporting_pages_avoid_style_guide_patterns(self):
  pages=[ROOT/'README.md',ROOT/'web/index.html',STUDY_ROOT/'README.md',STUDY_ROOT/'web/explore.html',STUDY_ROOT/'web/figures.html',*sorted((STUDY_ROOT/'docs').glob('*.md'))]
  for page in pages:
   text=page.read_text()
   for banned in (', not ','rather than','does not replace','operator','condition cell','assessed denominator'):
    with self.subTest(page=page.name,banned=banned):self.assertNotIn(banned,text.lower())
  for page in (STUDY_ROOT/'docs/METHODS.md',STUDY_ROOT/'docs/PROVENANCE.md',STUDY_ROOT/'docs/DATA_DICTIONARY.md'):
   self.assertNotRegex(page.read_text(),r'\d+[–-]\d+ October')

if __name__=='__main__':unittest.main()
