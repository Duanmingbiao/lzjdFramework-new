from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def build():
 c=json.loads((ROOT/'project.json').read_text('utf-8-sig'))
 paths=[c['entry']]+c['modules']
 actual={p.relative_to(ROOT).as_posix() for d in ['app','common','flows'] for p in (ROOT/d).rglob('*.mq')}
 if set(paths)!=actual or len(paths)!=len(set(paths)):raise ValueError('module inventory mismatch')
 content='\r\n\r\n'.join('// '+p+'\r\n'+(ROOT/p).read_text('utf-8-sig').replace('\n','\r\n') for p in paths)
 ui=(ROOT/c['ui']).read_text('utf-8-sig').replace('\n','\r\n')
 out={}
 for folder,encoding in [('UTF-8查看版','utf-8-sig'),('手机助手3.8导入版','gbk')]:
  target=ROOT/'dist'/folder;target.mkdir(parents=True,exist_ok=True)
  for ext,text in [('mq',content),('uip',ui)]:
   p=target/('龙珠激斗脚本.'+ext);p.write_bytes(text.encode(encoding,errors='strict'));out[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 (ROOT/'reports/构建记录.json').write_text(json.dumps({'outputs':out,'validation':'concatenation and encoding only; not official MQ compilation'},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Built standard MQ text and UI; no compiler or device execution.')
if __name__=='__main__':build()
