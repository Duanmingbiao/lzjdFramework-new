import re
import unittest
from pathlib import Path
from PIL import Image
import test_nameless

ROOT = Path(__file__).resolve().parents[1]


class NamelessColorFallbackTests(unittest.TestCase):
    def fixture(self, hit=True):
        e, clock, calls, logs, probes = test_nameless.NamelessTests().fixture()
        e['WorldMatch'] = lambda n: n == '020_报名界面一'
        e['ReleaseCapture'] = lambda: None
        def find(*args):
            calls.append(('find', args))
            e['foundX'], e['foundY'] = (335, 1120) if hit else (-1, -1)
        e['FindMultiColor'] = find
        return e, clock, calls, logs

    def test_first_unknown_starts_timer_and_exact_30_seconds_enables(self):
        e, t, calls, logs = self.fixture()
        e['NamelessRegistration'](False)
        t[0] = 29999
        e['NamelessRegistration'](True)
        self.assertFalse(calls)
        t[0] = 30000
        self.assertEqual(e['NamelessRegistration'](False), 2)
        self.assertEqual(calls[-1], ('tap', 360, 1140, 1000))
        args = calls[0][1]
        self.assertEqual(args[:4], (301, 1108, 417, 1158))
        self.assertEqual(args[6:8], (1, 1.0))
        self.assertEqual(e['businessStarted'], 0)
        self.assertFalse(e['terminalConfirmed'])
        self.assertFalse(e['namelessDone'])
        self.assertFalse(e['namelessBattleOcrWaiting'])

    def test_expired_or_unrecognized_page_never_taps(self):
        for expired in (False, True):
            e, t, calls, logs = self.fixture()
            e['NamelessRegistration'](False)
            t[0] = 120001 if expired else 30000
            e['WorldMatch'] = lambda n: False
            self.assertEqual(e['NamelessRegistration'](False), 4 if expired else 2)
            self.assertFalse(calls)

    def test_no_color_match_or_wrong_anchor_never_taps(self):
        e, t, calls, logs = self.fixture(False)
        e['NamelessRegistration'](False)
        t[0] = 30000
        e['NamelessRegistration'](False)
        self.assertEqual([x[0] for x in calls], ['find'])
        e['FindMultiColor'] = lambda *args: e.update(foundX=340, foundY=1120)
        e['NamelessRegistration'](False)
        self.assertFalse(any(x[0] == 'tap' for x in calls))

    def test_exact_original_texts_keep_priority_and_reset_timer(self):
        for text in ['报名', '已报名', '未报名', '战斗']:
            e, t, calls, logs = self.fixture()
            e.update(namelessBattleOcrWaiting=True, namelessBattleOcrWaitAt=0)
            t[0] = 40000
            e['WorldText'] = lambda *args: text
            e['NamelessRegistration'](True)
            self.assertFalse(any(x[0] == 'find' for x in calls))
            self.assertFalse(e['namelessBattleOcrWaiting'])

    def test_interruption_during_native_match_never_taps(self):
        e, t, calls, logs = self.fixture()
        e['NamelessRegistration'](False)
        t[0] = 30000
        def interrupted(*args):
            e.update(foundX=335, foundY=1120)
            t[0] = 120001
        e['FindMultiColor'] = interrupted
        self.assertEqual(e['NamelessRegistration'](False), 4)
        self.assertFalse(calls)

    def test_recovery_start_resets_wait_and_does_not_extend_business_timer(self):
        e, t, calls, logs = self.fixture()
        e.update(namelessBattleOcrWaiting=True, namelessBattleOcrWaitAt=0)
        e['StartNamelessTask']()
        self.assertFalse(e['namelessBattleOcrWaiting'])
        self.assertEqual(e['businessStarted'], 0)

    def test_real_saved_pixels_positive_and_overlay_negative(self):
        source=(ROOT/'flows/020_无名星之战/无名星之战.mq').read_text('utf-8-sig')
        m=re.search(r'FindMultiColor 301,1108,417,1158,"([^"]+)","([^"]+)"',source)
        points=[(0,0,m[1])]+[(int(x),int(y),color) for x,y,color in (p.split('|') for p in m[2].split(','))]
        def matches(path):
            im=Image.open(path).convert('RGB')
            for ax in range(333,338):
                for ay in range(1118,1123):
                    ok=True
                    for dx,dy,c in points:
                        bgr,tol=c.split('-');rgb=tuple(bytes.fromhex(bgr)[::-1]);limits=tuple(bytes.fromhex(tol)[::-1])
                        if any(abs(a-b)>limit for a,b,limit in zip(im.getpixel((ax+dx,ay+dy)),rgb,limits)):
                            ok=False;break
                    if ok:return True
            return False
        shared=Path(r'C:\Users\31027\Documents\leidian9\Pictures')
        for name in ['dragonball-nameless-ocr-empty-46507-1.png','dragonball-nameless-ocr-empty-158618-12.png']:
            self.assertTrue(matches(shared/name),name)
        self.assertFalse(matches(shared/'dragonball-nameless-ocr-empty-181156-14.png'))
        self.assertFalse(matches(ROOT/'reports/OCR资源补齐-20261017/补齐后当前画面.png'))


if __name__ == '__main__':
    unittest.main()
