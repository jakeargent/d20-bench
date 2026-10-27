"""Offline publication pipeline. Private imports are explicit; releases are allowlisted."""
from __future__ import annotations
import argparse,copy,csv,hashlib,html,ipaddress,json,math,re,statistics,sys,zipfile
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
# Also supports importlib-based test loading and direct script execution.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from markdown_subset import render as render_markdown
from paper_pages import (document_sources, source_routes, link_mapper, load_figures,
                         paper_page, report_content, rewrite_html_links, back_to_report)

from transforms import public_metadata_v1 as metadata

ROOT=Path(__file__).resolve().parents[1]
CONDITIONS={'no_source':'Without oracle passages','supplied_passage':'With oracle passages'}
GENERATION=('context_length','max_output_tokens','temperature','top_p','top_k','min_p','repeat_penalty','presence_penalty','frequency_penalty')
SCORE=('earned_points','met_claims','required_claims','uncertain_claims','requirement_coverage','complete_task_success','has_material_error')
QUALITY=('planned','answers_returned','operational_failures','graded','exact_claim_scores','mean_claim_score','fully_correct','profile_assessed','mean_fully_met_claim_coverage','answers_with_material_errors','material_error_assessed','unknown_judgments','operationally_flagged_answers','output_ceiling_hits','thinking_marker_breaches','direct_failures','regenerated_answers','mean_output_tokens','mean_client_seconds')
OPERATIONS=('input_tokens','total_output_tokens','reasoning_output_tokens','tokens_per_second','time_to_first_token_seconds','client_elapsed_seconds')
TEXT_KEYS={'question','reference_answer','requirements','passages','claim_id','original_text','weight','rationale','credit_rule','full_credit_condition','partial_levels','points','condition','zero_credit_condition','selection_rule','no_partial_credit_reason','pdf_page_numbers','text','claims','status','earned_points','reason','answer_quote','pdf_pages','mistakes','mistake_id','evidence_findings','supplied_support','srd_support','accepted_alternatives','uncertainty_flags','extra_assertions_audited','source_evidence','pdf_page','source_quote'}
FLAGS={'output_ceiling_hit','reasoning_content_despite_off','thinking_not_closed','empty_answer','request_failure','missing_final_answer'}
PRIVATE_PATH=re.compile(r'(?:/home/|/tmp/|/Users/|[A-Za-z]:\\|(?:\.\./)?artifacts/)\S*')
CASE_ID=re.compile(r'd20-en-pilot-t\d{2}-\d{3}')
IP=re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
SECRET=re.compile(r'(?i)(?:sk-[a-z0-9_-]{24,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|Bearer\s+[a-z0-9._-]{20,})')
RELEASE_FILES={'LICENSE','LICENSE-CC-BY-4.0.md','README.md','SECURITY.md','THIRD_PARTY_NOTICES.md','CITATION.cff','pyproject.toml','uv.lock','.python-version','.gitignore','Makefile'}
RELEASE_DIRS={'scripts','tests','web','.github'}
SHARED_DATA={'cases.json','visibility.json'}
STUDY_DATA={'answers.json','results.json'}
STUDY_DOCS={'METHODS.md','LIMITATIONS.md','DATA_DICTIONARY.md','RESULTS.md','PROVENANCE.md'}
FONT_FILES={'newsreader-normal.woff2','newsreader-italic.woff2','newsreader-latin-ext.woff2','ibm-plex-mono-latin-400-normal.woff2','ibm-plex-mono-latin-ext-400-normal.woff2','Newsreader-LICENSE.txt','IBM-Plex-Mono-LICENSE.txt'}
WEB_ASSETS={'paper.css','favicon.svg','theme.js','report-figures.js',*{'fonts/'+name for name in FONT_FILES}}
SITE_NOTICES={'CITATION.cff','THIRD_PARTY_NOTICES.md','LICENSE','LICENSE-CC-BY-4.0.md','README.md'}

