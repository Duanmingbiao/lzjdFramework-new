"""Keep historical no-sync snapshots immutable; follow explicit authorized sync records."""
import json
from mq_subset import ROOT

def authorized_sync_baseline(baseline):
 path=ROOT/'reports/授权同步边界.json'
 if not path.exists():return baseline
 journal=json.loads(path.read_text('utf8'))
 project=json.loads((ROOT/'assistant-sync.json').read_text('utf8'))['id']
 for record in journal:
  assert record['authorizedByUser'] is True
  assert record['projectId']==project
  assert set(record['before'])==set(record['after'])
  if baseline==record['before']:
   baseline=record['after']
 return baseline
