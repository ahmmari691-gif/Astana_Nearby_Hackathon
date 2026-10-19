# -*- coding: utf-8 -*-
import unittest
import app
from test_app import BASE,place
from test_verification import normalized
class MinimumRatingTests(unittest.TestCase):
 def test_low_rating_excluded_but_three_and_unrated_kept(self):
  places=[]
  for i,rating in enumerate((2.9,3,4.5,None)):
   places.append(normalized(id=str(123456+i),rubrics=[{'name':'Парки'}],name_ex={'primary':str(i),'extension':'парк'},reviews={'general_rating':rating}))
  rows,_=app.retrieve(dict(BASE,_min_rating=3),places)
  self.assertEqual({p['id'] for p in rows},{'2gis/123457','2gis/123458','2gis/123459'})
 def test_missing_or_invalid_rating_does_not_exclude(self):
  self.assertTrue(app.has_minimum_rating(place()))
  for value in (None,True,'2.0',float('nan'),-1,8):
   self.assertTrue(app.has_minimum_rating(normalized(reviews={'general_rating':value})))
 def test_organisation_rating_does_not_replace_branch_rating(self):
  self.assertTrue(app.has_minimum_rating(normalized(reviews={'is_org_reviews':True,'general_rating':2})))

if __name__=='__main__':unittest.main()
