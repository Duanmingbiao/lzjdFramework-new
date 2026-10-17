"""Actual MQ helper + captured pixels; digit OCR is a declared mock, not native OCR proof."""
import unittest
from PIL import Image
from mq_subset import ROOT,load
import test_gold

E=ROOT/'reports/金币分隔符OCR修复-20261017'
class TrialSeparator(unittest.TestCase):
 def setUp(self):
  self.g=test_gold.GoldTests();self.g.setUp();self.e=self.g.e;self.f=self.g.f
  load(['common/强敌入口.mq'],self.e)
  self.calls=[];self.events=[];self.raw='073';self.left='0';self.right='3'
  self.image=Image.open(E/'金币经验.png').convert('RGB')
  self.roi=(149,835,219,875)
  self.e.update(Int=int,KeepCapture=lambda:self.events.append('keep'),ReleaseCapture=lambda:self.events.append('release'))
  self.e['FindColor']=self.find
  self.e['GetPixelColor']=lambda x,y,t:sum(v<<(8*i) for i,v in enumerate(self.image.getpixel((x,y))))
  self.e['SmartOcr']=self.ocr
 def red(self,x,y):
  r,g,b=self.image.getpixel((x,y));return 217<=r<=249 and 0<=g<=16 and 0<=b<=16
 def find(self,x1,y1,x2,y2,*a):
  self.assertEqual(a[:3],('0000E9-101010',0,1))
  return 0 if any(self.red(x,y) for x in range(x1,x2+1) for y in range(y1,y2+1)) else -1
 def ocr(self,*a):
  self.calls.append(a)
  if a[:4]==self.roi:return self.raw
  return self.left if a[0]<180 else self.right
 def result(self):
  self.f.text='';return self.e['TrialCountText'](*self.roi)
 def test_real_gold_slash_is_excluded_from_both_native_digit_rois(self):
  self.assertEqual(self.result(),'0/3')
  self.assertEqual(self.calls,[(149,835,219,875,'0000E9-101010'),(168,835,176,875,'0000E9-101010'),(188,835,196,875,'0000E9-101010')])
  self.assertEqual(self.events,['release','release','keep','release'])
 def test_prior_capture_gold_original_roi(self):
  self.image=Image.open(ROOT/'reports/金币OCR与试炼公共超时修复-20261017/金币次数原图.png').convert('RGB');self.roi=(149,306,219,346)
  self.assertEqual(self.result(),'0/3')
 def test_full_roi_073_is_not_replaced_by_a_string_rule(self):
  self.left='1';self.assertEqual(self.result(),'1/3');self.assertFalse(self.e['GoldCountExhausted'](self.e['GoldFilterText']('1/3')))
 def test_raw_garbage_is_diagnostic_not_a_count(self):
  for raw in ['',None,'073','65465','03']:
   self.raw=raw;self.left='';self.assertEqual(self.result(),'')
 def test_missing_slash_rejects_even_if_all_ocr_claims_zero(self):
  for y in range(835,876):
   for x in range(177,188):self.image.putpixel((x,y),(255,255,255))
  self.assertEqual(self.result(),'');self.assertEqual(len(self.calls),1)
 def test_digit_seven_is_not_a_slash(self):
  for y in range(835,876):
   for x in range(178,186):self.image.putpixel((x,y),(255,255,255))
  for x in range(179,185):self.image.putpixel((x,844),(233,0,0))
  for y in range(845,858):self.image.putpixel((184-(y-845)//3,y),(233,0,0))
  self.assertEqual(self.result(),'')
 def test_empty_single_digit_bad_denominator_never_exhausted(self):
  for left,right in [('', '3'),(None,'3'),('0',''),('0',None),('0','7'),('0','03'),('00','3'),('x','3'),('8x','3')]:
   self.left=left;self.right=right;self.assertEqual(self.result(),'')
 def test_primary_exhaustion_candidate_cannot_bypass_geometry(self):
  self.image=Image.new('RGB',(720,1280),'white')
  for text in ['03','0/3','0 | 13']:
   self.f.text=text;self.assertEqual(self.e['TrialCountText'](*self.roi),'')
 def test_nonempty_primary_digit_errors_also_go_through_separator(self):
  for text in ['073','65465','0','3']:
   self.f.text=text;self.assertEqual(self.e['TrialCountText'](*self.roi),'0/3')
 def test_primary_cooldown_and_positive_boundary_unchanged(self):
  for text in ['00:10','1/3','错误03']:
   self.f.text=text;self.assertEqual(self.e['TrialCountText'](*self.roi),text)
  self.assertFalse(self.calls)
 def test_digit_eight_misread_zero_is_rejected(self):
  for x in range(168,177):self.image.putpixel((x,851),(233,0,0))
  self.assertEqual(self.result(),'')
 def test_clipped_zero_is_rejected(self):
  for y in [856,857]:
   for x in range(168,177):self.image.putpixel((x,y),(255,255,255))
  self.assertEqual(self.result(),'')
 def test_expiry_before_separator_cannot_return_primary_exhaustion_candidate(self):
  calls=[]
  self.f.text='03';self.e['BusinessExpired']=lambda:calls.append(1) or len(calls)>=3
  self.assertEqual(self.e['TrialCountText'](*self.roi),'')
  self.assertFalse(self.calls)
 def test_real_experience_gene_partner_and_soul_glyph_segmentation(self):
  # Exact all-point professional anchor matches + each original relative ROI.
  for file,roi in [('金币经验.png',(152,1107,212,1147)),('龙魂基因伙伴异时空.png',(156,284,209,310)),('龙魂基因伙伴异时空.png',(150,551,210,591)),('龙魂基因伙伴异时空.png',(150,827,210,867))]:
   self.image=Image.open(E/file).convert('RGB');self.roi=roi;self.right='2'
   self.assertEqual(self.result(),'0/2'),(file,roi)
 def test_foreground_during_digit_ocr_discards_result_and_releases_frame(self):
  original=self.e['SmartOcr']
  def ocr(*a):
   result=original(*a)
   if len(self.calls)==2:self.e['Sys'].AppIsFront=lambda p:False
   return result
  self.e['SmartOcr']=ocr;self.assertEqual(self.result(),'');self.assertEqual(self.events[-1],'release')
 def test_no_new_business_exit_or_scroll_change(self):
  flow=(ROOT/'flows/012_金币试炼/金币试炼.mq').read_text('utf-8-sig')
  self.assertIn('If TickCount() - movedAt > 1500 Then',flow)
  self.assertIn('Swipe 370, 300, 370, 1000, 300',flow)
  self.assertIn('phase = 3',flow)

if __name__=='__main__':unittest.main()
