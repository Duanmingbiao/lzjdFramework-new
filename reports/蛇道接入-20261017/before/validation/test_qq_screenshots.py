from historical_source import before_foreground
"""Supplied screenshots replay + actual MQ control flow. No live QQ automation."""
from pathlib import Path
import hashlib
import json
import unittest
import numpy as np
from PIL import Image
from mq_subset import ROOT, load

EVIDENCE = ROOT/'common/evidence/QQ授权适配'
RECORDS = json.loads((EVIDENCE/'截图图色参数.json').read_text('utf-8'))
IMAGES = [np.asarray(Image.open(EVIDENCE/r['screenshot']).convert('RGB'),dtype=np.int16) for r in RECORDS]

def match_pixels(image, definition):
    """BGR, explicit per-channel tolerance, similarity1 only. Not engine emulation."""
    x1,y1,x2,y2,main,offsets,mode,similarity = definition
    assert similarity == 1 and mode == 0
    yy,xx = np.mgrid[y1:y2+1,x1:x2+1]
    valid = np.ones(xx.shape,dtype=bool)
    points = [(0,0,main)]+[(int(x),int(y),c) for x,y,c in (t.split('|',2) for t in offsets.split(','))]
    for dx,dy,token in points:
        value,tolerance = token.split('-')
        rgb = np.array([int(value[i:i+2],16) for i in [4,2,0]])
        bias = np.array([int(tolerance[i:i+2],16) for i in [4,2,0]])
        px,py=xx+dx,yy+dy
        inside=(px>=0)&(px<720)&(py>=0)&(py<1280)
        valid &= inside & np.all(np.abs(image[np.clip(py,0,1279),np.clip(px,0,719)]-rgb)<=bias,axis=2)
    ys,xs=np.where(valid)
    return [(int(x+x1),int(y+y1)) for x,y in zip(xs,ys)]

class QQScreenshotPixels(unittest.TestCase):
    def test_each_new_pattern_matches_own_screenshot_only(self):
        for row,record in enumerate(RECORDS):
            for column,image in enumerate(IMAGES):
                with self.subTest(pattern=record['name'],image=column+1):
                    self.assertEqual(bool(match_pixels(image,record['definition'])),row==column)

    def test_all_candidate_clicks_are_inside_the_blue_button(self):
        for record,image in zip(RECORDS,IMAGES):
            for x,y in match_pixels(image,record['definition']):
                x+=record['clickOffset'][0];y+=record['clickOffset'][1]
                self.assertLessEqual(abs(x-record['expectedClick'][0]),12)
                self.assertLessEqual(abs(y-record['expectedClick'][1]),12)
                # The center can land on the white label; adjoining button interior must be blue.
                self.assertTrue(np.array_equal(image[y,250],[0,153,255]))
                self.assertTrue(960<=y<=1072 and 209<=x<=511)

    def test_blank_page_does_not_match_any_template(self):
        blank=np.full((1280,720,3),255,dtype=np.int16)
        for record in RECORDS:self.assertFalse(match_pixels(blank,record['definition']))

    def test_blue_button_without_matching_page_heading_is_rejected(self):
        for record,image in zip(RECORDS,IMAGES):
            modified=image.copy();modified[:900]=255
            self.assertFalse(match_pixels(modified,record['definition']))

    def test_title_without_blue_button_is_rejected(self):
        for record,image in zip(RECORDS,IMAGES):
            modified=image.copy();modified[940:1160]=255
            self.assertFalse(match_pixels(modified,record['definition']))

    def test_prior_professional_and_hall_profile_records_unchanged(self):
        before=json.loads((EVIDENCE/'修改前基线.json').read_text('utf-8'))
        current=[r for r in json.loads((ROOT/'evidence/图色参数.json').read_text('utf-8')) if r['name'] not in ['游戏协议弹窗','首次启动协议'] and not r['name'].startswith(('154_','153_','081_','080_','082_','079_','078_','169_','167_','166_','055_','056_','050_','151_','152_','070_','032_','强敌_','083_','084_','085_'))]
        self.assertEqual(current[:-3],before['existingProfileData'])
        self.assertEqual([r['name'] for r in current[-3:]],[r['name'] for r in RECORDS])

    def test_only_authorized_qq_mq_files_changed(self):
        before=json.loads((EVIDENCE/'修改前基线.json').read_text('utf-8'))
        allowed={str(Path(p)) for p in ['app/入口.mq','common/任务状态.mq','common/图色参数.mq','flows/001_游戏重连/QQ登录.mq','flows/001_游戏重连/登录游戏.mq']}
        allowed.update(str(Path(x)) for x in ['app/入口.mq', 'common/配置读取.mq', 'common/任务状态.mq', 'common/任务注册.mq', 'common/任务分派.mq', 'common/图色参数.mq'])
        for name,digest in before['mqFiles'].items():
            if name not in allowed:
                with self.subTest(file=name):self.assertEqual(hashlib.sha256(before_foreground(ROOT/name).read_bytes()).hexdigest(),digest)
        for name,digest in before['mailFiles'].items():self.assertEqual(hashlib.sha256(before_foreground(ROOT/name).read_bytes()).hexdigest(),digest)

