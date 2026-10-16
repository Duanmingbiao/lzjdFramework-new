"""Actual public MQ control flow with mocked recognition/time. Not an MQ compiler or live test."""
import hashlib
from pathlib import Path
import json
import unittest
from mq_subset import ROOT, load

class HallClearing(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.front = True
        self.patterns = set()
        self.lookups = []
        self.clicks = []
        self.logs = []
        self.after_touch = None
        fixture = self

        class GameApi:
            def AppIsFront(self, package):
                return fixture.front and package == 'game'

        self.env = {
            'TickCount': lambda: self.now,
            'Delay': self.delay,
            'Note': self.logs.append,
            'SetStage': lambda name: None,
            'Sys': GameApi(),
            'MatchPattern': self.match,
            'TouchPoint': self.touch,
        }
        load([
            'common/任务状态.mq',
            'common/运行计时.mq',
            'common/大厅清障.mq',
            'common/页面识别.mq',
            'common/返回大厅.mq',
            'flows/001_游戏重连/登录游戏.mq',
        ], self.env)
        self.env.update(
            GAME_PACKAGE='game', QQ_PACKAGE='qq', RESULT_OK=1, RESULT_WAIT=2,
            RESULT_FAIL=3, RESULT_TIMEOUT=4, businessLimit=20000,
            loginLimit=20000, hallReturnDelaySeconds=0,
            StartGame=lambda: None, HandleQQ=lambda: False,
            TouchPattern=lambda name, delay: False,
        )
        self.env['NewSession']()

    def delay(self, milliseconds):
        self.now += milliseconds

    def match(self, name):
        self.lookups.append(name)
        # Even failed lookups clobber native output coordinates.
        if name == '大厅清障特殊分支':
            self.env['foundX'], self.env['foundY'] = 650, 100
        else:
            self.env['foundX'], self.env['foundY'] = 460, 600
        return name in self.patterns

    def touch(self, x, y, milliseconds):
        self.clicks.append((x, y, milliseconds))
        self.now += milliseconds
        if self.after_touch:
            self.after_touch()

    def test_all_17_candidate_slots_select_and_click(self):
        for index in range(1, 18):
            with self.subTest(index=index):
                self.env['ResetHallClearing']()
                self.env['hallExtended'] = index > 6
                self.patterns = {f'大厅清障{index:02d}'}
                self.clicks.clear()
                self.assertTrue(self.env['ClearHallObstacle']())
                self.assertEqual(self.clicks, [(460, 600, 1000)])
                self.assertIn(f'候选={index}，', self.logs[-1])

    def test_candidate_order_stops_at_first_match(self):
        self.patterns = {'大厅清障02', '大厅清障05', '大厅清障17'}
        self.env['hallExtended'] = True
        self.assertTrue(self.env['ClearHallObstacle']())
        self.assertEqual(self.lookups, ['大厅清障01', '大厅清障02', '大厅清障特殊分支'])

    def test_three_duplicate_entries_are_preserved(self):
        self.patterns = {'大厅清障05'}
        self.env['ClearHallObstacle']()
        self.assertEqual(self.lookups[:5], [f'大厅清障{i:02d}' for i in range(1, 6)])
        data = json.loads((ROOT/'common/evidence/大厅清障/原始图色.json').read_text('utf-8'))
        self.assertEqual(data['candidates'][1]['definition'], data['candidates'][2]['definition'])
        self.assertEqual(data['candidates'][2]['definition'], data['candidates'][3]['definition'])

    def test_special_overrides_selected_candidate_without_double_click(self):
        self.patterns = {'大厅清障02', '大厅清障特殊分支'}
        self.assertTrue(self.env['ClearHallObstacle']())
        self.assertEqual(self.clicks, [(339, 110, 1000)])
        self.assertEqual(self.lookups, ['大厅清障01', '大厅清障02', '大厅清障特殊分支'])

    def test_special_without_any_candidate_still_acts(self):
        self.patterns = {'大厅清障特殊分支'}
        self.assertTrue(self.env['ClearHallObstacle']())
        self.assertEqual(self.clicks, [(339, 110, 1000)])

    def test_failed_special_lookup_does_not_lose_saved_candidate_coordinates(self):
        self.patterns = {'大厅清障06'}
        self.env['ClearHallObstacle']()
        self.assertEqual(self.clicks[0][:2], (460, 600))

    def test_extension_starts_after_four_misses_on_fifth_round(self):
        self.patterns = {'大厅清障07'}
        for _ in range(4):
            self.assertFalse(self.env['ClearHallObstacle']())
        self.assertEqual(self.env['hallMisses'], 4)
        self.assertNotIn('大厅清障07', self.lookups)
        self.assertTrue(self.env['ClearHallObstacle']())
        self.assertTrue(self.env['hallExtended'])
        self.assertEqual(self.env['hallMisses'], 0)

    def test_expanded_candidates_survive_later_basic_candidate_match(self):
        self.env['hallMisses'] = 4
        self.patterns = {'大厅清障07'}
        self.env['ClearHallObstacle']()
        self.patterns = {'大厅清障01'}
        self.env['ClearHallObstacle']()
        self.patterns = {'大厅清障17'}
        self.assertTrue(self.env['ClearHallObstacle']())
        self.assertTrue(self.env['hallExtended'])

    def test_new_return_flow_resets_extension(self):
        self.env.update(hallExtended=True, hallMisses=4)
        self.env['ResetHallClearing']()
        self.assertFalse(self.env['hallExtended'])
        self.assertEqual(self.env['hallMisses'], 0)

    def test_return_delay_configuration_changes_only_action_wait(self):
        self.patterns = {'大厅清障02'}
        self.env['hallReturnDelaySeconds'] = 3
        self.env['ClearHallObstacle']()
        self.assertEqual(self.clicks, [(460, 600, 3000)])

    def test_all_clearance_blockers_prevent_hall_success_even_before_extension(self):
        for name in [f'大厅清障{i:02d}' for i in range(1, 18)] + ['大厅清障特殊分支']:
            with self.subTest(name=name):
                self.patterns = {'大厅主体', name}
                self.assertFalse(self.env['HallCandidate']())
                self.assertFalse(self.env['hallExtended'])
                self.assertEqual(self.clicks, [])

    def test_click_resets_continuous_hall_confirmation(self):
        self.env['hallFrames'] = 1
        self.patterns = {'大厅清障02'}
        self.env['ClearHallObstacle']()
        self.assertEqual(self.env['hallFrames'], 0)

    def test_hall_requires_two_consecutive_samples_after_obstacle_disappears(self):
        self.patterns = {'大厅主体'}
        self.assertFalse(self.env['ConfirmHall']())
        self.delay(500)
        self.patterns.add('大厅清障02')
        self.assertFalse(self.env['ConfirmHall']())
        self.assertEqual(self.env['hallFrames'], 0)
        self.patterns.remove('大厅清障02')
        self.delay(500)
        self.assertFalse(self.env['ConfirmHall']())
        self.delay(500)
        self.assertTrue(self.env['ConfirmHall']())

    def test_unknown_page_never_clicks_and_return_times_out(self):
        self.env.update(businessLimit=500, currentTask=168, resumeTask=168, terminalConfirmed=True)
        self.assertEqual(self.env['ReturnToHall'](), 4)
        self.assertEqual(self.now, 1500)
        self.assertEqual(self.clicks, [])
        self.assertEqual(self.env['mailCount'], 0)
        self.assertEqual(self.env['resumeTask'], 168)

    def test_clearing_success_is_not_itself_a_task_completion(self):
        self.patterns = {'大厅清障02'}
        self.env.update(currentTask=168, resumeTask=168, terminalConfirmed=False)
        self.env['ClearHallObstacle']()
        self.assertFalse(self.env['terminalConfirmed'])
        self.assertEqual(self.env['mailCount'], 0)
        self.assertEqual(self.env['resumeTask'], 168)

    def test_return_clears_popup_then_confirms_hall_without_committing(self):
        self.patterns = {'大厅主体', '大厅清障02'}
        self.after_touch = lambda: self.patterns.discard('大厅清障02')
        self.assertEqual(self.env['ReturnToHall'](), 1)
        self.assertEqual(self.clicks, [(460, 600, 1000)])
        self.assertEqual(self.env['hallFrames'], 2)
        self.assertEqual(self.env['mailCount'], 0)
        self.assertEqual(self.now, 2600)  # action1000 + six tail rounds100

    def test_login_uses_same_clearance_without_resetting_login_origin(self):
        self.patterns = {'大厅主体', '大厅清障02'}
        self.after_touch = lambda: self.patterns.discard('大厅清障02')
        started = self.now
        self.assertEqual(self.env['EnsureGameHall'](), 1)
        self.assertEqual(self.env['loginStarted'], started)
        self.assertEqual(self.clicks, [(460, 600, 1000)])

    def test_popup_never_disappears_does_not_refresh_total_login_deadline(self):
        self.patterns = {'大厅清障02'}
        self.env['loginLimit'] = 1500
        started = self.now
        self.assertEqual(self.env['EnsureGameHall'](), 4)
        self.assertEqual(self.env['loginStarted'], started)
        self.assertEqual(len(self.clicks), 2)
        self.assertEqual(self.env['mailCount'], 0)

    def test_qq_front_does_not_run_game_clearance_or_increment_miss_counter(self):
        self.front = False
        self.patterns = {'大厅清障02', '大厅清障特殊分支'}
        self.env['hallMisses'] = 2
        self.assertFalse(self.env['ClearHallObstacle']())
        self.assertEqual(self.clicks, [])
        self.assertEqual(self.lookups, [])
        self.assertEqual(self.env['hallMisses'], 2)

    def test_mail_files_and_evidence_match_pre_edit_hashes(self):
        before = json.loads((ROOT/'common/evidence/大厅清障/修改前基线.json').read_text('utf-8'))
        for name, digest in before['protectedMailFiles'].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest)

    def test_exact_pattern_arguments_match_evidence_including_special_clipping(self):
        records = json.loads((ROOT/'common/evidence/大厅清障/图色转换.json').read_text('utf-8'))
        source = (ROOT/'common/图色参数.mq').read_text('utf-8-sig')
        self.assertEqual(len(records), 18)
        for record in records:
            args = ','.join(json.dumps(v, ensure_ascii=False) for v in record['definition'])
            clause = f'Case "{record["name"]}"\n        // {record["id"]}\n        FindMultiColor {args},foundX,foundY'
            self.assertIn(clause, source)
        self.assertEqual(records[-1]['originalRegion'], [0, 0, 720, 250])
        self.assertEqual(records[-1]['definition'][:4], [0, 0, 719, 250])

    def test_existing_color_cases_are_unchanged(self):
        before = json.loads((ROOT/'common/evidence/大厅清障/修改前基线.json').read_text('utf-8'))
        records = json.loads((ROOT/'common/evidence/大厅清障/图色转换.json').read_text('utf-8'))
        source = (ROOT/'common/图色参数.mq').read_text('utf-8-sig')
        qq_records = json.loads((ROOT/'common/evidence/QQ授权适配/截图图色参数.json').read_text('utf-8'))
        for record in qq_records:
            args = ','.join(json.dumps(v, ensure_ascii=False) for v in record['definition'])
            clause = f'    Case "{record["name"]}"\n        // {record["id"]}; user screenshot adaptation, not original professional data\n        FindMultiColor {args},foundX,foundY\n'
            source = source.replace(clause, '', 1)
        for record in records:
            args = ','.join(json.dumps(v, ensure_ascii=False) for v in record['definition'])
            clause = f'    Case "{record["name"]}"\n        // {record["id"]}\n        FindMultiColor {args},foundX,foundY\n'
            source = source.replace(clause, '', 1)
        restored = source.replace('\n', '\r\n').encode('utf-8-sig')
        self.assertEqual(hashlib.sha256(restored).hexdigest(), before['publicSourceHashes'][str(Path('common/图色参数.mq'))])

    def test_scheduler_registry_dispatch_and_public_clicks_are_unchanged(self):
        before = json.loads((ROOT/'common/evidence/大厅清障/修改前基线.json').read_text('utf-8'))
        for name in ['common/任务调度.mq','common/任务注册.mq','common/任务分派.mq','common/运行计时.mq','common/点击操作.mq']:
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), before['publicSourceHashes'][str(Path(name))])

if __name__ == '__main__':
    unittest.main()
