#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

from base64 import b64encode, encodestring, encodebytes
from datetime import datetime, timedelta
from functools import partial
from os import environ, path
from sys import modules

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pkg_resources import resource_filename
from pytz import timezone, utc
from six import iteritems
# import statsmodels as stats
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import create_engine
from xgboost import XGBClassifier, to_graphviz, plot_importance

try:
    from cStringIO import StringIO
except ImportError:
    from six import StringIO

from glaucoma_analytics_rest_api.utils import PY3, update_d, maybe_to_dict

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

'''
emails = get_ipython().getoutput(
  'sort -u glaucoma-risk-calculator-datadir/emails.txt | egrep -v \'{"email":null}|{"email":""}\' | wc -l'
)
# ^Ignore duplicated and null entries
emails = int(emails[0]) + 60  # 60 collected independently by OPSM
print('emails collected:'.ljust(just), emails)
'''

# Global variables FTW

just = 20  # indentation

parent_dir = path.dirname(resource_filename(modules[__name__].__name__.partition('.')[0], '__main__.py'))
with open(path.join(parent_dir, '_data', 'joint_explosion.sql')) as f:
    joint_explosion_query = f.read()


# /end global vars

def run(event_start, event_end, function):  # type: (datetime, datetime) -> dict
    """
    Runner, wraps stdout and stderr also

    :param event_start: start datetime
    :type event_start: datetime

    :param event_end: end datetime
    :type event_end: datetime

    :param function: function to run
    :type function: (datetime, datetime) -> {}

    :return: dictionary to show on endpoint
    :rtype: dict
    """
    if PY3:
        f = io.StringIO()
        with redirect_stdout(f):
            res = function(event_start, event_end)
        res['_out'] = f.getvalue()
    else:
        with capture() as out:
            res = function(event_start, event_end)
            res['_out'] = out
    return res


# Server was in UTC, switch datetimes to Sydney
sydney = utc.localize(datetime.utcfromtimestamp(1143408899)).astimezone(timezone('Australia/Sydney')).tzinfo


