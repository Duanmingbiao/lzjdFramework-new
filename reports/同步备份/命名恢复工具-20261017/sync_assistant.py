"""Sync only this fresh project to its independently named assistant script. No device run."""
from pathlib import Path
import hashlib,json,uuid,datetime,shutil,subprocess,sys
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
  if target.parent!=TARGET_DIR or not target.name.startswith('龙珠激斗脚本('):raise RuntimeError('Unexpected destination')
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
if __name__=='__main__':sync()
