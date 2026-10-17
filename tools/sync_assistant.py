"""Sync only this fresh project to its independently named assistant script. No device run."""
from pathlib import Path
import hashlib,json,uuid,datetime,shutil,subprocess,sys,argparse
from build import build,ROOT
TARGET_DIR=Path(r'D:\ProgramData\按键精灵\按键精灵手机助手\Script')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def matches_saved(path, expected):
 if digest(path) == expected:
  return True
 if path.suffix not in ['.mq', '.uip'] or not path.exists():
  return False
 canonical = path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
 return hashlib.sha256(canonical).hexdigest() == expected

def sync():
 subprocess.run([sys.executable,str(ROOT/'validation/check_source.py')],check=True)
 subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'validation'),'-p','test_*.py'],check=True)
 build();config=ROOT/'assistant-sync.json'
 if not TARGET_DIR.is_dir():raise RuntimeError('Assistant Script directory missing')
 if config.exists():
  cfg=json.loads(config.read_text('utf-8'));target=Path(cfg['target'])
  if target.parent!=TARGET_DIR or target.name!=cfg['name']+'('+cfg['id']+').mq':raise RuntimeError('Unexpected destination')
  for ext in ['.mq','.uip','.prop']:
   p=target.with_suffix(ext)
   if not matches_saved(p,cfg['lastSynced'].get(ext)):raise RuntimeError('Assistant-side changes detected; sync stopped: '+str(p))
 else:
  uid=str(uuid.uuid4());target=TARGET_DIR/('龙珠激斗脚本('+uid+').mq')
  if list(TARGET_DIR.glob('龙珠激斗脚本(*')):raise RuntimeError('A same-name script already exists; inspect before choosing a target')
  cfg={'name':'龙珠激斗脚本','id':uid,'target':str(target),'lastSynced':{}}
 sources={ext:(ROOT/'dist/手机助手3.8导入版'/('龙珠激斗脚本'+ext)).read_bytes() for ext in ['.mq','.uip']}
 for b in sources.values():b.decode('gbk',errors='strict')
 if config.exists():
  sources['.prop']=target.with_suffix('.prop').read_bytes()
 else:
  prop={'BestResolution':{'X':720,'Y':1280},'ChangeFileList':0,'Description':'邮件闭环首版；待手机助手编译及实机验证','FileVersion':{x:0 for x in ['.atc','.mq','.prop','.rtd','.uip','.uis']},'Name':'龙珠激斗脚本','id':cfg['id']}
  sources['.prop']=json.dumps(prop,ensure_ascii=False,indent=3).encode('gbk')
 changed=[ext for ext,b in sources.items() if digest(target.with_suffix(ext))!=hashlib.sha256(b).hexdigest()]
 if changed:
  backup=ROOT/'reports/同步备份'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup.mkdir(parents=True)
  for ext in changed:
   p=target.with_suffix(ext)
   if p.exists():shutil.copy2(p,backup/p.name)
  # One independent ID; no existing user script is used as a template or overwritten.
  for ext in changed:
   p=target.with_suffix(ext);tmp=p.with_suffix(ext+'.new')
   with tmp.open('xb') as f:f.write(sources[ext])
   tmp.replace(p)
 cfg['lastSynced']={ext:digest(target.with_suffix(ext)) for ext in sources}
 cfg['validation']='File sync verified by SHA256. Assistant UI loading, official compilation and device running are not verified.'
 config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Synced new independent script: '+str(target));print(cfg['validation'])