def read(p):return json.loads(Path(p).read_text())
def write(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def payload_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def studies(root=ROOT):
 registry=read(Path(root)/'studies/registry.json')
 slugs=[s['slug'] for s in registry]
 if not slugs or len(slugs)!=len(set(slugs)) or any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',s) for s in slugs):raise ValueError('Invalid study registry')
 return registry
def study_path(root,study):return Path(root)/'studies'/study['slug']
def study_config(root,study):return read(study_path(root,study)/'config.json')
def public_configuration(policy,source_id):
 if source_id in policy['excluded_source_ids']:return None
 try:return policy['configuration_ids'][source_id]
 except KeyError:raise ValueError('Unmapped source configuration: '+source_id) from None
def publication_config(cfg,policy):
 source_id=cfg['id'];identifier=public_configuration(policy,source_id)
 if identifier is None:raise ValueError('Excluded configuration cannot be projected')
 return {**cfg,'id':identifier,'source_id':source_id,'batch':cfg['suite_id'],**policy['models'][identifier.split('/')[0]]}
def configuration_order(cfg):return (('small','medium','large').index(cfg['size_class']),cfg['total_parameters'],cfg['id'])
def finite(x):return type(x) in (int,float) and math.isfinite(x)
def fields(d,keys):return {k:d[k] for k in keys if k in d and (d[k] is None or type(d[k]) is bool or finite(d[k]))}
def clean_text(s):
 s=PRIVATE_PATH.sub('[private path removed]',s)
 def mask(m):
  try:return '[private address removed]' if ipaddress.ip_address(m[0]).is_private and m[0]!='127.0.0.1' else m[0]
  except ValueError:return m[0]
 return IP.sub(mask,s)
def public_text(x):
 if isinstance(x,dict):return {k:public_text(v) for k,v in x.items() if k in TEXT_KEYS}
 if isinstance(x,list):return [public_text(v) for v in x]
 return clean_text(x) if isinstance(x,str) else x

AGGREGATE_KEYS={'180', 'request_failures', 'max_seconds', 'retried_cases', 'final_returned_p95_seconds', 'first_token_timing_cases', 'first_token_p95_seconds', 'nonempty_finals', 'p99_seconds', 'attempt_count', 'p25', 'count', 'no_final_cases', '300', 'request_failure_attempts', '120', 'final_returned_median_seconds', 'output_ceiling_hit', 'p75_seconds', 'p95_seconds', 'missing_or_partial_timing_cases', 'median', '1800', 'output_ceiling_hits', 'denominator', 'final_answer_completion', 'median_seconds', 'retried', 'selected_request_seconds', 'recorded_cases', 'first_token_seconds', 'has_final', 'above_30_seconds', 'p75', 'p90_seconds', 'ordinal', 'total_attempt_seconds', 'observed_above_seconds', 'maximum', 'p95', 'bins', 'complete_timing_cases', 'mean', 'mean_seconds', '900', 'p25_seconds'}

def safe_tree(x):
 """Numeric aggregates only. Caller selects structural labels separately."""
 if isinstance(x,dict):
  if set(x)-AGGREGATE_KEYS:raise ValueError('Unexpected aggregate field')
  return {k:safe_tree(v) for k,v in x.items()}
 if isinstance(x,list):return [safe_tree(v) for v in x]
 if x is None or type(x) is bool or finite(x):return x
 raise ValueError('Unexpected text in numeric aggregate')

def final_awards(row):
 awards=[{k:c[k] for k in ('claim_id','status','earned_points') if k in c} for c in row.get('annotation',{}).get('claims',[])]
 j=row.get('human_adjudication',{})
 if j.get('scope')=='claim_C004':
  claim=next(c for c in awards if c['claim_id']==j['claim_id']);claim.update(status=j['status'],earned_points=j['points'])
 if awards and all(finite(c.get('earned_points')) for c in awards):
  if sum(c['earned_points'] for c in awards)!=row['score']['earned_points']:raise ValueError('Final claim awards do not match final score')
 return awards

def project_answer(row,suite):
 if set(row.get('operational_flags',[]))-FLAGS:raise ValueError('Unknown operational flag')
 out={'suite_id':suite,'configuration':suite+'/'+row['configuration'],'case_id':row['case_id'],'condition':row['condition'],'candidate_answer':clean_text(row.get('candidate_answer') or ''),'score':fields(row['score'],SCORE),'claim_awards':final_awards(row),'expert_annotation':public_text(row.get('annotation',{})),'operations':fields(row.get('operations',{}),OPERATIONS),'operational_flags':row.get('operational_flags',[]),'answer_sha256':row.get('answer_sha256'),'candidate_input_sha256':row['candidate_input_sha256']}
 if row.get('expert_score'):out['original_expert_score']=fields(row['expert_score'],SCORE)
 if row.get('human_adjudication'):
  j=row['human_adjudication'];out['final_review']={'kind':'human','scope':j.get('scope','profile'),'verdict':j.get('verdict') or ('points_awarded' if j.get('scope')=='claim_C004' else 'no_material_error' if row['score']['has_material_error'] is False else 'material_error' if row['score']['has_material_error'] is True else 'unresolved'),'claim_id':j.get('claim_id'),'points':j.get('points')}
 metadata.normalize_answer_metadata(out)
 return out

def project_config(cfg,name,title,mode,suite):
 return {'id':suite+'/'+name,'suite_id':suite,'model':clean_text(title),'mode':mode,'model_key':clean_text(cfg['model_key']),'selected_variant':clean_text(cfg['selected_variant']) if cfg.get('selected_variant') else None,'quantization':cfg.get('quantization'),'adapter':cfg.get('adapter'),'generation':fields(cfg['generation'],GENERATION),'thinking':cfg['generation'].get('reasoning','native'),'reasoning_effort':cfg.get('reasoning_effort'),'generation_seed':cfg.get('generation_seed'),'generation_seed_status':'not set' if cfg.get('generation_seed') is None else 'set','runtime_version':None,'exact_gpu_placement':None}

def import_private(source_root,root=ROOT,study_slug=None,source_manifest=None,case_reviews=None):
 """Import selected records from explicitly supplied source files.

 The JSON source manifest is a list of objects with suite_id, observations,
 metrics and runtime_profiles paths relative to source_root. case_reviews
 identifies the case-review JSON relative to the same root.
 """
 root=Path(root);study=next((s for s in studies(root) if study_slug in (None,s['slug'])),None)
 if study is None:raise ValueError('Unknown study')
 dest=study_path(root,study);policy=study_config(root,study)
 source_root=Path(source_root).resolve()
 if source_manifest is None or case_reviews is None:raise ValueError('Supply source_manifest and case_reviews paths')
 def source_path(name):
  path=(source_root/name).resolve()
  if not path.is_relative_to(source_root):raise ValueError('Source file outside source root')
  return path
 inputs=read(source_manifest)
 expected_suites={key.split('/')[0] for key in policy['configuration_ids']}
 if not isinstance(inputs,list) or {entry['suite_id'] for entry in inputs}!=expected_suites or len(inputs)!=len(expected_suites):raise ValueError('Source manifest membership mismatch')
 review_path=source_path(case_reviews);reviews=read(review_path);review_rows={(a['mode'],a['case_id'],a['condition']):a for a in reviews['answers']}
 public_ids=sorted(c['case_id'] for c in reviews['cases'])
 if len(public_ids)!=18 or len(set(public_ids))!=18:raise ValueError('Expected 18 public cases')
 cases=None;answers=[];configs=[];cells=[];sources=[]
 for entry in inputs:
  suite=entry['suite_id'];observation_path=source_path(entry['observations']);metrics_path=source_path(entry['metrics']);runtime_path=source_path(entry['runtime_profiles'])
  p=observation_path.parent;obs=read(observation_path);metrics=read(metrics_path);runtime=read(runtime_path);by_case={c['case_id']:c for c in obs['cases']}
  if not set(public_ids)<=by_case.keys():raise ValueError('Public selection not in source')
  selected=[{'case_id':cid,'topic_id':by_case[cid]['topic_id'],'topic':by_case[cid]['topic'],**public_text(by_case[cid])} for cid in public_ids]
  metadata.normalize_cases({'cases':selected})
  if cases is None:cases=selected
  elif cases!=selected:raise ValueError('Case versions differ between selected reports')
  for model in metrics['models']:
   for mode in model['modes']:
    name=mode['id'];identifier=public_configuration(policy,suite+'/'+name)
    if identifier is None:continue
    configs.append(publication_config(project_config(obs['configurations'][name],name,model['title'],mode['title'],suite),policy))
    for c in mode['conditions']:
     if c['records']!=120:raise ValueError('Incomplete aggregate condition')
     cell={'configuration':identifier,'condition':c['condition'],'records':c['records'],'quality':fields(c['quality'],QUALITY)}
     # Observation summaries supply the final quality measurements.
     cell['quality']=fields(metadata.normalize_quality(copy.deepcopy(obs['summary'][name][c['condition']])),QUALITY)
     for k in ['timing','output_tokens','input_tokens','thinking_tokens','server_tokens_per_second','first_token_seconds']:cell[k]=safe_tree(c[k])
     cell['no_final']=c['no_final'];cells.append(cell)
  runtime_lookup={(n,c['ordinal']):c for n,v in runtime['profiles'].items() for c in v['cases']}
  for row in obs['answers']:
   identifier=public_configuration(policy,suite+'/'+row['configuration'])
   if identifier is None:continue
   if row['case_id'] not in public_ids:continue
   result=project_answer(row,suite);result['configuration']=identifier
   if row.get('historical_record'):
    hist=review_rows[row['configuration'].split('-')[1],row['case_id'],row['condition']]
    assert hist['answer_sha256']==row['answer_sha256'] and hist['earned_points']==row['score']['earned_points']
    result['historical_review']={'claim_detail':metadata.CLAIM_DETAIL,'targeted_human_review':bool(hist.get('human_review'))}
    result['historical_expert_annotations']={k:public_text(v) for k,v in hist.get('expert_annotations',{}).items() if k in {'gpt','sonnet'}}
   result['request_timing']=safe_tree({k:v for k,v in runtime_lookup[row['configuration'],row['ordinal']].items() if k not in {'case_id','condition'}})
   clock=runtime_lookup[row['configuration'],row['ordinal']];assert clock['case_id']==row['case_id'] and clock['condition']==row['condition']
   result['request_timing'].pop('ordinal',None)
   record_path=(p/row['answer_record']).resolve()
   if not record_path.is_relative_to(source_root):raise ValueError('Answer record outside source repository')
   record=read(record_path);assert record['answer']==row['candidate_answer'] and record['answer_sha256']==row['answer_sha256']
   result['candidate_request']={k:clean_text(v) for k,v in record['request'].items() if k in {'prompt','system_prompt','input'} and isinstance(v,str)}
   if result.get('candidate_request',{}).get('input') is not None and row['case_id'] not in public_ids:raise ValueError('Private prompt')
   answers.append(result)
  sources.append({'historical_pilot_sha256':sha(review_path) if any(g['batch']==suite and g['id'].startswith('gemma4-e4b/') for g in configs) else None,'suite_id':suite,'source_selected_records':len(obs['answers']),'selected_records':sum(c['records'] for c in cells if c['configuration'] in {g['id'] for g in configs if g['batch']==suite}),'observations_sha256':sha(observation_path),'metrics_sha256':sha(metrics_path),'runtime_profiles_sha256':sha(runtime_path)})
 visibility={'schema_version':1,'case_ids':public_ids,'public_case_count':18,'private_case_count':102,'basis':metadata.VISIBILITY_BASIS,'private_disclosure':metadata.PRIVATE_DISCLOSURE}
 shared={'visibility.json':visibility,'cases.json':{'schema_version':1,'cases':cases}}
 for name,value in shared.items():
  if read(root/'data'/name)!=value:raise ValueError('Shared cases or visibility differ from the public selection')
 for row in answers:metadata.normalize_answer_metadata(row)
 metadata.apply_annotation_edits(answers)
 results={'schema_version':1,'suite_questions':120,'selected_records':sum(c['records'] for c in cells),'public_answer_records':len(answers),'configurations':configs,'cells':cells,'sources':sources,'grader_accuracy':'unmeasured'}
 metadata.normalize_results(results)
 metadata.verify(policy,results,answers,shared['cases.json'],visibility)
 write(dest/'data/answers.json',{'schema_version':1,'answers':answers});write(dest/'data/results.json',results)
 validate(root);print(json.dumps({'public_cases':len(cases),'public_answers':len(answers),'configurations':len(configs),'aggregate_conditions':len(cells),'private_case_records_copied':0}))

def release_paths(root):
 result=[]
 allowed_study_files={'studies/registry.json'}
 for study in studies(root):
  prefix=Path('studies')/study['slug']
  allowed_study_files.update(str(prefix/p) for p in [Path('README.md'),Path('config.json'),Path('web/index.html'),Path('web/explore.html'),Path('web/figures.html'),Path('web/report-links.json'),Path('report/REPORT.md'),*[Path('data')/n for n in STUDY_DATA],*[Path('docs')/n for n in STUDY_DOCS]])
 for f in Path(root).rglob('*'):
  rel=f.relative_to(root)
  if any(x in {'__pycache__','.venv','.git','node_modules'} for x in rel.parts):continue
  if f.is_symlink():raise ValueError('Symlinks are not allowed in publication tree')
  if not f.is_file():continue
  rel=f.relative_to(root)
  if any(x in {'__pycache__','.venv','.git','node_modules'} for x in rel.parts):continue
  if str(rel) in RELEASE_FILES or str(rel) in allowed_study_files or (rel.parts[0]=='data' and str(rel) in {'data/'+n for n in SHARED_DATA}) or rel.parts[0] in RELEASE_DIRS:result.append(f)
 return sorted(result)

def scan_public(root,ids):
 for f in release_paths(root):
  if f.suffix=='.woff2':
   if f.relative_to(root).as_posix() not in {'web/fonts/'+name for name in FONT_FILES if name.endswith('.woff2')}:raise ValueError('Unexpected font asset')
   if f.read_bytes()[:4]!=b'wOF2':raise ValueError('Invalid WOFF2 asset')
   continue
  if f.suffix not in {'.json','.md','.py','.js','.css','.svg','.html','.toml','.yml','.cff','.example','.txt'} and f.name not in {'LICENSE','Makefile','.gitignore','.python-version','uv.lock'}:raise ValueError('Unexpected release file type')
  s=f.read_text()
  if f.suffix=='.json':
   def strings(x):
    if isinstance(x,str):yield x
    elif isinstance(x,dict):
     for k,v in x.items():yield k;yield from strings(v)
    elif isinstance(x,list):
     for v in x:yield from strings(v)
   s='\n'.join(strings(json.loads(s)))
  # Guard implementation contains patterns, not real local identifiers.
  if PRIVATE_PATH.search(s) and f.name not in {'publication.py','.gitignore'}:raise ValueError('Private path in publication tree: '+str(f.relative_to(root)))
  if SECRET.search(s):raise ValueError('Credential-like content in publication tree')
  for m in IP.finditer(s):
   try:
    if ipaddress.ip_address(m[0]).is_private and m[0]!='127.0.0.1':raise ValueError('Private network address in publication tree')
   except ipaddress.AddressValueError:pass
  if set(CASE_ID.findall(s))-set(ids):raise ValueError('Held-out case ID in publication tree: '+str(f.relative_to(root)))

def validate(root=ROOT):
 root=Path(root);audits={s['slug']:validate_study(root,s) for s in studies(root)}
 scan_public(root,read(root/'data/visibility.json')['case_ids'])
 return next(iter(audits.values())) if len(audits)==1 else {'studies':audits}

def validate_study(root,study):
 dest=study_path(root,study);policy=study_config(root,study)
 v=read(root/'data/visibility.json');cases=read(root/'data/cases.json')['cases'];rows=read(dest/'data/answers.json')['answers'];results=read(dest/'data/results.json');ids=set(v['case_ids']);configs={c['id']:c for c in results['configurations']}
 if len(ids)!=18 or {c['case_id'] for c in cases}!=ids or len(cases)!=18:raise ValueError('Public case membership changed')
 if v['public_case_count']!=18 or v['private_case_count']!=102 or results['suite_questions']!=120:raise ValueError('Shared case coverage changed')
 if results['selected_records']!=study['selected_records'] or len(configs)!=study['configurations'] or len(results['cells'])!=study['conditions'] or len(rows)!=study['public_answer_records'] or results['public_answer_records']!=len(rows):raise ValueError('Publication coverage differs from frozen selection')
 if len(configs)!=len(results['configurations']) or set(configs)!=set(policy['configuration_ids'].values()):raise ValueError('Configuration mapping differs from frozen selection')
 if set(policy['excluded_source_ids'])&set(policy['configuration_ids']):raise ValueError('Excluded source configuration is mapped')
 for cfg in configs.values():
  if public_configuration(policy,cfg['source_id'])!=cfg['id'] or cfg['batch']!=cfg['suite_id'] or cfg['source_id'].split('/')[0]!=cfg['batch']:raise ValueError('Configuration provenance mismatch')
  model_metadata=policy['models'][cfg['id'].split('/')[0]]
  if any(cfg.get(k)!=value for k,value in model_metadata.items()):raise ValueError('Configuration parameter metadata mismatch')
  total,active=cfg['total_parameters'],cfg['active_parameters']
  if type(total) is not int or total<=0 or (active is not None and (type(active) is not int or not 0<active<=total)):raise ValueError('Invalid parameter count')
  if cfg['size_class'] not in {'small','medium','large'} or not cfg['parameter_source_url'].startswith('https://huggingface.co/'):raise ValueError('Invalid parameter provenance')
 metadata.verify(policy,results,rows,{'schema_version':1,'cases':cases},v)
 if sum(c['records'] for c in results['cells'])!=results['selected_records'] or sum(s['selected_records'] for s in results['sources'])!=results['selected_records']:raise ValueError('Aggregate record total mismatch')
 for source in results['sources']:
  selected=sum(c['records'] for c in results['cells'] if configs[c['configuration']]['batch']==source['suite_id'])
  if source['selected_records']!=selected or source['source_selected_records']<selected:raise ValueError('Source selection count mismatch')
 rubrics={c['case_id']:{r['claim_id']:r for r in c['requirements']} for c in cases}
 for claims in rubrics.values():
  if sum(c['weight'] for c in claims.values())!=100:raise ValueError('Invalid public rubric total')
 keys=set()
 for row in rows:
  key=(row['configuration'],row['case_id'],row['condition'])
  if key in keys or row['case_id'] not in ids or row['configuration'] not in configs or row['condition'] not in CONDITIONS:raise ValueError('Unexpected public answer membership')
  keys.add(key)
  if set(row)-{'suite_id','configuration','case_id','condition','candidate_answer','score','claim_awards','expert_annotation','operations','operational_flags','answer_sha256','candidate_input_sha256','original_expert_score','final_review','request_timing','candidate_request','historical_review','historical_expert_annotations'}:raise ValueError('Unknown public answer field')
  awards=row['claim_awards']
  if not finite(row['score']['earned_points']) or not 0<=row['score']['earned_points']<=100:raise ValueError('Invalid final score')
  if awards and ({x['claim_id'] for x in awards}!=set(rubrics[row['case_id']]) or len(awards)!=len(rubrics[row['case_id']])):raise ValueError('Claim membership mismatch')
  if not awards and (row['configuration'] not in {'gemma4-e4b/off','gemma4-e4b/on'} or not row.get('historical_review')):raise ValueError('Missing final claim awards')
  for claim in awards:
   rubric=rubrics[row['case_id']][claim['claim_id']];allowed=[0,rubric['weight']]+[v['points'] for v in rubric['credit_rule']['partial_levels']]
   if claim['earned_points'] not in allowed:raise ValueError('Unreviewed claim point level')
  if row['score']['complete_task_success'] is True and (row['score']['earned_points']!=100 or row['score']['has_material_error'] is not False):raise ValueError('Fully correct profile conflicts with score/error judgment')
  if awards and all(finite(c.get('earned_points')) for c in awards) and sum(c['earned_points'] for c in awards)!=row['score']['earned_points']:raise ValueError('Claim arithmetic mismatch')
  if set(row.get('operational_flags',[]))-FLAGS:raise ValueError('Unknown operational flag')
 if len({(c['configuration'],c['condition']) for c in results['cells']})!=study['conditions']:raise ValueError('Duplicate aggregate condition')
 for c in results['cells']:
  if c['configuration'] not in configs or c['condition'] not in CONDITIONS or c['records']!=120 or c['quality']['exact_claim_scores']!=120:raise ValueError('Unexpected aggregate membership')
  if c['quality']['profile_assessed']>120 or c['quality']['material_error_assessed']>120:raise ValueError('Invalid profile denominator')
  if len([r for r in rows if r['configuration']==c['configuration'] and r['condition']==c['condition']])!=18:raise ValueError('Public subset incomplete')
 return {'public_cases':18,'private_cases':102,'public_answer_records':len(rows),'selected_records_in_aggregates':results['selected_records'],'configurations':len(configs),'conditions':len(results['cells']),'status':'passed'}

def fmt(x,digits=1):return 'unknown' if x is None else f'{Decimal(str(x)).quantize(Decimal(1).scaleb(-digits),rounding=ROUND_HALF_UP):,.{digits}f}'
def display_mode(configuration):
 """Reader labels derived from stable configuration IDs; source metadata stays intact."""
 return 'on (low)' if configuration=='qwen3.8-27b/on' else configuration.split('/')[1]

def table_rows(root,study):
 r=read(study_path(root,study)/'data/results.json');cfg={x['id']:x for x in r['configurations']};rows=[]
 for c in sorted(r['cells'],key=lambda c:(configuration_order(cfg[c['configuration']]),c['condition'])):
  q,t=c['quality'],c['timing'];g=cfg[c['configuration']]
  rows.append({'size_class':g['size_class'],'configuration':g['id'],'total_parameters':g['total_parameters'],'active_parameters':g['active_parameters'],'parameter_source_url':g['parameter_source_url'],'model':g['model'],'mode':display_mode(g['id']),'passages':CONDITIONS[c['condition']],'records':120,'public_records':18,'mean_claim_score':q['mean_claim_score'],'fully_correct':q['fully_correct'],'profile_assessed':q['profile_assessed'],'material_errors':q['answers_with_material_errors'],'material_error_assessed':q['material_error_assessed'],'mean_seconds':t['mean_seconds'],'median_seconds':t['median_seconds'],'p25_seconds':t['p25_seconds'],'p75_seconds':t['p75_seconds'],'p95_seconds':t['p95_seconds'],'max_seconds':t['max_seconds'],'above_30_seconds':t['above_30_seconds'],'timed_records':t['complete_timing_cases'],'mean_output_tokens':c['output_tokens']['mean'],'output_limit_hits':q['output_ceiling_hits'],'thinking_marker_breaches':q['thinking_marker_breaches'],'context_tokens':g['generation']['context_length'],'output_ceiling_tokens':g['generation']['max_output_tokens']})
 return rows

def generation_speed_rows(answers,configurations,public_case_count):
 """Pool both conditions from public answers; never use full-suite aggregates."""
 groups={c['id']:[] for c in configurations}
 for answer in answers:
  timing=answer.get('request_timing',{});operations=answer.get('operations',{})
  tokens=operations.get('total_output_tokens');seconds=timing.get('selected_request_seconds');first=timing.get('first_token_seconds')
  if timing.get('attempt_count')!=1 or not finite(tokens) or tokens<100 or not finite(seconds):continue
  if first is not None and (not finite(first) or first<0):continue
  duration=seconds-(first if first is not None else 0)
  if duration<=0:continue
  speed=tokens/duration
  if finite(speed):groups[answer['configuration']].append((speed,first is not None))
 rows=[]
 for cfg in sorted(configurations,key=configuration_order):
  speeds=groups[cfg['id']]
  rows.append({'size_class':cfg['size_class'],'configuration':cfg['id'],'model':cfg['model'],'mode':cfg['mode'],'population':f'{public_case_count} public cases only; both passage conditions pooled','public_cases':public_case_count,'minimum_output_tokens':100,'n':len(speeds),'n_first_token_timing':sum(first for _,first in speeds),'median_tokens_per_second':statistics.median(speed for speed,_ in speeds) if speeds else None})
 return rows

GENERATED_FILES={'speed.csv','speed.json','comparison.csv','comparison.md','latency.svg','index.html','explore.html','comparison.json','answer-index.json',*SHARED_DATA,*STUDY_DATA,*STUDY_DOCS,'THIRD_PARTY_NOTICES.md','manifest.json','comparison.html','README.html',*{str(Path(n).with_suffix('.html')) for n in STUDY_DOCS}}

def answer_shards(root,study):
 # Numeric filenames avoid coupling URLs to configuration IDs containing slashes.
 groups={}
 for row in read(study_path(root,study)/'data/answers.json')['answers']:
  groups.setdefault((row['case_id'],row['configuration']),[]).append(row)
 return [(f'answers/{i:04d}.json',case,cfg,rows) for i,((case,cfg),rows) in enumerate(sorted(groups.items()))]

def generated_paths(root):
 return {'index.html','manifest.json','studies/registry.json',*document_sources(Path(root),studies(root)).values(),*SITE_NOTICES,*{'assets/'+name for name in WEB_ASSETS}}|{str(Path('studies')/s['slug']/name) for s in studies(root) for name in GENERATED_FILES|{name for name,_,_,_ in answer_shards(root,s)}}

def build(root=ROOT,output=None):
 root=Path(root);audit=validate(root);out=Path(output) if output else root/'site';out.mkdir(parents=True,exist_ok=True)
 allowed=generated_paths(root)
 if any(f.is_symlink() or (f.is_file() and str(f.relative_to(out)) not in allowed) for f in out.rglob('*')):raise ValueError('Unexpected file in build directory; refuse to package it')
 for name in sorted(WEB_ASSETS):
  target=out/'assets'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((root/'web'/name).read_bytes())
 for name in SITE_NOTICES:(out/name).write_bytes((root/name).read_bytes())
 (out/'studies').mkdir(exist_ok=True)
 (out/'studies/registry.json').write_bytes((root/'studies/registry.json').read_bytes())
 routes=source_routes(root,studies(root))
 template=(study_path(root,studies(root)[0])/'web/index.html').read_text()
 for source,target in document_sources(root,studies(root)).items():
  if source=='LICENSE-CC-BY-4.0.md':
   # The unmodified official license is plain text, despite its file extension.
   content='<h1>Attribution 4.0 International</h1><pre><code>'+html.escape((root/source).read_text())+'</code></pre>'
  else:
   content=render_markdown((root/source).read_text(),link=link_mapper(source,target,routes))
  if target.startswith('studies/'):content=back_to_report(target,studies(root)[0]['slug'])+content
  page=paper_page(template,content,target,studies(root)[0]['slug'])
  path=out/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(page)
 links=[]
 for study in studies(root):
  build_study(root,study,out/'studies'/study['slug'])
  links.append('<li><a href="studies/'+html.escape(study['slug'],quote=True)+'/index.html">'+html.escape(study['title'])+'</a></li>')
 first=studies(root)[0]['slug']
 page=(root/'web/index.html').read_text().replace('<!--STUDIES-->','\n'.join(links)).replace('{{study-report}}',f'studies/{first}/index.html').replace('{{study-explore}}',f'studies/{first}/explore.html')
 (out/'index.html').write_text(rewrite_html_links(page,'index.html',allowed))
 inputs=[*[root/name for name in document_sources(root,studies(root))],root/'scripts/publication.py',root/'scripts/markdown_subset.py',root/'scripts/paper_pages.py',*[root/'scripts/transforms'/n for n in ('public_metadata_v1.py','annotation_text_v1.json')],root/'studies/registry.json',root/'web/index.html',*[root/'data'/name for name in sorted(SHARED_DATA)],*[root/'web'/name for name in sorted(WEB_ASSETS)],*[root/name for name in sorted(SITE_NOTICES)]]
 write(out/'manifest.json',{'schema_version':1,'validation':audit,'source_files':{str(f.relative_to(root)):sha(f) for f in inputs},'files':{name:sha(out/name) for name in sorted(allowed-{'manifest.json'})}})
 print(json.dumps({'build':'passed','studies':len(studies(root))}));return out

def build_study(root,study,out):
 dest=study_path(root,study);audit=validate_study(root,study);out.mkdir(parents=True,exist_ok=True)
 rows=table_rows(root,study)
 speeds=generation_speed_rows(read(dest/'data/answers.json')['answers'],read(dest/'data/results.json')['configurations'],len(read(root/'data/visibility.json')['case_ids']))
 with (out/'speed.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(speeds[0]));w.writeheader();w.writerows(speeds)
 write(out/'speed.json',{'table':speeds})
 with (out/'comparison.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 md=['# Configuration comparison','', 'Each row covers all 120 cases for one configuration and passage condition; 18 of those cases are public. Rows are grouped by total-parameter size class, then ordered by total parameters. A few answers couldn\'t be graded as clearly right or wrong; those are left out, so some counts are out of fewer than 120. Times are in seconds. They include retries and leave out model loading and grading. An answer is fully correct when it satisfies every required claim and contains no material error. The p95 is the slower end of the distribution, where 1 request in 20 is slower. Modes off and on mean thinking off and on; on (low) means thinking on at low effort. Models labelled low or native cannot turn thinking off: low ran at low effort, and native ran with thinking on.','', '| Size class | Model | Mode | Passages | Mean claim score | Fully correct | Material errors | Mean s | Median s | p25 s | p75 s | p95 s | >30 s |','|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in rows:md.append('| '+' | '.join([r['size_class'],r['model'],r['mode'],r['passages'],fmt(r['mean_claim_score']),str(r['fully_correct'])+'/'+str(r['profile_assessed']),str(r['material_errors'])+'/'+str(r['material_error_assessed']),*[fmt(r[k],2) for k in ['mean_seconds','median_seconds','p25_seconds','p75_seconds','p95_seconds']],str(r['above_30_seconds'])+'/'+str(r['timed_records'])])+' |')
 (out/'comparison.md').write_text('\n'.join(md)+'\n')
 # Standalone SVG uses a logarithmic time axis to retain long tails.
 chosen=[r for r in rows if r['passages']=='With oracle passages'];svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="'+str(160+len(chosen)*40)+'" role="img"><title>With oracle passages: median and P95 time by total-parameter size class</title><rect width="100%" height="100%" fill="#fafbf7"/><text x="20" y="28" font-family="sans-serif" font-size="20">With oracle passages · median (dot) and P95 (line), logarithmic seconds</text>']
 maximum=max(r['p95_seconds'] for r in chosen);scale=lambda v:480+600*math.log1p(v)/math.log1p(maximum)
 previous=None;offset=0
 for i,r in enumerate(chosen):
  if r['size_class']!=previous:
   heading=r['size_class'].capitalize()+' · total parameters';svg.append(f'<text x="20" y="{55+i*40+offset}" font-family="sans-serif" font-size="15" font-weight="bold">{heading}</text>');offset+=30;previous=r['size_class']
  y=65+i*40+offset;label=html.escape(r['model']+' · '+r['mode']);svg.append(f'<text x="20" y="{y+5}" font-family="sans-serif" font-size="13">{label}</text><line x1="480" x2="{scale(r["p95_seconds"]):.1f}" y1="{y}" y2="{y}" stroke="#91a894" stroke-width="5"/><circle cx="{scale(r["median_seconds"]):.1f}" cy="{y}" r="5" fill="#284e3d"/><text x="{scale(r["p95_seconds"])+8:.1f}" y="{y+4}" font-family="sans-serif" font-size="11">{r["p95_seconds"]:.1f}s</text>')
 svg.append('</svg>');(out/'latency.svg').write_text(''.join(svg))
 prefix='studies/'+study['slug']+'/'
 routes=source_routes(root,studies(root));template=(dest/'web/index.html').read_text()
 # The five report examples link to their selected configurations.
 case_links=read(dest/'web/report-links.json')
 content=report_content((dest/'report/REPORT.md').read_text(),load_figures(dest/'web/figures.html'),link_mapper(prefix+'report/REPORT.md',prefix+'index.html',routes,case_links))
 (out/'index.html').write_text(paper_page(template,content,prefix+'index.html',study['slug'],'<script src="../../assets/report-figures.js" defer></script>'))
 (out/'explore.html').write_text(rewrite_html_links((dest/'web/explore.html').read_text(),prefix+'explore.html',generated_paths(root)))
 (out/'comparison.html').write_text(paper_page(template,back_to_report(prefix+'comparison.html',study['slug'])+render_markdown('\n'.join(md)),prefix+'comparison.html',study['slug']))
 write(out/'comparison.json',{'table':rows})
 index={}
 for name,case,cfg,answers in answer_shards(root,study):
  write(out/name,{'answers':answers})
  index.setdefault(case,{})[cfg]=name
 write(out/'answer-index.json',index)
 for name in SHARED_DATA:(out/name).write_bytes((root/'data'/name).read_bytes())
 for name in STUDY_DATA:(out/name).write_bytes((dest/'data'/name).read_bytes())
 for name in STUDY_DOCS:(out/name).write_bytes((dest/'docs'/name).read_bytes())
 (out/'THIRD_PARTY_NOTICES.md').write_text((root/'THIRD_PARTY_NOTICES.md').read_text().replace('(assets/fonts/','(../../assets/fonts/').replace('(README.md#license)','(../../README.md#license)'))
 inputs=[root/'studies/registry.json',dest/'config.json',root/'scripts/publication.py',root/'scripts/markdown_subset.py',root/'scripts/paper_pages.py',*[root/'scripts/transforms'/n for n in ('public_metadata_v1.py','annotation_text_v1.json')],dest/'report/REPORT.md',dest/'README.md',dest/'web/figures.html',dest/'web/report-links.json',*[root/'data'/name for name in sorted(SHARED_DATA)],*[dest/'data'/name for name in sorted(STUDY_DATA)],*[dest/'docs'/name for name in sorted(STUDY_DOCS)],dest/'web/index.html',dest/'web/explore.html',root/'THIRD_PARTY_NOTICES.md',*[root/'web'/name for name in sorted(WEB_ASSETS)]]
 manifest={'schema_version':1,'validation':audit,'source_files':{str(f.relative_to(root)):sha(f) for f in inputs},'files':{str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='manifest.json'}};write(out/'manifest.json',manifest)
 print(json.dumps({'study':study['slug'],'build':'passed','public_answers':study['public_answer_records'],'aggregate_cells':study['conditions']}))

def package(root=ROOT,output=None):
 root=Path(root);out=Path(output) if output else root/'dist';out.mkdir(parents=True,exist_ok=True);site=build(root)
 files=release_paths(root)+[site/name for name in sorted(generated_paths(root))];target=out/'d20-bench-study1.zip'
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for f in files:
   entry=zipfile.ZipInfo('d20-bench/'+str(f.relative_to(root)),date_time=(1980,1,1,0,0,0));entry.external_attr=0o100644<<16;entry.compress_type=zipfile.ZIP_DEFLATED;z.writestr(entry,f.read_bytes())
 write(out/'release-manifest.json',{'archive_sha256':sha(target),'archive':target.name,'files':len(files)})
 print(json.dumps({'package':target.name,'files':len(files)}))

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 imp=sub.add_parser('import-private');imp.add_argument('--source-root',required=True,type=Path);imp.add_argument('--source-manifest',required=True,type=Path);imp.add_argument('--case-reviews',required=True,type=Path);imp.add_argument('--study',choices=[s['slug'] for s in studies()])
 sub.add_parser('validate');b=sub.add_parser('build');b.add_argument('--output-dir',type=Path)
 z=sub.add_parser('package');z.add_argument('--output-dir',type=Path)
 s=sub.add_parser('serve');s.add_argument('--port',type=int,default=8000)
 args=p.parse_args()
 if args.command=='import-private':import_private(args.source_root,study_slug=args.study,source_manifest=args.source_manifest,case_reviews=args.case_reviews)
 elif args.command=='validate':print(json.dumps(validate()))
 elif args.command=='build':build(output=args.output_dir)
 elif args.command=='package':package(output=args.output_dir)
 else:
  from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
  from functools import partial
  site=build();print('Preview on http://127.0.0.1:'+str(args.port),flush=True)
  ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=str(site))).serve_forever()
if __name__=='__main__':main()
