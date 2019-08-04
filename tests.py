# coding: utf-8

from __future__ import print_function

from datetime import datetime, timedelta
from os import environ
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

        self.assertEqual(
            run_output,
            {
                '_out': 'survey_tbl#:         29\n'
                        'risk_res_tbl#:       17\n'
                        "Excluded 022 records using 'createdAt' from survey_tbl\n"
                        "Excluded 011 records using 'createdAt' from risk_res_tbl\n"
                        "Excluded 000 records using 'updatedAt' from survey_tbl\n"
                        "Excluded 000 records using 'updatedAt' from risk_res_tbl\n"
                        'joint#:              34\n'
                        'step1_only_sql#:     17\n'
                        'step1_only#:         1\n'
                        'step2_only#:         000\n'
                        "step3_only['id'].size: 0 ;\n"
                        'step3_only#:         000\n'
                        'number_of_risk_res_ids#: 6\n'
                        'event_start_iso 2019-03-11T08:00:00+11:00 event_end_iso '
                        '2019-03-11T15:00:00+11:00\n'
                        'step1_and_2#:        3\n'
                        'step1_and_3#:        000\n'
                        'step2_and_1#:        3\n'
                        'step2_and_3#:        3\n'
                        'step3_and_1#:        000\n'
                        'step3_and_2#:        000\n',
                'all_steps': 3,
                'completed': 0.3,
                'email_conversion': 16.9,
                'some_combination': 6,
                'step1_count': 1,
                'step2_count': 0,
                'step3_count': 0,
                'survey_count': 10
            } if environ.get('TRAVIS') else {
                '_out': [
                    'survey_tbl#:         0\n'
                    'risk_res_tbl#:       0\n'
                    'Excluded 000 records using \'createdAt\' from survey_tbl\n'
                    'Excluded 000 records using \'createdAt\' from risk_res_tbl\n'
                    'Excluded 000 records using \'updatedAt\' from survey_tbl\n'
                    'Excluded 000 records using \'updatedAt\' from risk_res_tbl\n'
                    'joint#:              0\n'
                    'step1_only_sql#:     0\n'
                    'step1_only#:         0\n'
                    'step2_only#:         000\n'
                    'step3_only[\'id\'].size: 0 ;\n'
                    'step3_only#:         000\n'
                    'number_of_risk_res_ids#: 0\n'
                    'event_start_iso 2019-03-11T08:00:00+11:00 event_end_iso 2019-03-11T15:00:00+11:00\n'
                    'step1_and_2#:        0\n'
                    'step1_and_3#:        000\n'
                    'step2_and_1#:        0\n'
                    'step2_and_3#:        0\n'
                    'step3_and_1#:        000\n'
                    'step3_and_2#:        000\n',
                    ''],
                'all_steps': 0,
                'completed': 0,
                'email_conversion': 0,
                'some_combination': 0,
                'step1_count': 0,
                'step2_count': 0,
                'step3_count': 0,
                'survey_count': 0}
        )


if __name__ == '__main__':
    unittest_main()