def restore_deleted(name):
 """Explicit recovery after user deletion; never merge with surviving script files."""
 if name not in ['龙珠激斗','龙珠激斗脚本']:raise ValueError('Unsupported script name')
 config=ROOT/'assistant-sync.json';journal_path=ROOT/'reports/授权同步边界.json'
 old_config=config.read_bytes();old_journal=journal_path.read_bytes()
 cfg=json.loads(old_config.decode('utf8'));old_target=Path(cfg['target'])
 if old_target.parent!=TARGET_DIR or old_target.name!=cfg['name']+'('+cfg['id']+').mq':raise RuntimeError('Unexpected old destination')
 if list(TARGET_DIR.glob('*('+cfg['id']+').*')):raise RuntimeError('Project ID still exists; recovery stopped')
 if list(TARGET_DIR.glob(name+'(*')):raise RuntimeError('Same-name project already exists')
 journal=json.loads(old_journal.decode('utf8'));before=journal[-1]['after']
 for p,h in before.items():
  if Path(p).parent==TARGET_DIR:
   if Path(p).exists():raise RuntimeError('Old target still exists')
  elif digest(Path(p))!=h:raise RuntimeError('Protected baseline changed: '+p)
 # The deleted-target protection assertions are evaluated after recreation, with
 # an explicit path migration record. No business test is disabled.
 subprocess.run([sys.executable,'-B','-c',"import re,runpy,sys;re._MAXCACHE=65536;sys.path.insert(0,'validation');runpy.run_path('validation/check_source.py',run_name='__main__')"],cwd=ROOT,check=True)
 build()
 target=TARGET_DIR/(name+'('+cfg['id']+').mq')
 sources={ext:(ROOT/'dist/手机助手3.8导入版'/('龙珠激斗脚本'+ext)).read_bytes() for ext in ['.mq','.uip']}
 prop={'BestResolution':{'X':720,'Y':1280},'ChangeFileList':0,'Description':'完整开发工程；待助手官方编译与打包验证','FileVersion':{x:0 for x in ['.atc','.mq','.prop','.rtd','.uip','.uis']},'Name':name,'id':cfg['id']}
 sources['.prop']=json.dumps(prop,ensure_ascii=False,indent=3).encode('gbk')
 for b in sources.values():b.decode('gbk',errors='strict')
 backup=ROOT/'reports/同步备份'/('重新同步-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True)
 shutil.copy2(config,backup/config.name);shutil.copy2(journal_path,backup/journal_path.name)
 created=[]
 try:
  for ext,b in sources.items():
   p=target.with_suffix(ext)
   with p.open('xb') as f:f.write(b)
   created.append(p)
  cfg.update(name=name,target=str(target),lastSynced={ext:digest(target.with_suffix(ext)) for ext in sources})
  cfg['validation']='File sync verified by SHA256. Assistant UI loading, official compilation and device running are not verified.'
  config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
  mapping={str(old_target.with_suffix(ext)):str(target.with_suffix(ext)) for ext in ['.mq','.uip','.prop']}
  after={mapping.get(p,p):digest(Path(mapping.get(p,p))) for p in before}
  record={'authorizedByUser':True,'projectId':cfg['id'],'request':'用户重启覆盖安装并清空助手脚本后，重新同步名为龙珠激斗的工程','deletedByUser':list(mapping),'pathMapping':mapping,'before':before,'after':after,'verification':str(backup/'恢复同步验证.json')}
  journal.append(record);journal_path.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
  subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'validation'),'-p','test_*.py'],cwd=ROOT,check=True)
  for ext,b in sources.items():
   if target.with_suffix(ext).read_bytes()!=b:raise RuntimeError('Post-sync mismatch')
  (backup/'恢复同步验证.json').write_text(json.dumps({'id':cfg['id'],'name':name,'target':str(target),'hashes':cfg['lastSynced'],'preservedSourceAndUIDefaults':True,'runtimeCacheRestored':False,'officialCompilationVerified':False},ensure_ascii=False,indent=2),encoding='utf8')
 except Exception:
  # Roll back only files created by this recovery, after byte identity checks.
  for p in created:
   if p.read_bytes()==sources[p.suffix]:p.unlink()
  config.write_bytes(old_config);journal_path.write_bytes(old_journal)
  raise
 print('Restored named script: '+str(target));print(cfg['validation'])

