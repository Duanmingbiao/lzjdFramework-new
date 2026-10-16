from historical_source import before_diagnostics
import unittest,threading,time,json,hashlib
from mq_subset import load,ROOT
class Store:
 def __init__(self):self.data={};self.guard=threading.Lock()
 def SetShareVar(self,k,v):
  with self.guard:self.data[k]=v
  time.sleep(0.00001)
 def GetShareVar(self,k):
  with self.guard:v=self.data[k]
  time.sleep(0.00001);return v
 def Lock(self):raise AssertionError('Android must not call native lock')
 def Release(self):raise AssertionError('Android must not call native release')
class AndroidGate(unittest.TestCase):
 def setUp(self):
  self.store=Store();self.main={'Thread':self.store,'Delay':lambda ms:time.sleep(ms/1000)};self.monitor=dict(self.main)
  load(['common/前台监控.mq'],self.main);load(['common/前台监控.mq'],self.monitor);self.main['InitForegroundMonitor']()
 def test_two_threads_exclude_each_other_under_contention(self):
  barrier=threading.Barrier(2);inside=[0];violations=[];counts=[0,0]
  def worker(env,enter,leave,index):
   barrier.wait()
   for _ in range(60):
    env[enter]()
    try:
     inside[0]+=1
     if inside[0]!=1:violations.append(inside[0])
     time.sleep(0.0001);counts[index]+=1;inside[0]-=1
    finally:env[leave]()
  threads=[threading.Thread(target=worker,args=(self.main,'EnterMainForegroundGate','LeaveMainForegroundGate',0),daemon=True),threading.Thread(target=worker,args=(self.monitor,'EnterMonitorForegroundGate','LeaveMonitorForegroundGate',1),daemon=True)]
  for t in threads:t.start()
  for t in threads:t.join(5)
  self.assertTrue(all(not t.is_alive() for t in threads),'gate deadlock');self.assertEqual(violations,[]);self.assertEqual(counts,[60,60])
 def test_report_blocks_commit_and_releases_main_intent(self):
  self.store.SetShareVar('fg.request',True);self.assertFalse(self.main['BeginForegroundCommit']());self.assertFalse(self.store.GetShareVar('fg.gate.main'))
 def test_commit_blocks_monitor_until_completion(self):
  self.assertTrue(self.main['BeginForegroundCommit']());entered=threading.Event()
  def monitor():
   self.monitor['EnterMonitorForegroundGate']();entered.set();self.monitor['LeaveMonitorForegroundGate']()
  t=threading.Thread(target=monitor,daemon=True);t.start();self.assertFalse(entered.wait(0.03))
  self.main['EndForegroundCommit']();t.join(2);self.assertTrue(entered.is_set());self.assertFalse(t.is_alive())
 def test_recovery_updates_and_releases_gate(self):
  self.store.SetShareVar('fg.request',True);self.main['BeginForegroundRecovery']()
  self.assertFalse(self.store.GetShareVar('fg.request'));self.assertTrue(self.store.GetShareVar('fg.recovering'));self.assertFalse(self.store.GetShareVar('fg.gate.main'))
  self.main['EndForegroundRecovery']();self.assertFalse(self.store.GetShareVar('fg.recovering'))
 def test_only_public_gate_module_changed_and_no_native_locks(self):
  base=json.loads((ROOT/'common/evidence/安卓线程互斥/修改前基线.json').read_text('utf-8'))
  for p,h in base.items():
   if p not in ['common/前台监控.mq','common/游戏控制.mq','common/点击操作.mq']:self.assertEqual(hashlib.sha256(before_diagnostics(ROOT/p).read_bytes()).hexdigest(),h,p)
   text=(ROOT/p).read_text('utf-8-sig');self.assertNotIn('Thread.Lock(',text);self.assertNotIn('Thread.Release(',text)
if __name__=='__main__':unittest.main()
