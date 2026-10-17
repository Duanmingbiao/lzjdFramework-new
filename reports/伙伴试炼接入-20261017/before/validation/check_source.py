from pathlib import Path
import json,re,hashlib
from mq_symbols import symbol_conflicts
R=Path(__file__).resolve().parents[1]
c=json.loads((R/'project.json').read_text('utf-8-sig'));sources=[R/c['entry']]+[R/x for x in c['modules']]
issues=[];defs=set();calls=set()
issues.extend(symbol_conflicts((str(p),p.read_text('utf-8-sig')) for p in sources))
for p in sources:
 t=p.read_text('utf-8-sig');b=p.read_bytes()
 if not b.startswith(b'\xef\xbb\xbf') or b'\n' in b.replace(b'\r\n',b''):issues.append('source encoding/newline: '+str(p))
 if '\ufffd' in t:issues.append('replacement char: '+str(p))
 defs.update(re.findall(r'(?m)^(?:Function|Sub) (\w+)\(',t))
 calls.update(re.findall(r'\bCall (\w+)\(',t))
 if any(k in t.lower() for k in ['adb ', 'keycode_back','keycode back','accessibility']):issues.append('forbidden API: '+str(p))
 if any(x in str(p) for x in ['078_', '168_', '169_', '167_', '166_', '055_', '056_', '050_', '151_', '152_', '070_', '032_', '083_', '084_', '085_', '088_', '071_']) and re.search(r'\b(?:KillApp|RunApp|CommitTask|SchedulerStep)\b',t):issues.append('business boundary: '+str(p))
 if p.suffix=='.mq' and re.search(r'(?m)^local |LuaAuxLib|GK\.',t):issues.append('Lua syntax: '+str(p))
 if any(k in str(p) for k in ['015_','014_','013_','012_','079_','082_','080_','081_','153_','154_','155_','150_']) and re.search(r'\b(?:KillApp|RunApp|CommitTask|SchedulerStep)\b',t):issues.append('business boundary: '+str(p))
# Function return assignment is legal; reading a bare function name is not.
for path in sources:
 for number,line in enumerate(path.read_text('utf-8-sig').splitlines(),1):
  code=line.split('//',1)[0]
  code=re.sub(r'Thread\.Start\(\w+(?=[,)])', 'Thread.Start(0', code)
  code=re.sub(r'"(?:[^"]|"")*"','""',code)
  for name in defs:
   if re.match(r'^\s*'+re.escape(name)+r'\s*=',code):continue
   if re.search(r'\b'+re.escape(name)+r'\b(?!\s*\()',code):
    issues.append('bare function reference: '+str(path)+':'+str(number)+': '+name)

if calls-defs:issues.append('unresolved Call: '+str(calls-defs))
if c['registeredTasks']!=[168,169,167,166,55,56,50,51,52,53,54,151,152,70,32,83,84,85,86,87,88,71,78,79,82,80,81,153,154,155,150,12,13,14,15]:issues.append('unexpected business registration')
for p in json.loads((R/'evidence/图色参数.json').read_text('utf-8')):
 x1,y1,x2,y2=p['definition'][:4]
 if not(0<=x1<=x2<=719 and 0<=y1<=y2<=1279):issues.append('invalid rectangle '+p['name'])
report={'scope':'static structure and encoding only; not official MQ compilation','issues':issues,'moduleCount':len(sources),'pass':not issues}
(R/'reports/静态检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False));raise SystemExit(bool(issues))
