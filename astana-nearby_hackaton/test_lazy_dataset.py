# -*- coding: utf-8 -*-
import json,pathlib,tempfile,unittest
from unittest.mock import patch
import app,request_dataset
from understanding import local_profile
from test_app import BASE

class LazyDatasetTests(unittest.TestCase):
 def test_gemini_precedes_provider_and_snapshot(self):
  order=[]
  def interpret(*args):order.append('gemini');return local_profile('Хочу суши')
  def provider(*args):order.append('2gis');return []
  with patch.object(app,'KEY','fake'),patch.object(app,'DIGIS_KEY','fake'),patch.object(app,'ai_profile',side_effect=interpret),patch.object(app,'search_2gis',side_effect=provider),patch.object(app,'dataset',return_value={'places':[]}),patch.object(request_dataset,'save_batch',side_effect=lambda *args:order.append('save')):
   app.recommend(dict(BASE,query='Хочу суши',use_ai=True))
  self.assertEqual(order,['gemini','2gis','save'])
 def test_snapshot_excludes_raw_prompt(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(request_dataset,'ROOT',pathlib.Path(directory)):
   profile=local_profile('Хочу суши');profile['summary']='private user text'
   request_dataset.save_batch(profile,[])
   text=next((pathlib.Path(directory)/'data/request-datasets').glob('*.json')).read_text()
   self.assertNotIn('private user text',text);self.assertEqual(json.loads(text)['source'],'2ГИС')
