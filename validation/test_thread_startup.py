from historical_source import before_diagnostics
import unittest,json,hashlib
from mq_subset import ROOT,load
from test_foreground import Shared
class Startup(unittest.TestCase):
 def test_worker_entry_first_sample_and_ready_before_loop(self):
  shared=Shared();shared.data={'fg.ready':False};events=[]
  e={'Thread':shared,'WriteForegroundLog':lambda s:events.append(s)}
  load(['common/前台监控.mq'],e)
  e['SampleForeground']=lambda g,q:events.append((g,q,shared.data['fg.ready']))
  def stop(ms):raise StopIteration
  e['Delay']=stop
  with self.assertRaises(StopIteration):e['ForegroundMonitor']()
  self.assertIn('已进入监控线程',events[0]);self.assertEqual(events[1],('com.tencent.tmgp.dragonball','com.tencent.mobileqq',False))
  self.assertEqual(events[3],('com.tencent.tmgp.dragonball','com.tencent.mobileqq',True))
 def test_startup_has_checkpoints_and_does_not_print_userdata(self):
  s=(ROOT/'app/入口.mq').read_text('utf-8-sig')
  self.assertIn('Thread.Start(ForegroundMonitor)',s)
  self.assertLess(s.index('准备调用Thread.Start'),s.index('foregroundThread = Thread.Start'))
  self.assertLess(s.index('Thread.Start已返回'),s.index('首次采样已确认'))
  self.assertLess(s.index('首次采样已确认'),s.index('Call SchedulerStep()'))
  self.assertNotIn('& foregroundThread',s)
 def test_only_startup_and_monitor_changed(self):
  base=json.loads((ROOT/'common/evidence/线程启动排查/修改前基线.json').read_text('utf-8'))
  for p,h in base.items():
   if p not in ['app/入口.mq','common/前台监控.mq','common/游戏控制.mq','common/点击操作.mq']:self.assertEqual(hashlib.sha256(before_diagnostics(ROOT/p).read_bytes()).hexdigest(),h,p)
if __name__=='__main__':unittest.main()