def sync_code_only():
 """Preserve all existing assistant settings; explicitly journal user-owned metadata."""
 config=ROOT/'assistant-sync.json';journal_path=ROOT/'reports/授权同步边界.json'
 cfg=json.loads(config.read_text('utf8'));target=Path(cfg['target'])
 if target.parent!=TARGET_DIR or target.name!=cfg['name']+'('+cfg['id']+').mq':raise RuntimeError('Unexpected destination')
 if not matches_saved(target,cfg['lastSynced']['.mq']):raise RuntimeError('Assistant code changed; inspect before sync')
 prop=json.loads(target.with_suffix('.prop').read_bytes().decode('gbk'))
 if prop['Name']!=cfg['name'] or prop['id']!=cfg['id']:raise RuntimeError('Project identity mismatch')
 preserved={p:p.read_bytes() for p in TARGET_DIR.glob(target.stem+'.*') if p.suffix!='.mq'}
 if target.with_suffix('.uip') not in preserved:raise RuntimeError('Missing existing UI')
 journal=json.loads(journal_path.read_text('utf8'));before=journal[-1]['after']
 actual={p:digest(Path(p)) for p in before}
 for p,h in before.items():
  if Path(p).parent!=TARGET_DIR and actual[p]!=h:raise RuntimeError('Protected build changed: '+p)
 backup=ROOT/'reports/同步备份'/('79启动修复-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True)
 for p in [config,journal_path,target,*preserved]:shutil.copy2(p,backup/p.name)
 def record(old,new,request):
  journal.append({'authorizedByUser':True,'projectId':cfg['id'],'request':request,'before':old,'after':new})
  journal_path.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
 record(before,actual,'保留用户当前助手配置，仅同步79启动及日志阶段修复；接纳现有配置文件字节，不覆盖')
 checks=[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s',str(ROOT/'validation'),'-p','test_*.py']
 subprocess.run([sys.executable,'-B','-X','utf8','-c',"import re,runpy,sys;re._MAXCACHE=65536;sys.path.insert(0,'validation');runpy.run_path('validation/check_source.py',run_name='__main__')"],cwd=ROOT,check=True)
 subprocess.run(checks,cwd=ROOT,check=True)
 build()
 data=(ROOT/'dist/手机助手3.8导入版/龙珠激斗脚本.mq').read_bytes();data.decode('gbk')
 if any(p.read_bytes()!=b for p,b in preserved.items()):raise RuntimeError('Settings changed concurrently')
 if digest(target)!=actual[str(target)]:raise RuntimeError('Code changed concurrently')
 tmp=target.with_suffix('.mq.new')
 with tmp.open('xb') as f:f.write(data)
 tmp.replace(target)
 cfg['lastSynced']={ext:digest(target.with_suffix(ext)) for ext in ['.mq','.uip','.prop']}
 cfg['validation']='Code-only SHA256 sync; existing settings preserved byte-for-byte; official compilation/device testing pending.'
 config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
 after={p:digest(Path(p)) for p in actual};record(actual,after,'验证后仅同步龙珠激斗代码，保留现有勾选配置')
 subprocess.run(checks,cwd=ROOT,check=True)
 assert target.read_bytes()==data
 assert all(p.read_bytes()==b for p,b in preserved.items())
 (backup/'验证.json').write_text(json.dumps({'target':str(target),'hashes':cfg['lastSynced'],'preserved':{str(p):hashlib.sha256(b).hexdigest() for p,b in preserved.items()},'officialCompilationVerified':False},ensure_ascii=False,indent=2),encoding='utf8')
 print('Code-only sync verified: '+str(target));print('Backup: '+str(backup))

def sync_unchecked():
 """Explicit user-requested file sync; preserve identity and compiled caches."""
 import re,time
 config=ROOT/'assistant-sync.json';journal_path=ROOT/'reports/授权同步边界.json'
 cfg=json.loads(config.read_text('utf8'));target=Path(cfg['target'])
 if cfg['name']!='龙珠激斗' or target.parent!=TARGET_DIR or target.name!=cfg['name']+'('+cfg['id']+').mq':raise RuntimeError('Unexpected existing project')
 prop=json.loads(target.with_suffix('.prop').read_bytes().decode('gbk'))
 if prop['Name']!=cfg['name'] or prop['id']!=cfg['id']:raise RuntimeError('Project identity mismatch')
 for ext in ['.mq','.uip','.prop']:
  if not matches_saved(target.with_suffix(ext),cfg['lastSynced'][ext]):raise RuntimeError('Assistant-side changes detected: '+ext)
 ui=(ROOT/'ui/最小配置.uip').read_text('utf-8-sig')
 from check_ui import check
 check()
 # A missing comma after a layout can hide every following configuration entry.
 unquoted=re.sub(r'"(?:[^"\\]|\\.)*"','""',ui)
 if re.search(r'}\s*[^\s,}\]]',unquoted):raise RuntimeError('UI missing separator after a control/layout')
 previous_ui=target.with_suffix('.uip').read_bytes().decode('gbk')
 names=lambda text:set(re.findall(r'名称\s*:\s*"([^"]+)"',text))
 missing=names(previous_ui)-names(ui)
 if missing:raise RuntimeError('Existing UI controls missing: '+repr(sorted(missing)))
 boxes=re.findall(r'多选框\s*:\s*\{[^{}]*\}',ui)
 if not boxes or any(not re.search(r'选中\s*:\s*false\b',b) for b in boxes):raise RuntimeError('Checkbox defaults must all be false')
 journal=json.loads(journal_path.read_text('utf8'));old_boundary=journal[-1]['after']
 before={p:digest(Path(p)) for p in old_boundary}
 preserved={p:p.read_bytes() for p in TARGET_DIR.glob(target.stem+'.*') if p.suffix not in ['.mq','.uip']}
 backup=ROOT/'reports/同步备份'/('全不勾选-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True)
 for p in [config,journal_path,target,target.with_suffix('.uip'),*preserved]:shutil.copy2(p,backup/p.name)
 build()
 sources={ext:(ROOT/'dist/手机助手3.8导入版'/('龙珠激斗脚本'+ext)).read_bytes() for ext in ['.mq','.uip']}
 for data in sources.values():data.decode('gbk',errors='strict')
 for ext,data in sources.items():
  p=target.with_suffix(ext)
  if digest(p)!=before[str(p)]:raise RuntimeError('Target changed concurrently')
  tmp=p.with_suffix(ext+'.new')
  with tmp.open('xb') as f:f.write(data)
  tmp.replace(p)
 time.sleep(2)
 if any(target.with_suffix(ext).read_bytes()!=data for ext,data in sources.items()):raise RuntimeError('Delayed sync mismatch')
 if any(p.read_bytes()!=data for p,data in preserved.items()):raise RuntimeError('Metadata/cache changed')
 cfg['lastSynced']={ext:digest(target.with_suffix(ext)) for ext in ['.mq','.uip','.prop']}
 cfg['validation']='MQ/UI SHA256 verified after delay; all checkbox defaults false; existing identity, metadata and caches preserved; user will package and test.'
 config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
 after={p:digest(Path(p)) for p in before}
 report={'target':str(target),'id':cfg['id'],'checkboxCount':len(boxes),'allUnchecked':True,'hashes':cfg['lastSynced'],'preserved':{str(p):digest(p) for p in preserved},'assistantOperated':False,'deviceConnected':False}
 report_path=backup/'同步后验证.json';report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 journal.append({'authorizedByUser':True,'projectId':cfg['id'],'request':'同步到既有龙珠激斗脚本，取消所有勾选配置；不连接模拟器、不操作助手、不提交Git','before':old_boundary,'after':after,'verification':str(report_path)})
 journal_path.write_text(json.dumps(journal,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(report,ensure_ascii=False,indent=2));print('Backup: '+str(backup))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--restore-deleted',action='store_true');parser.add_argument('--name',default='龙珠激斗')
 parser.add_argument('--code-only',action='store_true')
 parser.add_argument('--all-unchecked',action='store_true')
 args=parser.parse_args()
 if args.all_unchecked:sync_unchecked()
 elif args.code_only:sync_code_only()
 elif args.restore_deleted:restore_deleted(args.name)
 else:sync()
