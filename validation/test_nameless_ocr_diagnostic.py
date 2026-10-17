import unittest
from types import SimpleNamespace
import test_nameless
from mq_subset import load


class OcrDiagnosticTests(unittest.TestCase):
    def fixture(self):
        env, clock, calls, logs, _ = test_nameless.NamelessTests().fixture()
        shots = []
        env.update(IsNull=lambda x: x is None,
                   Dir=SimpleNamespace(Exist=lambda p: True, Create=lambda p: True),
                   File=SimpleNamespace(Bytes=lambda p: 123), SnapShot=shots.append)
        return env, clock, calls, logs, shots

    def test_null_empty_rate_limit_and_no_business_mutation(self):
        e, clock, calls, logs, shots = self.fixture()
        e['NamelessOcrEmptyDiagnostic'](None)
        self.assertIn('原始返回类型=null IsNull=true 原始返回内容=[<null>]', logs[0])
        e['NamelessOcrEmptyDiagnostic']('')
        clock[0] = 9999
        e['NamelessOcrEmptyDiagnostic']('')
        self.assertEqual(len(shots), 1)
        clock[0] = 10000
        e['NamelessOcrEmptyDiagnostic']('')
        self.assertEqual(len(shots), 2)
        self.assertTrue(any('原始返回类型=string IsNull=false 原始返回内容=[]' in x for x in logs))
        self.assertEqual((e['businessStarted'], e['foundX'], e['foundY']), (0, 100, 200))
        self.assertFalse(calls)
        self.assertFalse(e['terminalConfirmed'])

    def test_nonempty_and_expired_do_not_capture(self):
        e, clock, calls, logs, shots = self.fixture()
        for raw in ['报名', '战斗', ' 报名', '报名\n', '未知']:
            e['NamelessOcrEmptyDiagnostic'](raw)
        clock[0] = 120001
        e['NamelessOcrEmptyDiagnostic'](None)
        self.assertFalse(shots)
        self.assertFalse(logs)

    def test_single_original_call_raw_before_normalization_scoped_to_task_roi(self):
        e, clock, calls, logs, shots = self.fixture()
        reads = []
        e.update(ReleaseCapture=lambda: None, worldLastOcr='',
                 Image=SimpleNamespace(OcrText=lambda *a: reads.append(a)))
        load(['common/强敌入口.mq'], e)
        self.assertEqual(e['WorldText'](301, 1108, 417, 1158), '')
        self.assertEqual(reads, [(301, 1108, 417, 1158, 0, 0)])
        self.assertEqual(len(shots), 1)
        clock[0] = 10000
        e['currentTask'] = 21
        e['WorldText'](301, 1108, 417, 1158)
        e['currentTask'] = 20
        e['WorldText'](100, 395, 317, 448)
        self.assertEqual(len(shots), 1)

    def test_failed_snapshot_not_retried(self):
        e, clock, calls, logs, shots = self.fixture()
        e['Dir'].Exist = lambda p: False
        e['NamelessOcrEmptyDiagnostic']('')
        e['NamelessOcrEmptyDiagnostic']('')
        self.assertEqual(len(shots), 1)
        self.assertTrue(any('截图未确认写入' in x for x in logs))


if __name__ == '__main__':
    unittest.main()
