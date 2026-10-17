import unittest,json,hashlib
from types import SimpleNamespace
from mq_subset import ROOT,load
E=ROOT/'flows/055_好友体力/evidence'
class FriendFlow(unittest.TestCase):
 def setUp(self):
  self.now=0;self.taps=[];self.logs=[];self.hits=[];self.visible=True
  self.e=dict(RESULT_OK=1,RESULT_TIMEOUT=4,terminalConfirmed=False,GAME_PACKAGE='game',Sys=SimpleNamespace(AppIsFront=lambda p:True),TickCount=lambda:self.now,Delay=self.delay,Note=self.logs.append,SetStage=lambda x:None,BusinessExpired=lambda:self.now>=12000,MatchPattern=self.match,TouchPoint=self.tap)
  load(['flows/055_好友体力/好友体力.mq'],self.e)
 def delay(self,n):self.now+=n
 def match(self,n):
  self.hits.append(n);self.e['foundX']=100;self.e['foundY']=1100
  return self.visible and n=='055_好友页面'
 def tap(self,x,y,w):self.taps.append((x,y,w));self.delay(w)
 def test_exact_two_groups_and_fresh_anchor(self):
  self.assertEqual(self.e['ExecuteFriendEnergy'](),1)
  self.assertEqual(self.taps,[(350,990,500),(350,990,1000),(560,990,500),(560,990,0)])
  self.assertEqual(self.hits.count('055_好友页面'),3);self.assertTrue(self.e['terminalConfirmed'])
 def test_unknown_entry_is_timeout_never_success(self):
  self.visible=False;self.assertEqual(self.e['ExecuteFriendEnergy'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(self.now,10000)
 def test_interrupt_after_first_pair_cannot_succeed(self):
  self.e['BusinessExpired']=lambda:len(self.taps)>=2
  self.assertEqual(self.e['ExecuteFriendEnergy'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertEqual(len(self.taps),2)
 def test_missing_action_page_uses_total_timeout(self):
  old=self.match
  self.e['MatchPattern']=lambda n:old(n) if len(self.hits)<2 else False
  self.assertEqual(self.e['ExecuteFriendEnergy'](),4);self.assertFalse(self.e['terminalConfirmed'])
 def test_public_commit_requires_hall_and_preserves_others(self):
  e=self.e;e.update(currentTask=55,resumeTask=55,friendInterval=14400,friendCount=0,friendFirst=True,BeginForegroundCommit=lambda:True,EndForegroundCommit=lambda:None,mailCount=7,rewardCount=8,signCount=9,monthCount=10)
  load(['common/任务状态.mq'],e);e['terminalConfirmed']=True
  self.assertFalse(e['CommitTask'](False));self.assertEqual(e['friendCount'],0)
  self.assertTrue(e['CommitTask'](True));self.assertEqual(e['friendCount'],1);self.assertEqual(e['friendDue'],14400000)
  self.assertEqual([e[k] for k in ['mailCount','rewardCount','signCount','monthCount']],[7,8,9,10])
 def test_recovery_55_has_priority_even_disabled(self):
  self.e.update(resumeTask=55,registeredTask=168,rewardRegisteredTask=169,signRegisteredTask=167,monthRegisteredTask=166,friendRegisteredTask=55,friendEnabled=False)
  load(['common/任务注册.mq'],self.e);self.assertEqual(self.e['SelectDueTask'](),55)
 def test_existing_four_business_bytes_unchanged(self):
  for folder in ['168_领邮件奖励','169_领任务奖励','167_日常签到','166_领月卡龙石']:
   for p in (ROOT/'flows'/folder).glob('*.mq'):
    old=E/'before'/p.relative_to(ROOT).with_suffix('.txt');self.assertEqual(p.read_bytes(),old.read_bytes())
 def test_catalog_append_only_exact_conversion(self):
  old=json.loads((E/'before/evidence/图色参数.json').read_text('utf-8'));now=[x for x in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if not x['name'].startswith(('150_','155_','154_','153_','081_','080_','082_','079_','078_','056_','050_','151_','152_','070_','032_','强敌_','083_','084_','085_'))]
  self.assertEqual(now[:-2],old)
  converted=json.loads((E/'图色转换.json').read_text('utf-8'));self.assertEqual([x['definition'] for x in now[-2:]],[x['definition'] for x in converted])
