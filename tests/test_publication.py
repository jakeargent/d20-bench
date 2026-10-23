import shutil,copy,csv,importlib.util,json,re,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('publication',ROOT/'scripts/publication.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
STUDY=p.studies(ROOT)[0]
STUDY_ROOT=p.study_path(ROOT,STUDY)

def fixture(root,full=False):
 (root/'studies').mkdir(parents=True,exist_ok=True)
 shutil.copyfile(ROOT/'studies/registry.json',root/'studies/registry.json')
 if full:
  shutil.copytree(ROOT/'data',root/'data')
  shutil.copytree(STUDY_ROOT,p.study_path(root,STUDY))
  shutil.copytree(ROOT/'web',root/'web')
  shutil.copytree(ROOT/'scripts',root/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
  shutil.copyfile(ROOT/'THIRD_PARTY_NOTICES.md',root/'THIRD_PARTY_NOTICES.md')
  for name in p.SITE_NOTICES|{'SECURITY.md'}:shutil.copyfile(ROOT/name,root/name)
 return root

class SiteReferences(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):
  self.urls.extend(value for key,value in attrs if key in {'href','src'} and value is not None)

class DataExportTests(unittest.TestCase):
 def row(self):
  return {'configuration':'test','case_id':'public','condition':'no_source','candidate_answer':'answer','candidate_input_sha256':'hash','score':{'earned_points':25,'complete_task_success':True,'has_material_error':False},'annotation':{'claims':[{'claim_id':'C004','status':'uncertain','earned_points':None,'reason':'original'}]},'human_adjudication':{'scope':'claim_C004','claim_id':'C004','status':'met','points':25,'private_comment':'DO_NOT_PUBLISH'}}
 def test_human_claim_override_and_original_annotation_both_preserved(self):
  r=self.row();b=copy.deepcopy(r);y=p.project_answer(r,'source')
  self.assertEqual(y['claim_awards'][0]['earned_points'],25)
  self.assertIsNone(y['expert_annotation']['claims'][0]['earned_points'])
  self.assertNotIn('DO_NOT_PUBLISH',json.dumps(y));self.assertEqual(r,b)
 def test_unknown_flag_fails_closed(self):
  r=self.row();r['operational_flags']=['UNREVIEWED_FLAG']
  with self.assertRaises(ValueError):p.project_answer(r,'b')
 def test_private_path_and_private_address_redacted(self):
  secret_path='/'+'home/'+'private/file';address='192.'+'168.'+'7.'+'8';v=p.clean_text(secret_path+' '+address)
  self.assertNotIn(secret_path,v);self.assertNotIn(address,v)
 def test_numeric_aggregate_rejects_text(self):
  with self.assertRaises(ValueError):p.safe_tree({'unexpected':'PRIVATE_TEXT'})
 def test_private_aggregate_key_rejected(self):
  with self.assertRaises(ValueError):p.safe_tree({'PRIVATE_TEXT':1})
 def test_ignored_environment_symlinks_are_not_released(self):
  with tempfile.TemporaryDirectory() as td:
   root=fixture(Path(td));(root/'.venv').mkdir();(root/'.venv/python').symlink_to(Path(sys.executable));self.assertEqual(p.release_paths(root),[root/'studies/registry.json'])
 def test_bad_claim_arithmetic_rejected(self):
  r=self.row();r['score']['earned_points']=90
  with self.assertRaises(ValueError):p.project_answer(r,'b')
 def test_release_allowlist_excludes_unlisted_files(self):
  with tempfile.TemporaryDirectory() as td:
   r=fixture(Path(td));(r/'README.md').write_text('ok');(r/'raw').mkdir();(r/'raw/answers.json').write_text('secret');(r/'data').mkdir();(r/'data/public.json').write_text('{}');(r/'docs').mkdir();(r/'docs/WRITING_STYLE.md').write_text('local')
   self.assertEqual({str(f.relative_to(r)) for f in p.release_paths(r)},{'README.md','studies/registry.json'})
 def test_symlink_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=fixture(Path(td));(r/'README.md').write_text('ok');(r/'alias').symlink_to(r/'README.md')
   with self.assertRaises(ValueError):p.release_paths(r)
 def test_import_skips_excluded_configurations(self):
  # Synthetic reports contain only public case versions and deliberately
  # incomplete excluded rows: touching any excluded payload would fail.
  policy=p.study_config(ROOT,STUDY);cases=p.read(ROOT/'data/cases.json')['cases']
  excluded=[x.split('/')[1] for x in policy['excluded_source_ids']]
  suites=list(dict.fromkeys(key.split('/')[0] for key in policy['configuration_ids']))
  sources=[{'suite_id':suite,**{name:suite+'/'+filename for name,filename in [('observations','observations.json'),('metrics','metrics.json'),('runtime_profiles','runtime.json')]}} for suite in suites]
  read=p.read
  def source_read(path):
   path=Path(path)
   if path.name=='sources.json':return sources
   if path.name=='case-reviews.json':return {'cases':cases,'answers':[]}
   if path.name=='observations.json':
    rows=[{'configuration':name,'case_id':cases[0]['case_id']} for name in excluded] if path.parent.name==suites[0] else []
    return {'cases':cases,'answers':rows,'configurations':{},'summary':{}}
   if path.name=='metrics.json':
    return {'models':[{'title':'Excluded fixture','modes':[{'id':name,'title':'excluded','conditions':[{'records':120}]} for name in excluded]}]} if path.parent.name==suites[0] else {'models':[]}
   if path.name=='runtime.json':return {'profiles':{}}
   return read(path)
  with tempfile.TemporaryDirectory() as td:
   root=fixture(Path(td),full=True)
   with patch.object(p,'read',side_effect=source_read),patch.object(p,'sha',return_value='f'*64),patch.object(p,'validate'),patch.object(p.metadata,'verify'),patch.object(p,'project_config',side_effect=AssertionError('excluded configuration projected')),patch.object(p,'project_answer',side_effect=AssertionError('excluded answer projected')):
    p.import_private(root/'synthetic-source',root=root,source_manifest=root/'sources.json',case_reviews=Path('case-reviews.json'))
   result=read(p.study_path(root,STUDY)/'data/results.json')
   self.assertEqual(result['configurations'],[]);self.assertEqual(result['cells'],[])
   self.assertEqual(read(p.study_path(root,STUDY)/'data/answers.json')['answers'],[])
 def test_source_mapping_retains_rerun_and_rejects_unknown_id(self):
  policy=p.study_config(ROOT,STUDY)
  self.assertEqual(p.public_configuration(policy,'medium/qwen4-off'),'qwen3.5-4b/off')
  for identifier in policy['excluded_source_ids']:self.assertIsNone(p.public_configuration(policy,identifier))
  with self.assertRaisesRegex(ValueError,'Unmapped source'):p.public_configuration(policy,'unregistered/model-off')

class FrozenDataTests(unittest.TestCase):
 def test_generation_speed_filters_and_missing_first_token_timing(self):
  configs=p.read(STUDY_ROOT/'data/results.json')['configurations'][:2];cfg=configs[0]['id']
  def answer(tokens=100,seconds=3,first=1,attempts=1):
   return {'configuration':cfg,'operations':{'total_output_tokens':tokens,'tokens_per_second':999},'request_timing':{'selected_request_seconds':seconds,'first_token_seconds':first,'attempt_count':attempts}}
  answers=[answer(),answer(200,2,None),answer(99),answer(attempts=2),answer(seconds=1),answer(seconds=0),answer(seconds=None),answer(seconds=float('nan')),answer(tokens=None),answer(first=-1),answer(first=float('inf'))]
  rows=p.generation_speed_rows(answers,configs,18);row=next(r for r in rows if r['configuration']==cfg)
  self.assertEqual(row['n'],2);self.assertEqual(row['n_first_token_timing'],1)
  self.assertEqual(row['median_tokens_per_second'],75)
  self.assertIsNone(next(r for r in rows if r['configuration']!=cfg)['median_tokens_per_second'])
  self.assertEqual(rows,p.generation_speed_rows(list(reversed(answers)),list(reversed(configs)),18))
 def test_speed_exports_public_subset_counts_and_manifest_hashes(self):
  with tempfile.TemporaryDirectory() as td:
   out=p.build(output=Path(td));report=out/'studies'/STUDY['slug'];rows=p.read(report/'speed.json')['table']
   self.assertEqual(len(rows),25);by_id={r['configuration']:r for r in rows}
   self.assertEqual(by_id['gemma4-26b-a4b/off']['n'],35)
   self.assertAlmostEqual(by_id['gemma4-26b-a4b/off']['median_tokens_per_second'],128.80970897756546,places=5)
   self.assertEqual(by_id['glm4.7-flash/on']['n'],34)
   self.assertTrue(all(r['public_cases']==18 and 'public cases only' in r['population'] for r in rows))
   with (report/'speed.csv').open(newline='') as f:csv_rows=list(csv.DictReader(f))
   self.assertEqual([r['configuration'] for r in csv_rows],[r['configuration'] for r in rows])
   self.assertEqual([float(r['median_tokens_per_second']) for r in csv_rows],[r['median_tokens_per_second'] for r in rows])
   for name in ('speed.csv','speed.json'):
    for base in (out,report):self.assertEqual(p.read(base/'manifest.json')['files'][str((report/name).relative_to(base))],p.sha(report/name))
    self.assertIn(str((report/name).relative_to(out)),p.generated_paths(ROOT))
 def test_retained_data_validates(self):self.assertEqual(p.validate()['public_answer_records'],900)
 def test_every_public_configuration_has_both_conditions(self):
  d=p.read(STUDY_ROOT/'data/answers.json')['answers'];self.assertEqual(len({(r['configuration'],r['case_id'],r['condition']) for r in d}),900)
 def test_no_held_out_records_or_comments(self):
  ids=set(p.read(ROOT/'data/visibility.json')['case_ids'])
  for r in p.read(STUDY_ROOT/'data/answers.json')['answers']:
   self.assertIn(r['case_id'],ids);self.assertNotIn('private_comment',json.dumps(r));self.assertNotIn('binding',r)
 def test_public_counterspell_human_awards_match_final_totals(self):
  rows=p.read(STUDY_ROOT/'data/answers.json')['answers'];targets=[r for r in rows if r['configuration'] in {'granite4.2-8b/on','granite4.2-8b/off'} and r['case_id'].endswith('t10-008') and r['condition']=='supplied_passage']
  self.assertEqual({r['score']['earned_points'] for r in targets},{100,60})
  for r in targets:self.assertEqual(sum(c['earned_points'] for c in r['claim_awards']),r['score']['earned_points'])
 def test_build_reproduces_data_and_has_no_embedded_script_breakout(self):
  with tempfile.TemporaryDirectory() as td:
   out=p.build(output=Path(td));report=out/'studies'/STUDY['slug'];html=(report/'index.html').read_text();self.assertIn('studies/'+STUDY['slug']+'/index.html',(out/'index.html').read_text());self.assertNotIn('/*PUBLIC_DATA*/',html)
   self.assertEqual((report/'answers.json').read_bytes(),(STUDY_ROOT/'data/answers.json').read_bytes());self.assertEqual(len(list((report/'comparison.csv').read_text().splitlines())),51)
   self.assertNotIn('</script><script>alert',html)
   manifest=p.read(out/'manifest.json')
   for name,h in manifest['files'].items():self.assertEqual(p.sha(out/name),h)
   for manifest_path in [out/'manifest.json',report/'manifest.json']:
    for name,h in p.read(manifest_path)['source_files'].items():self.assertEqual(p.sha(ROOT/name),h)
 def test_html_is_small_and_contains_no_public_payloads(self):
  with tempfile.TemporaryDirectory() as td:
   out=p.build(output=Path(td));answers=p.read(STUDY_ROOT/'data/answers.json')['answers'];cases=p.read(ROOT/'data/cases.json')['cases']
   for page in out.rglob('*.html'):
    text=page.read_text()
    self.assertLess(page.stat().st_size,120_000 if page.name!='index.html' or page.parent!=out else 10_000)
    for row in answers:
     if row['candidate_answer']:self.assertNotIn(row['candidate_answer'],text)
    for case in cases:self.assertNotIn(case['question'],text)
   report=out/'studies'/STUDY['slug']
   self.assertIn('href="explore.html"',(report/'index.html').read_text())
   self.assertNotIn('fetch(', (report/'index.html').read_text())
   self.assertIn('report-figures.js',(report/'index.html').read_text())
   explorer=(report/'explore.html').read_text()
   self.assertIn('Could not load the data. Reload the page, or download the JSON files linked above.',explorer)
   self.assertNotIn('http://127.0.0.1',explorer)
   self.assertNotIn("loadJSON('answers.json')",explorer)
 def test_lazy_answer_shards_reproduce_records_and_have_hashed_allowlist(self):
  with tempfile.TemporaryDirectory() as td:
   out=p.build(output=Path(td));report=out/'studies'/STUDY['slug'];index=p.read(report/'answer-index.json');rows=[]
   manifests=[(out,p.read(out/'manifest.json')),(report,p.read(report/'manifest.json'))];allowed=p.generated_paths(ROOT)
   self.assertEqual(p.read(report/'comparison.json')['table'],p.table_rows(ROOT,STUDY))
   for case,configs in index.items():
    for cfg,name in configs.items():
     path=report/name;shard=p.read(path)['answers'];rows.extend(shard)
     self.assertEqual(len(shard),2)
     self.assertEqual({r['condition'] for r in shard},{'no_source','supplied_passage'})
     self.assertTrue(all(r['case_id']==case and r['configuration']==cfg for r in shard))
     for base,manifest in manifests:self.assertEqual(manifest['files'][str(path.relative_to(base))],p.sha(path))
     self.assertIn(str(path.relative_to(out)),allowed)
     url=urlsplit(urljoin('https://example.com/d20-bench/studies/'+STUDY['slug']+'/explore.html',name))
     self.assertTrue(url.path.startswith('/d20-bench/'))
     self.assertEqual(out/url.path.removeprefix('/d20-bench/'),path)
   key=lambda r:(r['case_id'],r['configuration'],r['condition'])
   self.assertEqual(sorted(rows,key=key),sorted(p.read(STUDY_ROOT/'data/answers.json')['answers'],key=key))
 def test_built_site_links_and_assets_resolve_under_url_subpath(self):
  with tempfile.TemporaryDirectory() as td:
   out=p.build(output=Path(td));prefix='https://example.com/d20-bench/'
   for page in out.rglob('*.html'):
    parser=SiteReferences();parser.feed(page.read_text())
    if page.name=='explore.html':parser.urls.extend(['comparison.json','results.json','cases.json','answer-index.json'])
    self.assertTrue(parser.urls)
    for ref in parser.urls:
     with self.subTest(page=str(page.relative_to(out)),reference=ref):
      if urlsplit(ref).scheme:
       self.assertIn(urlsplit(ref).scheme,{'https','http','mailto'})
       if urlsplit(ref).scheme!='mailto':self.assertIn(urlsplit(ref).hostname,{'erolcanakbaba.com','127.0.0.1','arxiv.org','ahelpme.com','www.reddit.com','huggingface.co','github.com','www.nngroup.com','aclanthology.org'})
       continue
      self.assertFalse(ref.startswith('/'))
      self.assertFalse(urlsplit(ref).scheme)
      resolved=urlsplit(urljoin(prefix+page.relative_to(out).as_posix(),ref))
      self.assertEqual(resolved.netloc,'example.com')
      self.assertTrue(resolved.path.startswith('/d20-bench/'))
      self.assertTrue((out/resolved.path.removeprefix('/d20-bench/')).is_file())
   report=out/'studies'/STUDY['slug']
   self.assertIn('With oracle passages',(report/'comparison.csv').read_text())
   self.assertIn('With oracle passages',(report/'latency.svg').read_text())
   self.assertEqual({r['condition'] for r in p.read(report/'results.json')['cells']},{'no_source','supplied_passage'})
 def test_stale_build_file_is_not_silently_released(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td);(out/'scratch.txt').write_text('unreviewed')
   with self.assertRaises(ValueError):p.build(output=out)
 def test_membership_tampering_fails(self):
  with tempfile.TemporaryDirectory() as td:
   target=fixture(Path(td),full=True);answer_path=p.study_path(target,STUDY)/'data/answers.json'
   data=p.read(answer_path);data['answers'][0]['case_id']='not-public';p.write(answer_path,data)
   with self.assertRaises(ValueError):p.validate(target)
 def test_retained_answer_and_cell_values_cannot_change(self):
  for filename,key,field in [('answers.json','answers','candidate_answer'),('results.json','cells','no_final')]:
   with self.subTest(filename=filename),tempfile.TemporaryDirectory() as td:
    root=fixture(Path(td),full=True);path=p.study_path(root,STUDY)/'data'/filename;data=p.read(path)
    data[key][0][field]='changed' if key=='answers' else 999;p.write(path,data)
    with self.assertRaisesRegex(ValueError,'payload hash mismatch'):p.validate(root)
 def test_size_grouping_uses_total_parameters_and_preserves_provenance(self):
  results=p.read(STUDY_ROOT/'data/results.json');cfg={c['id']:c for c in results['configurations']}
  self.assertEqual(cfg['gemma4-e4b/off']['size_class'],'medium')
  self.assertEqual(cfg['gemma4-e2b/off']['size_class'],'small')
  self.assertEqual(cfg['lfm2.5-8b-a1b/native']['size_class'],'medium')
  self.assertEqual(cfg['gemma4-e4b/off']['source_id'],'tiny/gemma-off')
  self.assertIsNone(cfg['gemma4-e4b/off']['active_parameters'])
  self.assertEqual(cfg['gemma4-e4b/off']['effective_parameters'],4500000000)
  rows=p.table_rows(ROOT,STUDY);self.assertEqual(len(rows),50)
  self.assertTrue(all('source_id' not in row and 'batch' not in row for row in rows))
  classes=[r['size_class'] for r in rows];self.assertEqual(classes,sorted(classes,key=['small','medium','large'].index))
  self.assertEqual({size:classes.count(size) for size in set(classes)},{'small':16,'medium':14,'large':20})
  self.assertEqual(sum(s['selected_records'] for s in results['sources']),6000)
 def test_registry_rename_drives_build_and_package_allowlist(self):
  with tempfile.TemporaryDirectory() as td:
   root=fixture(Path(td),full=True);registry=p.studies(root);renamed=copy.deepcopy(STUDY);renamed['slug']='renamed-study'
   p.study_path(root,STUDY).rename(p.study_path(root,renamed));registry[0]=renamed;p.write(root/'studies/registry.json',registry)
   # A slug rename also requires updating relative documentation links.
   for source in root.rglob('*.md'):
    source.write_text(source.read_text().replace('studies/'+STUDY['slug']+'/', 'studies/'+renamed['slug']+'/'))
   out=p.build(root);report=out/'studies'/renamed['slug']
   self.assertTrue((report/'answers.json').is_file());self.assertFalse((out/'studies'/STUDY['slug']).exists())
   self.assertIn('studies/renamed-study/index.html',(out/'index.html').read_text())
   self.assertIn('studies/renamed-study/explore.html',(out/'index.html').read_text())
   self.assertNotIn('studies/'+STUDY['slug']+'/',(out/'index.html').read_text())
   self.assertIn(p.study_path(root,renamed)/'data/answers.json',p.release_paths(root))
 def test_package_excludes_unregistered_study_and_raw_study_files(self):
  with tempfile.TemporaryDirectory() as td:
   root=fixture(Path(td),full=True);dest=p.study_path(root,STUDY)
   for name in ('LICENSE','LICENSE-CC-BY-4.0.md','CITATION.cff'):
    shutil.copyfile(ROOT/name,root/name)
   (dest/'data/raw.json').write_text('{"private":"DO_NOT_RELEASE"}')
   (dest/'docs/notes.md').write_text('DO_NOT_RELEASE')
   (root/'studies/unregistered').mkdir();(root/'studies/unregistered/answers.json').write_text('DO_NOT_RELEASE')
   p.package(root);archive=root/'dist/d20-bench-study1.zip';digest=p.sha(archive)
   with zipfile.ZipFile(archive) as z:
    names=set(z.namelist());prefix='d20-bench/studies/'+STUDY['slug']
    for name in ('LICENSE','LICENSE-CC-BY-4.0.md','CITATION.cff'):
     self.assertEqual(z.read('d20-bench/'+name),(ROOT/name).read_bytes())
    self.assertIn(prefix+'/data/answers.json',names)
    self.assertIn('d20-bench/site/studies/'+STUDY['slug']+'/index.html',names)
    site_prefix='d20-bench/site/studies/'+STUDY['slug']+'/'
    self.assertIn(prefix+'/web/explore.html',names)
    for name in ('explore.html','comparison.json','answer-index.json','speed.csv','speed.json'):self.assertIn(site_prefix+name,names)
    for name,_,_,_ in p.answer_shards(root,STUDY):self.assertIn(site_prefix+name,names)
    self.assertFalse(any(b'DO_NOT_RELEASE' in z.read(n) for n in names))
    self.assertEqual(len(names),len(z.namelist()))
   p.package(root);self.assertEqual(p.sha(archive),digest)
 def test_registry_rejects_duplicate_and_unsafe_slugs(self):
  with tempfile.TemporaryDirectory() as td:
   root=fixture(Path(td));p.write(root/'studies/registry.json',[STUDY,STUDY])
   with self.assertRaises(ValueError):p.studies(root)
   invalid=copy.deepcopy(STUDY);invalid['slug']='../outside';p.write(root/'studies/registry.json',[invalid])
   with self.assertRaises(ValueError):p.studies(root)
 def test_import_rejects_unknown_study_before_reading_private_source(self):
  with self.assertRaisesRegex(ValueError,'Unknown study'):p.import_private(Path('nonexistent'),study_slug='unregistered')
 def test_import_requires_explicit_file_paths(self):
  with self.assertRaisesRegex(ValueError,'Supply source_manifest and case_reviews'):
   p.import_private(Path('nonexistent'))
 def test_config_export_uses_nulls_and_plain_seed_status(self):
  cfg={'model_key':'example','generation':{'context_length':32768,'max_output_tokens':8192}}
  result=p.project_config(cfg,'off','Example','off','source')
  for key in ('selected_variant','runtime_version','exact_gpu_placement','reasoning_effort'):
   self.assertIsNone(result[key])
  self.assertEqual(result['generation_seed_status'],'not set')
 def test_source_paths_cannot_escape_the_supplied_root(self):
  policy=p.study_config(ROOT,STUDY)
  suites=list(dict.fromkeys(key.split('/')[0] for key in policy['configuration_ids']))
  inputs=[{'suite_id':suite} for suite in suites]
  read=p.read
  def source_read(path):return inputs if Path(path).name=='sources.json' else read(path)
  with patch.object(p,'read',side_effect=source_read):
   with self.assertRaisesRegex(ValueError,'Source file outside source root'):
    p.import_private(Path('nonexistent'),source_manifest=Path('sources.json'),case_reviews=Path('../reviews.json'))

if __name__=='__main__':unittest.main()
