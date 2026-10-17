import unittest
from mq_subset import load
import test_universe


class UniverseStartupLogging(unittest.TestCase):
    def test_second_save_task_with_strict_boolean_logging(self):
        for capsule in (False, True):
            with self.subTest(capsule=capsule):
                fixture = test_universe.UniverseTests(); fixture.setUp()
                env = fixture.e
                load(['common/任务状态.mq'], env)
                def strict_concat(*args):
                    if any(isinstance(x, bool) or x is None for x in args):
                        raise TypeError('implicit boolean/null concatenation rejected')
                    return ''.join(str(x) for x in args)
                env['mqcat'] = strict_concat
                env['StartGatherTask'] = lambda: None
                env['SaveCurrentTask'](78)
                env['universeCapsule'] = capsule
                env['SaveCurrentTask'](79)
                self.assertEqual(env['currentTask'], 79)
                self.assertEqual(env['resumeTask'], 79)
                self.assertFalse(env['terminalConfirmed'])
                self.assertEqual(env['universeCapsule'], capsule)
                self.assertTrue(any('已完成任务79初始化' in s for s in fixture.f.logs))
                self.assertTrue(any('胶囊任务=' in s for s in fixture.f.logs))

    def hall_fixture(self, interrupted=False, timeout=False):
        env = {'stageName':'异时空冒险入口','RESULT_TIMEOUT':4,'RESULT_OK':1,
               'TickCount':lambda:100 if timeout else 0,'businessLimit':0 if timeout else 120000,
               'ForegroundInterrupted':lambda:interrupted,'ResetHallCheck':lambda:None,
               'ResetHallClearing':lambda:None,'ConfirmHall':lambda:True,
               'ClearHallObstacle':lambda:False,'Delay':lambda ms:None,'Note':lambda s:None}
        env['SetStage'] = lambda s: env.update(stageName=s)
        load(['common/返回大厅.mq'], env)
        return env

    def test_hall_success_restores_caller_stage(self):
        env=self.hall_fixture()
        self.assertEqual(env['ReturnToHall'](),1)
        self.assertEqual(env['stageName'],'异时空冒险入口')

    def test_hall_interruption_restores_caller_stage(self):
        env=self.hall_fixture(interrupted=True)
        self.assertEqual(env['ReturnToHall'](),4)
        self.assertEqual(env['stageName'],'异时空冒险入口')

    def test_hall_timeout_restores_caller_stage(self):
        env=self.hall_fixture(timeout=True)
        self.assertEqual(env['ReturnToHall'](),4)
        self.assertEqual(env['stageName'],'异时空冒险入口')
