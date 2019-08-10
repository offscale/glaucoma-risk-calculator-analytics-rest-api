#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

from datetime import datetime, timedelta
from os import environ, path

from glaucoma_analytics_rest_api.utils import PY3

if PY3:
    import io
    from contextlib import redirect_stdout
else:
    from contextlib import contextmanager


    @contextmanager
    def capture():
        import sys
        try:
            # noinspection PyCompatibility
            from cStringIO import StringIO
        except ImportError:
            # noinspection PyCompatibility
            from StringIO import StringIO
        oldout, olderr = sys.stdout, sys.stderr
        out = [StringIO(), StringIO()]
        try:
            sys.stdout, sys.stderr = out
            yield out
        finally:
            sys.stdout, sys.stderr = oldout, olderr
            out[0] = out[0].getvalue()
            out[1] = out[1].getvalue()

just = 20  # indentation

'''
emails = get_ipython().getoutput('sort -u glaucoma-risk-calculator-datadir/emails.txt | egrep -v \'{"email":null}|{"email":""}\' | wc -l')
# ^Ignore duplicated and null entries
emails = int(emails[0]) + 60  # 60 collected independently by OPSM
print('emails collected:'.ljust(just), emails)
'''

from sqlalchemy import create_engine
import pandas as pd

from pytz import timezone, utc


def run(event_start, event_end):  # type: (datetime, datetime) -> dict
    """
    Runner, wraps stdout and stderr also

    :param event_start: start datetime
    :type event_start: datetime

    :param event_end: end datetime
    :type event_end: datetime

    :return: dictionary to show on endpoint
    :rtype: dict
    """
    if PY3:
        f = io.StringIO()
        with redirect_stdout(f):
            res = _run(event_start, event_end)
        res['_out'] = f.getvalue()
    else:
        with capture() as out:
            res = _run(event_start, event_end)
            res['_out'] = out
    return res


# Server was in UTC, switch datetimes to Sydney
sydney = utc.localize(datetime.utcfromtimestamp(1143408899)).astimezone(timezone('Australia/Sydney')).tzinfo


