import unittest,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from mq_subset import load
from test_qq_screenshots import match_pixels,IMAGES
R=Path(__file__).resolve().parents[1]
E=R/'flows/001_游戏重连/evidence/游戏协议弹窗'
REC=json.loads((E/'截图图色参数.json').read_text('utf-8'))
IMG=np.asarray(Image.open(E/'游戏协议弹窗.png').convert('RGB'),dtype=np.int16)
class Agreement(unittest.TestCase):
 def test_screenshot_hits_only_agree_button(self):
  hits=match_pixels(IMG,REC['definition']);self.assertTrue(hits)
  for x,y in hits:self.assertTrue(443<x+58<614 and 866<y+16<927)
 def test_missing_button_or_content_rejected(self):
  for box in [(850,940),(400,580)]:
   img=IMG.copy();img[box[0]:box[1]]=0;self.assertFalse(match_pixels(img,REC['definition']))
  for img in IMAGES:self.assertFalse(match_pixels(img,REC['definition']))
 def test_protected_mq_unchanged(self):
  baseline=json.loads((E/'修改前基线.json').read_text('utf-8'))
  allowed={Path('common/图色参数.mq'),Path('flows/001_游戏重连/登录游戏.mq')}
  for name,digest in baseline.items():
   if Path(name) not in allowed:self.assertEqual(hashlib.sha256((R/name).read_bytes()).hexdigest(),digest,name)
 def run_login(self,visible,limit):
  env={};now=[1000];clicks=[];other=[]
  load(['common/运行计时.mq','flows/001_游戏重连/登录游戏.mq'],env)
  class Sys:
   def AppIsFront(self,p):return True
  def match(name):env['foundX']=470;env['foundY']=880;return visible and name=='游戏协议弹窗'
  def delay(ms):now[0]+=ms
  def tap(x,y,ms):clicks.append((x,y,ms));delay(ms)
  env.update(Sys=Sys(),GAME_PACKAGE='game',RESULT_TIMEOUT=4,RESULT_OK=1,loginLimit=limit,
   TickCount=lambda:now[0],Delay=delay,Note=lambda m:None,SetStage=lambda m:None,
   ResetHallCheck=lambda:None,ResetHallClearing=lambda:None,StartGame=lambda:None,
   ConfirmHall=lambda:False,HandleQQ=lambda:False,MatchPattern=match,TouchPoint=tap,
   TouchPattern=lambda n,w:other.append(n) or False,ClearHallObstacle=lambda:False,
   currentTask=168,resumeTask=168)
  result=env['EnsureGameHall']()
  return result,env,clicks,other,now[0]
 def test_repeated_agreement_keeps_total_deadline_and_pending_business(self):
  result,e,clicks,other,now=self.run_login(True,2100)
  self.assertEqual(result,4);self.assertEqual(e['loginStarted'],1000)
  self.assertEqual(e['currentTask'],168);self.assertEqual(e['resumeTask'],168)
  self.assertEqual(clicks,[(528,896,1000)]*3);self.assertEqual(other,[])
  self.assertLess(now,4200)
 def test_unrecognized_page_never_clicks_or_succeeds(self):
  result,e,clicks,_,_=self.run_login(False,300)
  self.assertEqual(result,4);self.assertEqual(clicks,[])
if __name__=='__main__':unittest.main()