class QQAuthorizationFlow(unittest.TestCase):
    def setUp(self):
        self.now=1000;self.logs=[];self.clicks=[];self.page=0;self.package='qq';self.lookups=[]
        fixture=self
        class Api:
            def GetFront(self):return fixture.package
        self.env={'TickCount':lambda:self.now,'Delay':lambda ms:setattr(self,'now',self.now+ms),'Note':self.logs.append,'MatchPattern':self.match,'TouchPoint':self.touch,'Sys':Api()}
        load(['common/任务状态.mq','common/运行计时.mq','flows/001_游戏重连/QQ登录.mq'],self.env)
        self.env.update(GAME_PACKAGE='game',QQ_PACKAGE='qq',loginLimit=10000)
        self.env['NewSession']();self.env['loginStarted']=self.now

    def match(self,name):
        self.lookups.append(name)
        record=next((r for r in RECORDS if r['name']==name),None)
        hits=match_pixels(IMAGES[self.page],record['definition']) if record and self.page<3 else []
        self.env['foundX'],self.env['foundY']=hits[0] if hits else (-1,-1)
        return bool(hits)

    def touch(self,x,y,wait):
        self.clicks.append((self.page,x,y,wait));self.now+=wait;self.page+=1

    def test_three_authorization_screens_click_in_order_with_no_setting_toggles(self):
        self.assertTrue(self.env['HandleQQ']())
        self.assertEqual([c[0] for c in self.clicks],[0,1,2])
        for page,x,y,wait in self.clicks:
            self.assertTrue(348<=x<=372 and 960<=y<=1072)
            self.assertEqual(wait,1000)
            self.assertFalse(y in [492,632,1095])
        self.assertEqual(self.env['loginStarted'],1000)
        self.assertTrue(any('头像昵称同意' in line for line in self.logs))
        self.assertTrue(any('VIP会员确认' in line for line in self.logs))
        self.assertTrue(any('游戏信息同意' in line for line in self.logs))

    def test_authorization_screen_does_not_depend_on_foreground_query(self):
        class UnavailableFrontApi:
            def GetFront(self):raise AssertionError('root.793 authorization must not require this API')
        self.env['Sys']=UnavailableFrontApi()
        self.assertTrue(self.env['HandleQQ']())
        self.assertEqual([c[0] for c in self.clicks],[0,1,2])

    def test_unknown_screen_still_cannot_click(self):
        self.package='unrelated.app';self.page=3
        self.assertFalse(self.env['HandleQQ']());self.assertEqual(self.clicks,[])
        self.assertTrue(any('未命中授权页面' in line for line in self.logs))

    def test_expired_login_prevents_any_click(self):
        self.now=11000
        self.assertFalse(self.env['HandleQQ']());self.assertEqual(self.clicks,[])

    def test_unknown_page_logs_are_throttled_without_timer_reset(self):
        self.page=3
        self.assertFalse(self.env['HandleQQ']());count=len(self.logs)
        self.assertGreaterEqual(count,2)
        self.env['HandleQQ']();self.assertEqual(len(self.logs),count)
        self.now+=5000;self.env['HandleQQ']();self.assertGreater(len(self.logs),count)
        self.assertEqual(self.env['loginStarted'],1000);self.assertEqual(self.clicks,[])

    def test_confirmation_original_second_candidate_is_retained(self):
        seen=[]
        def click(name,label,dx,dy):seen.append((name,label));return name=='QQ授权登录二'
        self.env['ClickQQAuthorization']=click
        self.assertTrue(self.env['HandleQQ']())
        self.assertIn(('QQ授权登录二','VIP会员确认候选二'),seen)

    def test_timed_out_mid_sequence_does_not_click_third_screen(self):
        self.env['loginLimit']=1500
        self.env['HandleQQ']()
        self.assertEqual(len(self.clicks),2)
        self.assertEqual(self.env['loginStarted'],1000)

class QQProfessionalOrder(unittest.TestCase):
    def test_one_click_is_checked_before_authorization_groups(self):
        env={};events=[];now=[1000]
        load(['common/任务状态.mq','common/运行计时.mq','flows/001_游戏重连/QQ登录.mq'],env)
        env.update(TickCount=lambda:now[0],Note=lambda message:None,loginLimit=20000)
        env['NewSession']();env['loginStarted']=1000
        def pattern(name):
            events.append(('match',name));env['foundX']=400;env['foundY']=700
            return name=='QQ一键登录'
        def touch(x,y,wait):events.append(('tap',x,y,wait));now[0]+=wait
        env.update(MatchPattern=pattern,TouchPoint=touch,Delay=lambda ms:now.__setitem__(0,now[0]+ms))
        def group(name,label,dx,dy):events.append(('group',name));return False
        env['ClickQQAuthorization']=group
        self.assertTrue(env['HandleQQ']())
        self.assertEqual(events[:4],[('match','QQ一键登录'),('tap',249,786,1000),('tap',463,700,1000),('group','QQ授权登录一')])
        self.assertEqual(now[0],3050)
        self.assertEqual(env['loginStarted'],1000)

    def test_r3_only_changes_authorization_mq(self):
        before=json.loads((EVIDENCE/'R3修改前基线.json').read_text('utf-8'))
        for name,digest in before.items():
            if Path(name) in {Path('app/入口.mq'),Path('common/配置读取.mq'),Path('common/任务状态.mq'),Path('common/任务注册.mq'),Path('common/任务分派.mq'),Path('common/图色参数.mq')}:continue
            if Path(name) in [Path('flows/001_游戏重连/QQ登录.mq'),Path('flows/001_游戏重连/登录游戏.mq'),Path('common/图色参数.mq')]:continue
            self.assertEqual(hashlib.sha256(before_foreground(ROOT/name).read_bytes()).hexdigest(),digest,name)

if __name__=='__main__':unittest.main()
