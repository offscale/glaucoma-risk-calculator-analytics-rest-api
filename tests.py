from unittest import TestCase, main as unittest_main

from webtest import TestApp

from namespace_rest_api import rest_api


class TestRestApi(TestCase):
    app = TestApp(rest_api)

    def test_status(self):
        """ Not really needed, but whatever """
        status_resp = self.app.get('/api/status').json
        for k in status_resp.keys():
            if k.endswith('_version'):
                self.assertEqual(status_resp[k].count('.'), 2)


if __name__ == '__main__':
    unittest_main()
