"""Execute only the actual MQ control-flow subset under mocked APIs. Not an MQ compiler."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def expression(s):
 s=re.sub(r'\bAnd\b','and',s);s=re.sub(r'\bOr\b','or',s);s=re.sub(r'\bNot\b','not',s)
 s=s.replace(' & ',' + ');s=s.replace('<>','!=');s=re.sub(r'(?<![<>=!])=(?!=)','==',s)
 return s

def load(paths, env):
 for key,value in {'experienceEnabled':False,'NewExperienceSession':lambda:None,'LoadExperienceSettings':lambda:None,'SelectExperience':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'geneEnabled':False,'geneNoRestartPending':False,'NewGeneSession':lambda:None,'LoadGeneSettings':lambda:None,'SelectGene':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'soulEnabled':False,'NewSoulSession':lambda:None,'LoadSoulSettings':lambda:None,'SelectSoul':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'goldEnabled':False,'NewGoldSession':lambda:None,'LoadGoldSettings':lambda:None,'SelectGold':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'advEnabled':False,'NewAdventureSession':lambda:None,'LoadAdventureSettings':lambda:None,'SelectAdventure':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'snakeEnabled':False,'NewSnakeSession':lambda:None,'LoadSnakeSettings':lambda:None,'SelectSnake':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'plantEnabled':False,'NewPlantSession':lambda:None,'LoadPlantSettings':lambda:None,'SelectPlant':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'senzuEnabled':False,'NewSenzuSession':lambda:None,'LoadSenzuSettings':lambda:None,'SelectSenzu':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'duelEnabled':False,'duelRunning':False,'duelTimedOut':False,'duelRestartOnTimeout':True,'NewDuelSession':lambda:None,'LoadDuelSettings':lambda:None,'SelectDuel':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'friezaEnabled':False,'friezaRunning':False,'friezaTimedOut':False,'friezaRestartOnTimeout':True,'NewFriezaSession':lambda:None,'LoadFriezaSettings':lambda:None,'SelectFrieza':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'memoryEnabled':False,'memoryUncompleted':False,'NewMemorySession':lambda:None,'LoadMemorySettings':lambda:None,'SelectMemory':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'universeEnabled':False,'NewUniverseSession':lambda:None,'LoadUniverseSettings':lambda:None,'SelectUniverse':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'gatherEnabled':False,'NewGatherSession':lambda:None,'LoadGatherSettings':lambda:None,'SelectGather':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'earthEnabled':False,'earthRegisteredTask':71,'NewEarthSession':lambda:None,'LoadEarthSettings':lambda:None,'SelectEarth':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'namekEnabled':False,'namekRegisteredTask':88,'namekDeferred':False,'NewNamekSession':lambda:None,'LoadNamekSettings':lambda:None,'SelectNamek':lambda:0}.items():env.setdefault(key,value)
 # Unit fixtures without the monitor model the no-interruption dependency explicitly.
 for key,value in {'beyondEnabled':False,'beyondRegisteredTask':87,'NewBeyondSession':lambda:None,'LoadBeyondSettings':lambda:None,'SelectBeyond':lambda:0,'legendEnabled':False,'legendRegisteredTask':86,'NewLegendSession':lambda:None,'LoadLegendSettings':lambda:None,'SelectLegend':lambda:0}.items():env.setdefault(key,value)
 for key,value in {'redEnabled':False,'IsRedArmy':lambda t:False,'NewRedArmySession':lambda:None,'LoadRedArmySettings':lambda:None,'SelectRedArmy':lambda:0,'crossEnabled':False,'NewCrossBossSession':lambda:None,'LoadCrossBossSettings':lambda:None,'SelectCrossBoss':lambda:0,'worldEnabled':False,'cellEnabled':False,'IsWorldBoss':lambda t:False,'SelectWorldBoss':lambda:0,'NewWorldBossSession':lambda:None,'LoadWorldBossSettings':lambda:None,'coopEnabled':False,'coopRegisteredTask':152,'NewCoopSession':lambda:None,'LoadCoopSettings':lambda:None,'CoopTimeEligible':lambda:False,'wukongEnabled':False,'wukongInterval':3600,'wukongRegisteredTask':151,'NewWukongSession':lambda:None,'LoadWukongSettings':lambda:None,'staminaEnabled':False,'IsTimedStamina':lambda x:False,'SelectTimedStamina':lambda:0,'LoadTimedStaminaSettings':lambda:None,'NewTimedStaminaSession':lambda:None,'qfriendEnabled':False,'qfriendInterval':14400,'qfriendRegisteredTask':56,'friendEnabled':False,'friendInterval':14400,'friendRegisteredTask':55,'monthEnabled':False,'monthInterval':3600,'monthRegisteredTask':166,'monthKeepDownload':False,'signEnabled':False,'signInterval':3600,'signRegisteredTask':167,'ForegroundInterrupted':lambda:False,'HandleForegroundRecovery':lambda:False,'BeginForegroundCommit':lambda:True,'EndForegroundCommit':lambda:None,'foregroundLoginPending':False,'BeginForegroundRecovery':lambda:None,'EndForegroundRecovery':lambda:None}.items():env.setdefault(key,value)
 env['mqcat']=lambda *args: ''.join(str(x) for x in args)
 allglobals=[]
 for line in (ROOT/'app/入口.mq').read_text('utf-8-sig').splitlines():
  if line.startswith('Dim '):allglobals.extend(x.strip() for x in line[4:].split(','))
 for path in paths:
  lines=(ROOT/path).read_text('utf-8-sig').splitlines();out=[];indent=0;fn=None;isfun=False
  for raw in lines:
   s=raw.strip()
   if not s or s.startswith('//'):continue
   m=re.match(r'(Function|Sub) (\w+)\((.*?)\)$',s)
   if m:
    isfun=m[1]=='Function';fn=m[2];out.append(f'def {fn}({m[3]}):');indent=1
    out.append('    global '+','.join(allglobals));out.append('    mq_result = None');continue
   if s in ('End Function','End Sub'):
    out.append('    return mq_result');indent=0;fn=None;continue
   if s.startswith('Dim '):continue
   if s=='End If':indent-=1;continue
   if s=='Loop':indent-=1;continue
   if s=='Next':indent-=1;continue
   loop=re.fullmatch(r'For (\w+) = (.+) To (.+)',s)
   if loop:
    out.append('    '*indent+'for '+loop[1]+' in range(int('+loop[2]+'), int('+loop[3]+')+1):');indent+=1;continue
   if s.startswith('ElseIf '):
    indent-=1;out.append('    '*indent+'elif '+expression(s[7:-5])+':');indent+=1;continue
   if s=='Else':
    indent-=1;out.append('    '*indent+'else:');indent+=1;continue
   if s.startswith('If ') and s.endswith(' Then'):
    out.append('    '*indent+'if '+expression(s[3:-5])+':');indent+=1;continue
   if s=='Do' or s.startswith('Do While '):
    out.append('    '*indent+'while '+(expression(s[9:]) if s.startswith('Do While ') else 'True')+':');indent+=1;continue
   if s in ('Exit Function','Exit Sub'):s='return mq_result'
   elif s in ('Exit Do','Exit For'):s='break'
   elif s.startswith('Call '):s=s[5:]
   elif s.startswith('Delay '):s='Delay('+s[6:]+')'
   elif s.startswith('RunApp '):s='RunApp('+s[7:]+')'
   elif s.startswith('KillApp '):s='KillApp('+s[8:]+')'
   elif s.startswith(fn+' ='):s='mq_result'+s[len(fn):]
   if s.startswith('TracePrint '):s='TracePrint('+s[11:]+')'
   if s=='ReleaseCapture':s='ReleaseCapture()'
   if s.startswith('Swipe '):s='Swipe('+s[6:]+')'
   if s.startswith('Tap '):s='Tap('+s[4:]+')'
   assignment=re.match(r'^(\w+) = (.*)$',s)
   if assignment:
    rhs=assignment[2]
    if ' & ' in rhs:rhs='mqcat('+rhs.replace(' & ', ', ')+')'
    else:rhs=expression(rhs)
    s=assignment[1]+' = '+rhs
   # MQ concatenation is only used in diagnostic messages here.
   if ' & ' in s:
    call=re.fullmatch(r'(\w+)\((.*)\)',s)
    if not call:raise ValueError('Unsupported MQ concatenation: '+s)
    s=call[1]+'(mqcat('+call[2].replace(' & ', ', ')+'))'
   out.append('    '*indent+s)
  code='\n'.join(out);exec(compile(code,str(path),'exec'),env)
 return env

