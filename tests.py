# coding: utf-8

from datetime import datetime, timedelta
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
        print(status_resp)
        for k in status_resp.keys():
            if k.endswith('_version'):
                self.assertEqual(status_resp[k].count('.'), 2)

    def test_run(self):
        event_start = datetime(year=2019, month=3, day=11, hour=8, tzinfo=sydney)
        event_end = event_start + timedelta(hours=6, minutes=60)
        run_output = run(arrow.get(event_start), arrow.get(event_end))
        self.assertEqual(run_output, {
            '_out': 'survey_tbl#:         662\n'
                    'risk_res_tbl#:       432\n'
                    "Excluded 060 records using 'createdAt' from survey_tbl\n"
                    "Excluded 043 records using 'createdAt' from risk_res_tbl\n"
                    "Excluded 000 records using 'updatedAt' from survey_tbl\n"
                    "Excluded 000 records using 'updatedAt' from risk_res_tbl\n"
                    'joint#:              690\n'
                    'step1_only_sql#:     258\n'
                    'step1_only#:         228\n'
                    'step2_only#:         026\n'
                    "step3_only['id'].size: 0 ;\n"
                    'step3_only#:         000\n'
                    'number_of_risk_res_ids#: 363\n'
                    'event_start_iso 2019-03-11T08:00:00+11:00 event_end_iso '
                    '2019-03-11T15:00:00+11:00\n'
                    'step1_and_2#:        227\n'
                    'step1_and_3#:        011\n'
                    'step2_and_1#:        227\n'
                    'step2_and_3#:        136\n'
                    'step3_and_1#:        000\n'
                    'step3_and_2#:        011\n',
            'all_steps': 136,
            'completed': 0.17801047120418848,
            'email_conversion': 0.2212041884816754,
            'some_combination': 374,
            'step1_count': 228,
            'step2_count': 26,
            'step3_count': 0,
            'survey_count': 764
        })


if __name__ == '__main__':
    unittest_main()