def analytics2(event_start, event_end, to_dict=True):  # type: (datetime, datetime, bool) -> dict
    """
    Runner

    :param event_start: start datetime
    :type event_start: datetime

    :param event_end: end datetime
    :type event_end: datetime

    :param to_dict: Convert from Pandas formats to Python dictionary
    :type to_dict: bool

    :return: dictionary to show on endpoint
    :rtype: dict
    """
    engine = create_engine(environ['RDBMS_URI'])

    survey_tbl = pd.read_sql_table('survey_tbl', engine)
    survey_tbl_count = len(survey_tbl.index)
    print('survey_tbl#:'.ljust(just), '{:0>3}'.format(survey_tbl_count))

    risk_res_tbl = pd.read_sql_table('risk_res_tbl', engine)
    risk_res_tbl_count = len(risk_res_tbl.index)
    print('risk_res_tbl#:'.ljust(just), '{:0>3}'.format(risk_res_tbl_count))

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
        print('survey_tbl:'.ljust(just), '{:0>3d} (excluded using {!r})'.format(
            b4_filter - len(survey_tbl.index),
            column
        ))

        b4_filter = len(risk_res_tbl.index)
        risk_res_tbl = risk_res_tbl.loc[(risk_res_tbl[column] > event_start)
                                        & (risk_res_tbl[column] <= event_end)]
        print('risk_res_tbl:'.ljust(just), '{:0>3d} (excluded using {!r})'.format(
            b4_filter - len(risk_res_tbl.index),
            column
        ))

    # survey_tbl.join(risk_res_tbl, on='risk_res_id')
    '''
    SELECT r.client_risk
    FROM risk_res_tbl r;
    '''

    joint = pd.read_sql_query('''
        SELECT r.age, r.client_risk, r.gender, r.ethnicity, r.other_info, r.email,
               r.sibling, r.parent, r.study, r.myopia, r.diabetes, r.id AS risk_id,
               r."createdAt", r."updatedAt", s.perceived_risk, s.recruiter,
               s.eye_test_frequency, s.glasses_use, s.behaviour_change,
               s.risk_res_id, s.id, s."createdAt", s."updatedAt"
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
    print('step3_only#:'.ljust(just), '{:0>3}'.format(step3_only_count))

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

    total = float(all_or_one + cover_fn((step1_and_2, step1_and_3, step2_and_3)))

    merged = survey_tbl.merge(risk_res_tbl,
                              left_on='risk_res_id',
                              right_on='id',
                              suffixes=('_survey', '_risk'))

    joint_for_pred = run_join_for_pred_query(engine, event_end_iso, event_start_iso)

    print('\nThe following includes only records that completed all 3 steps:')
    print('joint_for_pred#:'.ljust(just), '{:0>3}'.format(len(joint_for_pred.index)))

    _joint_for_pred_3cols = joint_for_pred[['client_risk_mag', 'perceived_risk_mag', 'behaviour_change']]
    join_for_pred_unique_cols = {column: _joint_for_pred_3cols[column].value_counts().to_dict()
                                 for column in _joint_for_pred_3cols}

    # joint_for_pred[joint_for_pred[''] == '']
    # ethnicities = (lambda array: array.to_list() if to_dict else array)(
    #    pd.read_sql_query('SELECT DISTINCT(ethnicity) FROM risk_res_tbl;', engine).values.flatten()
    # )

    joint_explosion = pd.read_sql_query(
        joint_explosion_query.replace('EVENT_START', event_start_iso).replace('EVENT_END', event_end_iso),
        engine, 'id'
    )

    expl_cat_df = joint_explosion[
        [col for col in joint_explosion.columns
         if '::' in col]
    ]

    name2variant_value = {}
    for col in expl_cat_df:
        name, variant = col.split('::')
        value = (lambda vc: True in vc.index and vc.loc[True] or 0)(
            expl_cat_df[col].value_counts()
        )
        total = int(value.sum()) if value > 0 else value
        with open('/tmp/v.txt', 'a') as f:
            f.write('value: {} ;\n'.format(value))

        if name not in name2variant_value:
            name2variant_value[name] = {variant: int(value) if to_dict else value,
                                        'Total': int(total) if to_dict else total}
        else:
            name2variant_value[name][variant] = int(value) if to_dict else value

    # Fix 'Total' calculation
    for name, variant_value in iteritems(name2variant_value):
        total = 0
        for variant, value in iteritems(variant_value):
            if variant != 'Total':
                total += value
        name2variant_value[name]['Total'] = total

    def add_percentage(d):
        for key, val in iteritems(d):
            if 'Total' not in val:
                return d
            for k, v in iteritems(val):
                if k != 'Total':
                    d[key][k] = {
                        'percentage': np.multiply(
                            np.true_divide(np.float64(v),
                                           np.float64(val['Total'])),
                            np.float64(100)),
                        'value': v
                    }

        return d

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

    if total > 0:
        email_conversion = emails / total * 100
        completed = all_steps_count / total
    else:
        email_conversion = completed = 0

    maybe2dict = partial(maybe_to_dict, to_dict=to_dict)

    return {
        'survey_count': total,
        # survey_tbl[survey_tbl['risk_res_id'].isna()]['id'].size
        # + step2_count
        # + joint['id'].size
        # ,
        'step1_count': step1_only_count,
        'step2_count': step2_only_count,
        'step3_count': step3_only_count,
        'some_combination': cover_fn((step1_and_2, step1_and_3, step2_and_3)),
        'all_steps': all_steps_count,
        'email_conversion': email_conversion,
        'completed': completed,
        'emails': emails,
        'joint_explosion': maybe2dict(joint_explosion),
        'join_for_pred_unique_cols': join_for_pred_unique_cols,
        'joint_for_pred': maybe2dict(joint_for_pred),
        'counts': add_percentage(update_d({
            column: (lambda p: update_d(
                p.to_dict(),
                {'Total': int(p.sum())}
            ))(joint_for_pred[column].value_counts())
            for column in ('gender', 'age_mag', 'client_risk_mag', 'behaviour_change')
        }, ethnicity=name2variant_value['ethnicity']))
    }


def run_join_for_pred_query(engine, event_end_iso, event_start_iso):
    return pd.read_sql_query('''
        WITH joint AS (
            SELECT r.age, r.client_risk, r.gender, r.ethnicity, r.other_info, r.email,
                   r.sibling, r.parent, r.study, r.myopia, r.diabetes, r.id AS risk_id,
                   r."createdAt", r."updatedAt",
                   s.perceived_risk, s.recruiter, s.eye_test_frequency,  s.glasses_use,
                   s.behaviour_change, s.risk_res_id, s.id,
                   s."createdAt" as created, s."updatedAt" as updated,
                   (array ['lowest','low','med','high'])[
                       ceil(greatest(client_risk, 1) / 25.0)
                   ] AS client_risk_mag,
                   (array ['lowest','low','med','high'])[
                       ceil(greatest(perceived_risk, 1) / 25.0)
                   ] AS perceived_risk_mag,
                   (array ['000–025','025–050','050–075','075–100'])[
                       ceil(greatest(perceived_risk, 1) / 25.0)
                   ] AS age_mag
            FROM survey_tbl s
            FULL JOIN risk_res_tbl r
            ON s.risk_res_id = r.id
            WHERE recruiter IS NOT NULL
                  AND age IS NOT NULL
                  AND risk_res_id IS NOT NULL
                  AND behaviour_change IS NOT NULL
                  AND s."createdAt" BETWEEN 'EVENT_START'::timestamptz AND 'EVENT_END'::timestamptz
                  AND s."updatedAt" BETWEEN 'EVENT_START'::timestamptz AND 'EVENT_END'::timestamptz
                  AND r."createdAt" BETWEEN 'EVENT_START'::timestamptz AND 'EVENT_END'::timestamptz
                  AND r."updatedAt" BETWEEN 'EVENT_START'::timestamptz AND 'EVENT_END'::timestamptz

                   )
        SELECT id, age, age_mag, client_risk, client_risk_mag, gender,
               perceived_risk, perceived_risk_mag, behaviour_change, ethnicity
        FROM joint
        WHERE created BETWEEN 'EVENT_START'::timestamptz AND 'EVENT_END'::timestamptz
              AND updated BETWEEN 'EVENT_START'::timestamptz AND 'EVENT_END'::timestamptz
        ORDER BY client_risk, perceived_risk;
    '''.replace('EVENT_START', event_start_iso).replace('EVENT_END', event_end_iso), index_col='id', con=engine)


def analytics3(event_start, event_end, to_dict=True):  # type: (datetime, datetime, bool) -> dict
    """
    Runner

    :param event_start: start datetime
    :type event_start: datetime

    :param event_end: end datetime
    :type event_end: datetime

    :param to_dict: Convert from Pandas formats to Python dictionary
    :type to_dict: bool

    :return: dictionary to show on endpoint
    :rtype: dict
    """
    event_start_iso = event_start.isoformat()
    event_end_iso = event_end.isoformat()

    engine = create_engine(environ['RDBMS_URI'])

    join_for_pred = run_join_for_pred_query(engine, event_end_iso, event_start_iso)
    join_for_pred = join_for_pred.reset_index()
    join_for_pred = join_for_pred.loc[:, join_for_pred.columns != 'index']

    join_for_pred.rename(columns={'perceived_risk': 'perception'})

    cat_df = join_for_pred.loc[:, join_for_pred.columns != 'age']  # creating a dataset only for categorical variables
    cat_df = cat_df.loc[:, cat_df.columns != 'client_risk']

    le = LabelEncoder()
    enc_df = pd.DataFrame({column: le.fit_transform(cat_df[column])
                           for column in cat_df})
    # append the age and client_risk columns onto the categorical dataframe
    # we can do this since label encoding maintains row order
    data_cat = enc_df
    data_cat['age'] = join_for_pred['age']
    data_cat['client_risk'] = join_for_pred['client_risk']

    features = data_cat.loc[:, data_cat.columns != 'behaviour_change']
    label = data_cat['behaviour_change']

    model = XGBClassifier()
    model.fit(features, label)

    def booster2graphviz(booster, fmap='', num_trees=0, rankdir='UT', ax=None, **kwargs):
        if ax is None:
            _, ax = plt.subplots(1, 1)

        return to_graphviz(booster, fmap=fmap, num_trees=num_trees,
                           rankdir=rankdir, **kwargs)

    big_xgb_gv = booster2graphviz(model)

    feature_importance_gv = {}
    k = plot_importance(model)
    k.plot()
    for f in dir(k):
        try:
            feature_importance_gv[f] = getattr(plot_importance, f)()
        except Exception as e:
            print(e)

    sio = StringIO()
    plt.savefig(sio, format='svg')
    sio.seek(0)
    feature_importance_gv = '{}'.format(b64encode(sio.read().encode('utf-8')))[2:-1]
    # feature_importance_gv['plot_importance(model)'] = '{}'.format(plot_importance(model))

    return {
        'big_xgb_gv': '{}'.format(big_xgb_gv),
        'feature_importance_gv': '{}'.format(feature_importance_gv)
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
