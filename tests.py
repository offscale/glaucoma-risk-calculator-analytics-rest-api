# coding: utf-8

from __future__ import print_function

from datetime import datetime, timedelta
from os import environ
from platform import python_version_tuple
from unittest import TestCase, main as unittest_main

if python_version_tuple()[0] == "3":
    from unittest.mock import patch
else:
    from mock import patch

from six import StringIO
from webtest import TestApp

import glaucoma_risk_calculator_analytics_rest_api

glaucoma_risk_calculator_analytics_rest_api.is_test = True

import glaucoma_risk_calculator_analytics_rest_api.routes
from glaucoma_risk_calculator_analytics_rest_api.analytics import sydney


class TestRestApi(TestCase):
    def setUp(self):
        self.app = TestApp(
            glaucoma_risk_calculator_analytics_rest_api.routes.rest_api,
            extra_environ={"TEST_MODE": "true"},
        )
        self.event_start = datetime(year=2018, month=3, day=11, hour=8, tzinfo=sydney)
        self.event_end = self.event_start + timedelta(days=720)

    def test_status(self):
        """ Not really needed, but whatever """
        for s in ("/api", "/api/py", "/api/status"):
            status_resp = self.app.get(s).json
            for k in status_resp.keys():
                if k.endswith("_version"):
                    self.assertEqual(status_resp[k].count("."), 2)

    def test_analytics2(self, res=None):
        if res is None:
            sio = StringIO()
            with patch("sys.stdout", new_callable=lambda: sio):
                res = glaucoma_risk_calculator_analytics_rest_api.analytics.analytics2(
                    self.event_start, self.event_end
                )

        self.assertSetEqual(
            frozenset(res.keys()),
            frozenset(
                (
                    "survey_count",
                    "step1_count",
                    "step2_count",
                    "step3_count",
                    "some_combination",
                    "all_steps",
                    "email_conversion",
                    "completed",
                    "emails",
                    "joint_explosion",
                    "join_for_pred_unique_cols",
                    "joint_for_pred",
                    "counts",
                )
            ),
        )

    def test_analytics3(self, res=None):
        if res is None:
            res = glaucoma_risk_calculator_analytics_rest_api.analytics.analytics3(
                self.event_start, self.event_end
            )

        # with open(os.path.join(os.path.dirname(__file__), 'delme.svg'), 'wb') as f:
        #     f.write(base64.decodebytes(bytearray(res['feature_importance_gv'], 'utf8')))

        if "TRAVIS" in environ:
            self.assertDictEqual(
                {
                    "error": "XGBClassifier",
                    "error_message": "features are of length 0; labels are of length: 0",
                },
                res,
            )
        else:
            self.assertIn("big_xgb_gv", res)
            self.assertIn("feature_importance_gv", res)

    def test_run(self):
        sio = StringIO()
        with patch("sys.stdout", new_callable=lambda: sio):
            self.test_analytics2(
                self.app.get(
                    "/api/py/analytics2",
                    params={
                        "startDatetime": self.event_start,
                        "endDatetime": self.event_end,
                    },
                ).json
            )

        self.test_analytics3(
            self.app.get(
                "/api/py/analytics3",
                params={
                    "startDatetime": self.event_start,
                    "endDatetime": self.event_end,
                },
                expect_errors="TRAVIS" in environ,
            ).json
        )


if __name__ == "__main__":
    unittest_main()
