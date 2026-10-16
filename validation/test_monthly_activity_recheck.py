from historical_source import before_friend
import unittest,json,hashlib
from pathlib import Path
from mq_subset import ROOT
import test_monthly
E=ROOT/'flows/166_领月卡龙石/evidence/活动入口复核'
MODULE='flows/166_领月卡龙石/领月卡龙石.mq'
class ActivityRecheck(unittest.TestCase):
 def setUp(self):
  self.f=test_monthly.MonthlyFlow();self.f.setUp();self.e=self.f.e;self.ocr=[];self.returns=[]
  self.e['ReadActivityText']=lambda *a:self.ocr.append(a) or ''
  self.e['ReturnToHall']=lambda:self.returns.append(self.f.now) or 1
  self.f.visible={'166_大厅识别一','166_大厅活动入口一'}
 def test_empty_ocr_after_click_uses_professional_frame_one(self):
  self.f.after=lambda *a:self.f.visible.add('166_活动框一')
  self.assertEqual(self.e['EnterMonthlyActivities'](),1)
  self.assertEqual(self.f.events,[(100,1100,1500)])
  self.assertEqual(len(self.returns),2);self.assertEqual(len(self.ocr),1)
  self.assertTrue(any('当前位置活动框复核成功' in x for x in self.f.logs));self.assertFalse(self.e['terminalConfirmed'])
 def test_frame_two_fallback_also_confirms_after_click(self):
  self.f.after=lambda *a:self.f.visible.add('166_活动框二')
  self.assertEqual(self.e['EnterMonthlyActivities'](),1);self.assertEqual(len(self.f.events),1);self.assertEqual(len(self.returns),2)
 def test_unknown_frame_and_empty_ocr_still_times_out(self):
  self.e['businessLimit']=8000
  self.assertEqual(self.e['EnterMonthlyActivities'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertGreater(len(self.returns),2)
 def test_activity_frame_alone_cannot_complete_monthly_business(self):
  self.f.after=lambda *a:self.f.visible.add('166_活动框一')
  self.assertEqual(self.e['ExecuteMonthlyStones'](),4);self.assertFalse(self.e['terminalConfirmed']);self.assertFalse(self.e['monthDone']);self.assertEqual(self.e['monthCount'],0)
 def test_nonpurchased_full_business_continues_without_ocr_title(self):
  self.f.after=lambda *a:self.f.visible.update({'166_活动框一','166_月卡页面','166_类型未购买'})
  self.assertEqual(self.e['ExecuteMonthlyStones'](),1);self.assertTrue(self.e['terminalConfirmed']);self.assertEqual(self.e['monthCardType'],0);self.assertEqual(self.e['monthCount'],0)
 def test_only_five_line_professional_recheck_added(self):
  before=(E/'修改前月卡.txt').read_text('utf-8-sig');now=(ROOT/MODULE).read_text('utf-8-sig');branch=(E/'精确新增分支.txt').read_text('utf-8')
  self.assertEqual(now.replace(branch,'',1),before)
  for rel,h in json.loads((E/'修改前基线.json').read_text('utf-8')).items():
   if rel!=MODULE:self.assertEqual(hashlib.sha256(before_friend(ROOT/rel).read_bytes()).hexdigest(),h,rel)
