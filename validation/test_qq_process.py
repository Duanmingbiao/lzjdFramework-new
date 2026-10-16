from historical_source import before_diagnostics, before_signin
import unittest,json,hashlib
from mq_subset import ROOT
import test_foreground
class QQProcess(unittest.TestCase):
 def setUp(self):self.f=test_foreground.Foreground();self.f.setUp()
 def test_opensdk_over_five_seconds_keeps_login_clock(self):
  f=self.f;f.e['loginStarted']=123;f.sample('com.tencent.mobileqq:openSdk',0);f.sample('com.tencent.mobileqq:openSdk',10000)
  self.assertFalse(f.e['ForegroundInterrupted']());self.assertEqual(f.e['loginStarted'],123)
 def test_opensdk_cancels_other_app_countdown(self):
  f=self.f;f.sample('other',0);f.sample('com.tencent.mobileqq:openSdk',4999);f.sample('com.tencent.mobileqq:openSdk',10000);self.assertFalse(f.e['ForegroundInterrupted']())
 def test_opensdk_authorization_taps_are_not_suppressed(self):
  f=self.f;f.front='com.tencent.mobileqq:openSdk';f.e['TouchPoint'](351,999,1000);self.assertEqual(f.events,[('tap',351,999)]);self.assertEqual(f.now,1000)
 def test_opensdk_does_not_relaunch_running_game(self):
  f=self.f;f.front='com.tencent.mobileqq:openSdk';f.e['StartGame']();self.assertEqual(f.events,[])
 def test_unseen_processes_still_trigger_recovery(self):
  f=self.f
  for p in ['com.tencent.mobileqq.fake','com.tencent.mobileqq:unknown','com.android.launcher3']:
   f.e['InitForegroundMonitor']();f.sample(p,0);f.sample(p,5000);self.assertTrue(f.e['ForegroundInterrupted']())
 def test_only_exact_three_conditions_changed(self):
  E=ROOT/'common/evidence/QQ授权进程';changes=json.loads((E/'精确变更.json').read_text('utf-8'));base=json.loads((E/'修改前基线.json').read_text('utf-8'))
  for p,h in base.items():
   if p not in changes:self.assertEqual(hashlib.sha256(before_diagnostics(ROOT/p).read_bytes()).hexdigest(),h,p)
  for p,(a,b) in changes.items():
   before=(E/((ROOT/p).stem+'修改前.txt')).read_text('utf-8-sig');after=before_signin(before_diagnostics(ROOT/p)).read_text('utf-8-sig');self.assertEqual(after,before.replace(a,b,1))
if __name__=='__main__':unittest.main()
