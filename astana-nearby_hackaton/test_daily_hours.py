# -*- coding: utf-8 -*-
import datetime,unittest
from scenario_rules import schedule_for_day

class DailyHoursTests(unittest.TestCase):
 def test_only_requested_day_is_selected_in_astana(self):
  reference=datetime.datetime(2026,10,18,20,0,tzinfo=datetime.timezone.utc)
  result=schedule_for_day({'schedule':{'Mon':{'working_hours':[{'from':'12:00','to':'24:00'}]},'Sun':{'working_hours':[{'from':'10:00','to':'18:00'}]}}},reference)
  self.assertEqual(result['date'],'2026-10-19');self.assertEqual(result['intervals'],[{'from':'12:00','to':'24:00'}])
 def test_no_guess_for_missing_day(self):
  result=schedule_for_day({'schedule':{'Tue':{'working_hours':[{'from':'12:00','to':'24:00'}]}}},datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc))
  self.assertEqual(result['status'],'unknown');self.assertEqual(result['intervals'],[])
 def test_split_intervals_and_overnight_are_preserved(self):
  intervals=[{'from':'10:00','to':'14:00'},{'from':'18:00','to':'02:00'}]
  result=schedule_for_day({'schedule':{'Mon':{'working_hours':intervals}}},datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc))
  self.assertEqual(result['intervals'],intervals)
 def test_explicit_day_off(self):
  result=schedule_for_day({'schedule':{'Mon':{'is_closed':True}}},datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc))
  self.assertEqual(result['status'],'day_off')
 def test_old_full_week_text_is_not_displayed(self):
  result=schedule_for_day({'hours':'Mon: 10:00-18:00; Tue: 11:00-19:00'},datetime.datetime(2026,10,19,tzinfo=datetime.timezone.utc))
  self.assertEqual(result['status'],'unknown')

if __name__=='__main__':unittest.main()
