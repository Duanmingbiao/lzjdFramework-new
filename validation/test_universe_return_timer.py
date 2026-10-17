import unittest
import test_universe
import test_frieza
import test_duel
from mq_subset import load

class UniverseReturnTimer(unittest.TestCase):
    def fixture(self):
        f=test_universe.UniverseTests();f.setUp()
        load(['common/运行计时.mq'],f.e)
        f.e.update(businessStarted=0,businessLimit=120000,ForegroundInterrupted=lambda:f.f.interrupt)
        return f

    def test_original_reset_can_cross_old_total_budget(self):
        f=self.fixture();f.f.now=119000
        self.assertTrue(f.e['ResetUniverseTaskTimer']())
        f.f.now=125000;f.f.visible={'079_返回界面一'}
        self.assertEqual(f.e['ReturnUniversePage'](False),1)
        self.assertFalse(f.e['terminalConfirmed'])

    def test_exact_limit_and_late_progress(self):
        f=self.fixture();f.f.now=120000
        self.assertFalse(f.e['BusinessExpired']())
        f.f.now=120001
        self.assertTrue(f.e['BusinessExpired']())
        self.assertFalse(f.e['ResetUniverseTaskTimer']())
        self.assertEqual(f.e['businessStarted'],0)

    def test_unknown_return_does_not_refresh_or_commit(self):
        f=self.fixture();f.e['businessLimit']=6000
        self.assertEqual(f.e['ReturnUniversePage'](False),4)
        self.assertEqual(f.e['businessStarted'],0)
        self.assertFalse(f.e['terminalConfirmed'])
        self.assertFalse(f.f.taps)
        self.assertTrue(any('返回界面尚未命中' in s for s in f.f.logs))

    def test_foreground_interruption_cannot_reset(self):
        f=self.fixture();f.f.now=100;f.f.interrupt=True
        self.assertFalse(f.e['ResetUniverseTaskTimer']())
        self.assertEqual(f.e['businessStarted'],0)

    def test_four_stage_reset_points_and_no_implicit_completion(self):
        f=self.fixture();events=[]
        def phase(name,result=1):
            def call(*args):events.append(name);f.f.now+=10;return result
            return call
        original=f.e['ResetUniverseTaskTimer']
        def reset():events.append('reset');return original()
        f.e.update(EnterGatherHall=phase('hall'),EnterUniverse=phase('entry'),
                   RunUniverse=phase('map'),ReturnUniversePage=lambda final:events.append('final' if final else 'return') or 1,
                   RunUniverseCapsule=phase('capsule'),ResetUniverseTaskTimer=reset,universeCapsule=True)
        self.assertEqual(f.e['ExecuteUniverse'](),1)
        self.assertEqual(events,['hall','entry','reset','map','reset','return','reset','capsule','reset','final'])
        self.assertEqual(f.e['universeCount'],0)

    def test_quick_challenge_resets_before_original_200ms_wait(self):
        f=self.fixture();f.f.visible={'079_胶囊快速挑战'};events=[]
        old=f.e['ResetUniverseTaskTimer'];wait=f.e['WorldWait']
        f.e['ResetUniverseTaskTimer']=lambda:events.append('reset') or old()
        def delay(ms):
            events.append(ms);wait(ms)
            if ms==200:f.f.interrupt=True
        f.e['WorldWait']=delay
        self.assertEqual(f.e['RunUniverseCapsule'](),4)
        self.assertIn(['reset',200],[events[i:i+2] for i in range(len(events)-1)])
        self.assertEqual(f.f.taps,[(450,950,0)])

    def test_other_tasks_keep_original_total_boundary(self):
        f=self.fixture();f.e['currentTask']=78;f.f.now=120000
        self.assertTrue(f.e['BusinessExpired']())

    def test_80_81_start_and_recovery_strict_boolean_concat(self):
        for module,task in ((test_frieza,80),(test_duel,81)):
            cls=module.FriezaTests if task==80 else module.DuelTests
            f=cls();f.setUp();env=f.e
            def concat(*args):
                if any(isinstance(x,bool) or x is None for x in args):raise TypeError('implicit boolean/null log')
                return ''.join(str(x) for x in args)
            env['mqcat']=concat
            prefix='Frieza' if task==80 else 'Duel'
            key='frieza' if task==80 else 'duel'
            for value in (False,True):
                env[key+'RestartOnTimeout']=value
                env['Start'+prefix+'Task']()
                env[key+'Abandoned']=value
                env['Recover'+prefix+'Task']()