def _run(event_start, event_end):  # type: (datetime, datetime) -> dict
    """
    Runner

    :param event_start: start datetime
    :type event_start: datetime

    :param event_end: end datetime
    :type event_end: datetime

    :return: dictionary to show on endpoint
    :rtype: dict
    """
    engine = create_engine(environ['RDBMS_URI'])

    survey_tbl = pd.read_sql_table('survey_tbl', engine)
    print('survey_tbl#:'.ljust(just), '{:0>3}'.format(len(survey_tbl.index)))

    risk_res_tbl = pd.read_sql_table('risk_res_tbl', engine)
    print('risk_res_tbl#:'.ljust(just), '{:0>3}'.format(len(risk_res_tbl.index)))

    columns = 'createdAt', 'updatedAt'

    for df in (survey_tbl, risk_res_tbl):
        for column in columns:
            try:
                df[column] = df[column].dt.tz_convert(sydney)
            except TypeError as e:
                if 'tz_localize' not in e.args[0]:
                    raise e
                try:
                    df[column] = df[column].dt.tz_localize('UTC').tz_convert(sydney)
                except TypeError as err:
                    if not environ.get('TRAVIS'):
                        raise err

    event_start_iso = event_start.isoformat()
    event_end_iso = event_end.isoformat()

    for column in columns:
        b4_filter = len(survey_tbl.index)
        survey_tbl = survey_tbl.loc[(survey_tbl[column] > event_start)
                                    & (survey_tbl[column] <= event_end)]
        print('Excluded {:0>3d} records using {!r} from survey_tbl'.format(
            b4_filter - len(survey_tbl.index),
            column
        ))

        b4_filter = len(risk_res_tbl.index)
        risk_res_tbl = risk_res_tbl.loc[(risk_res_tbl[column] > event_start)
                                        & (risk_res_tbl[column] <= event_end)]
        print('Excluded {:0>3d} records using {!r} from risk_res_tbl'.format(
            b4_filter - len(risk_res_tbl.index),
            column
        ))

    # survey_tbl.join(risk_res_tbl, on='risk_res_id')
    '''
    SELECT r.client_risk FROM risk_res_tbl r;
    '''

    joint = pd.read_sql_query('''
    SELECT r.age, r.client_risk, r.gender
         , r.ethnicity, r.other_info, r.email
         , r.sibling, r.parent, r.study
         , r.myopia, r.diabetes, r.id AS risk_id
         , r."createdAt", r."updatedAt"
         , s.perceived_risk, s.recruiter, s.eye_test_frequency
         , s.glasses_use, s.behaviour_change, s.risk_res_id
         , s.id, s."createdAt", s."updatedAt"
    FROM survey_tbl s
    FULL JOIN risk_res_tbl r
    ON s.risk_res_id = r.id;
    ''', engine)
    print('joint#:'.ljust(just), '{:0>3}'.format(len(joint.index)))

    step1_only_sql = pd.read_sql_query('''
    SELECT *
    FROM survey_tbl s
    WHERE NOT EXISTS (SELECT *
                      FROM risk_res_tbl r
                      WHERE s.risk_res_id = r.id)
    ''', engine)
    print('step1_only_sql#:'.ljust(just), '{:0>3}'.format(len(step1_only_sql.index)))

    step1_only = survey_tbl[survey_tbl['risk_res_id'].isna() & survey_tbl['behaviour_change'].isna()]
    step1_only_sql = pd.read_sql_query('''
    SELECT COUNT(*)
    FROM survey_tbl s
    WHERE s.risk_res_id IS NULL
          AND s.behaviour_change IS NULL
          AND s."createdAt" BETWEEN {event_start!r} AND {event_end!r};
    '''.format(event_start=event_start_iso,
               event_end=event_end_iso), engine)
    step1_only_count, _s1 = len(step1_only.index), int(step1_only_sql['count'])
    assert step1_only_count == _s1, '{s0} != {s1}'.format(s0=step1_only_count, s1=_s1)
    print('step1_only#:'.ljust(just), '{:0>3}'.format(step1_only_count))

    step2_only = survey_tbl[(survey_tbl['perceived_risk'].isna()
                             & survey_tbl['risk_res_id'].notnull()
                             & survey_tbl['behaviour_change'].isna()
                             )]

    step2_only = risk_res_tbl[
        ~risk_res_tbl['id'].isin(survey_tbl['risk_res_id'])
    ]
    step2_only_sql = pd.read_sql_query('''
    SELECT COUNT(*)
    FROM risk_res_tbl r
    WHERE 
           r."createdAt" BETWEEN {event_start!r} AND {event_end!r}
           AND r.id IN ( SELECT id
                         FROM risk_res_tbl rr
                         EXCEPT
                         SELECT risk_res_id
                         FROM survey_tbl s
                         WHERE s."createdAt" BETWEEN {event_start!r} AND {event_end!r});
    '''.format(event_start=event_start_iso,
               event_end=event_end_iso), engine)
    step2_only_count, _s1 = len(step2_only.index), int(step2_only_sql['count'])

    # assert step1_only_count == _s1, '{s0} != {s1}'.format(s0=step1_only_count, s1=_s1)
    print('step2_only#:'.ljust(just), '{:0>3}'.format(step2_only_count))

    step3_only = survey_tbl[survey_tbl['perceived_risk'].isna()
                            & survey_tbl['risk_res_id'].isna()
                            & survey_tbl['behaviour_change'].notnull()
                            ]
    step3_only_sql = pd.read_sql_query('''
    SELECT COUNT(*)
    FROM survey_tbl s
    WHERE
           s."createdAt" BETWEEN {event_start!r} AND {event_end!r}
           AND s.risk_res_id IS NULL
           AND s.perceived_risk IS NULL;
    '''.format(event_start=event_start_iso,
               event_end=event_end_iso), engine)
    step3_only_count, _snd = len(step3_only['id'].index), int(step3_only_sql['count'])
    assert step3_only_count == _snd, 'Expected {} == {}'.format(step3_only_count, _snd)
    print("step3_only.id.size#:", '{:0>3}'.format(step3_only['id'].size))
    print('step3_only#:'.ljust(just), '{:0>3}'.format(int(step3_only_sql['count'])))

    number_of_risk_res_ids_sql = pd.read_sql_query('''
    SELECT COUNT(risk_res_id)
    FROM survey_tbl s
    WHERE
          s."createdAt" BETWEEN {event_start!r} AND {event_end!r}
            AND s.risk_res_id IS NOT NULL;
    '''.format(event_start=event_start_iso,
               event_end=event_end_iso), engine)

    number_of_unique_risk_res_ids_sql = pd.read_sql_query('''
    SELECT COUNT(*)
    FROM (SELECT DISTINCT risk_res_id
          FROM survey_tbl s
          WHERE
              s."createdAt" BETWEEN {event_start!r} AND {event_end!r}
                AND s.risk_res_id IS NOT NULL
          ) AS C;
    '''.format(event_start=event_start_iso,
               event_end=event_end_iso), engine)

    number_of_risk_res_ids = survey_tbl[
        survey_tbl['risk_res_id'].notnull()
    ]['risk_res_id'].size

    _fst, _snd, _thd = (int(number_of_risk_res_ids_sql['count']), number_of_risk_res_ids,
                        int(number_of_unique_risk_res_ids_sql['count']))
    try:
        assert _fst == _snd == _thd, 'Expected {} == {} == {}'.format(_fst, _snd, _thd)
    except AssertionError:
        assert _fst == _snd == _thd + 1, 'Expected {} == {} == {}'.format(_fst, _snd, _thd + 1)
    print('risk_res_ids#:'.ljust(just), '{:0>3}'.format(number_of_risk_res_ids))

    print('event_start_iso:    ', event_start_iso, '\nevent_end_iso:      ', event_end_iso)

    step1_and_2 = survey_tbl[survey_tbl['perceived_risk'].notnull()
                             & survey_tbl['risk_res_id'].notnull()
                             & survey_tbl['behaviour_change'].isna()
                             ]
    print('step1_and_2#:'.ljust(just), '{:0>3}'.format(len(step1_and_2.index)))

    step1_and_3 = survey_tbl[survey_tbl['perceived_risk'].notnull()
                             & survey_tbl['risk_res_id'].isna()
                             & survey_tbl['behaviour_change'].notnull()
                             ]
    print('step1_and_3#:'.ljust(just), '{:0>3}'.format(len(step1_and_3.index)))

    step2_and_1 = survey_tbl[survey_tbl['perceived_risk'].notnull()
                             & survey_tbl['risk_res_id'].notnull()
                             & survey_tbl['behaviour_change'].isna()
                             ]
    print('step2_and_1#:'.ljust(just), '{:0>3}'.format(len(step2_and_1.index)))

    step2_and_3 = survey_tbl[survey_tbl['perceived_risk'].notnull()
                             & survey_tbl['risk_res_id'].notnull()
                             & survey_tbl['behaviour_change'].notnull()
                             ]
    print('step2_and_3#:'.ljust(just), '{:0>3}'.format(len(step2_and_3.index)))

    step3_and_1 = survey_tbl[survey_tbl['perceived_risk'].isna()
                             & survey_tbl['risk_res_id'].notnull()
                             & survey_tbl['behaviour_change'].notnull()
                             ]
    print('step3_and_1#:'.ljust(just), '{:0>3}'.format(len(step3_and_1.index)))

    step3_and_2 = survey_tbl[survey_tbl['perceived_risk'].notnull()
                             & survey_tbl['risk_res_id'].isna()
                             & survey_tbl['behaviour_change'].notnull()
                             ]
    print('step3_and_2#:'.ljust(just), '{:0>3}'.format(len(step3_and_2.index)))

    def cover_fn(collection):  # type: (tuple) -> int
        return sum(map(lambda s: len(s.index), collection))

    step1_cover = cover_fn((step1_only, step1_and_2, step1_and_3))

    step2_cover = cover_fn((step2_only, step2_and_1, step2_and_3))

    step3_cover = cover_fn((step3_only, step3_and_1, step3_and_2))

    all_steps = survey_tbl[survey_tbl['perceived_risk'].notnull()
                           & survey_tbl['behaviour_change'].notnull()
                           & survey_tbl['risk_res_id'].notnull()
                           ]
    all_steps_count = len(all_steps.index)

    all_or_one = cover_fn((step1_only, step2_only, step3_only, all_steps))

    total = all_or_one + cover_fn((step1_and_2, step1_and_3, step2_and_3))

    merged = survey_tbl.merge(risk_res_tbl,
                              left_on='risk_res_id',
                              right_on='id',
                              suffixes=('_survey', '_risk'))
    '''

    print('Of the {survey_count:d} entries:\n'
          u'\u2022 {step1_count:0>3d} completed just step 1;\n'
          u'\u2022 {step2_count:0>3d} did just step 2;\n'
          u'\u2022 {step3_count:0>3d} did just step 3;\n'
          u'\u2022 {some_combination} did some_combination; and\n'
          u'\u2022 {all_steps:0>3d} finished all 3.\n\n'
          'Some notable statistics:\n'
          u'\u2022 {completed:.2%} completed the final step; and\n'
          u'\u2022 {email_conversion:.2%} converted (provided their emails).'.format(
    '''

    '''emails = !sort -u glaucoma-risk-calculator-datadir/emails.txt | egrep -v '{"email":null}|{"email":""}' | wc -l
    # ^Ignore duplicated and null entries
    emails = int(emails[0]) + 60  # 60 collected independently by OPSM
    '''

    emails_txt_fname = path.join(environ.get('GLAUCOMA_DATADIR', 'glaucoma-risk-calculator-datadir'), 'emails.txt')
    if path.exists(emails_txt_fname):
        with open(emails_txt_fname, 'rt') as f:
            emails = len(frozenset(filter(lambda line: line not in frozenset(('{"email":null}', '{"email":""}')),
                                          map(lambda line: line.strip(), f.readlines()))))
    else:
        emails = 169

    return {'survey_count': total,
            # survey_tbl[survey_tbl['risk_res_id'].isna()]['id'].size
            # + step2_count
            # + joint['id'].size
            # ,
            'step1_count': step1_only_count,
            'step2_count': step2_only_count,
            'step3_count': step3_only_count,
            'some_combination': cover_fn((step1_and_2, step1_and_3, step2_and_3)),
            'all_steps': all_steps_count,
            'email_conversion': emails / total * 100 if total > 0 else total,
            'completed': all_steps_count / total if total > 0 else total
            }


# Average risk calculation
# Use same sorts of statistics used in eLearning course
# Add questionnaire to appendix
# Stratify by ethnicity to see what demography does to outcome measures
# t-test and t-test between groups

if __name__ == '__main__':
    event_start_at = datetime(year=2019, month=3, day=11, hour=8, tzinfo=sydney)
    event_end_at = event_start_at + timedelta(hours=6, minutes=60)
    run_output = run(event_start_at, event_end_at)
