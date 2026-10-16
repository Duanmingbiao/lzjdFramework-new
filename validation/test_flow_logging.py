from historical_source import before_signin
import unittest,json,re,hashlib
from mq_subset import ROOT
import test_foreground
class FlowLogging(unittest.TestCase):
 def test_only_diagnostic_calls_added(self):
  base=json.loads((ROOT/'common/evidence/流程日志/修改前基线.json').read_text('utf-8'))
  for rel,digest in base.items():
   data=before_signin(ROOT/rel).read_bytes()
   stripped=b''.join(line for line in data.splitlines(keepends=True) if 'Call Note("[流程]'.encode('utf-8') not in line)
   self.assertEqual(hashlib.sha256(stripped).hexdigest(),digest,rel)
 def test_tap_and_skipped_tap_have_distinct_logs(self):
  f=test_foreground.Foreground();f.setUp();logs=[];f.e['Note']=logs.append
  f.front='com.tencent.mobileqq:openSdk';f.e['TouchPoint'](351,999,1000)
  self.assertTrue(any('已发送点击' in x for x in logs));self.assertTrue(any('出口 TouchPoint' in x for x in logs))
  logs.clear();f.front='other';f.e['TouchPoint'](351,999,1000)
  self.assertFalse(any('已发送点击' in x for x in logs));self.assertTrue(any('出口 TouchPoint' in x for x in logs))
 def test_every_finite_operation_exit_has_log(self):
  names={'StartGame','RestartGame','SaveCurrentTask','SaveRecovery','CommitTask','DispatchTask','EnsureGameHall','ReturnToHall','ReadMessages','ExecuteMail','EnterTaskRewards','RewardFirstPass','RewardFourPositions','RewardFinalPass','ExecuteTaskRewards','TouchPoint'}
  for p in list((ROOT/'common').glob('*.mq'))+list((ROOT/'flows').glob('*/*.mq')):
   current=None;previous=''
   for line in p.read_text('utf-8-sig').splitlines():
    s=line.strip();m=re.match(r'(?:Function|Sub) (\w+)\(',s)
    if m:current=m[1]
    if current in names and s in ('Exit Function','Exit Sub','End Function','End Sub'):self.assertIn('[流程] 出口 '+current,previous)
    previous=s
