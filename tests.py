# coding: utf-8

from __future__ import print_function

from datetime import datetime, timedelta
from os import environ
from pprint import PrettyPrinter
from unittest import TestCase, main as unittest_main

import arrow
from webtest import TestApp

from glaucoma_analytics_rest_api import rest_api
from glaucoma_analytics_rest_api.analytics import sydney
from glaucoma_analytics_rest_api.routes import run


class TestRestApi(TestCase):
    maxDiff = 444444
    app = TestApp(rest_api)

    def test_status(self):
        """ Not really needed, but whatever """
        status_resp = self.app.get('/api/status').json
        for k in status_resp.keys():
            if k.endswith('_version'):
                self.assertEqual(status_resp[k].count('.'), 2)

    def test_run(self):
        event_start = datetime(year=2019, month=3, day=11, hour=8, tzinfo=sydney)
        event_end = event_start + timedelta(hours=6, minutes=60)
        run_output = run(arrow.get(event_start), arrow.get(event_end))

        PrettyPrinter(indent=4).pprint(run_output)

        self.assertEqual(
            run_output,
            {'_out': 'survey_tbl#:         000\n'
                     'risk_res_tbl#:       000\n'
                     "Excluded 022 records using 'createdAt' from survey_tbl\n"
                     "Excluded 011 records using 'createdAt' from risk_res_tbl\n"
                     "Excluded 000 records using 'updatedAt' from survey_tbl\n"
                     "Excluded 000 records using 'updatedAt' from risk_res_tbl\n"
                     'joint#:              000\n'
                     'step1_only_sql#:     000\n'
                     'step1_only#:         001\n'
                     'step2_only#:         000\n'
                     'step3_only.id.size#: 000\n'
                     'step3_only#:         000\n'
                     'risk_res_ids#:       000\n'
                     'event_start_iso:     2019-03-11T08:00:00+11:00 \n'
                     'event_end_iso:       2019-03-11T15:00:00+11:00\n'
                     'step1_and_2#:        000\n'
                     'step1_and_3#:        000\n'
                     'step2_and_1#:        000\n'
                     'step2_and_3#:        000\n'
                     'step3_and_1#:        000\n'
                     'step3_and_2#:        000\n',
             'all_steps': 3,
             'completed': 0.3,
             'email_conversion': 16.9,
             'some_combination': 6,
             'step1_count': 1,
             'step2_count': 0,
             'step3_count': 0,
             'survey_count': 10}
            if environ.get('TRAVIS')
            else {'_out': 'survey_tbl#:         029\n'
                          'risk_res_tbl#:       017\n'
                          "Excluded 022 records using 'createdAt' from survey_tbl\n"
                          "Excluded 011 records using 'createdAt' from risk_res_tbl\n"
                          "Excluded 000 records using 'updatedAt' from survey_tbl\n"
                          "Excluded 000 records using 'updatedAt' from risk_res_tbl\n"
                          'joint#:              034\n'
                          'step1_only_sql#:     017\n'
                          'step1_only#:         001\n'
                          'step2_only#:         000\n'
                          'step3_only.id.size#: 000\n'
                          'step3_only#:         000\n'
                          'risk_res_ids#:       006\n'
                          'event_start_iso:     2019-03-11T08:00:00+11:00 \n'
                          'event_end_iso:       2019-03-11T15:00:00+11:00\n'
                          'step1_and_2#:        003\n'
                          'step1_and_3#:        000\n'
                          'step2_and_1#:        003\n'
                          'step2_and_3#:        003\n'
                          'step3_and_1#:        000\n'
                          'step3_and_2#:        000\n',
                  'all_steps': 3,
                  'completed': 0.3,
                  'email_conversion': 16.9,
                  'some_combination': 6,
                  'step1_count': 1,
                  'step2_count': 0,
                  'step3_count': 0,
                  'survey_count': 10}
        )


if __name__ == '__main__':
    unittest_main()
