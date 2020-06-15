WITH joint_explosion AS (
    SELECT r.age,
           r.client_risk,
           r.gender,
           r.ethnicity,
           r.other_info,
           r.email,
           r.sibling,
           r.parent,
           r.study,
           r.myopia,
           r.diabetes,
           r.id                                                                       AS risk_id,
           r."createdAt",
           r."updatedAt",
           r.age BETWEEN 0 AND 25                                                     AS "age::0-25",
           r.age BETWEEN 25 AND 50                                                    AS "age::25-50",
           r.age BETWEEN 50 AND 75                                                    AS "age::50-75",
           r.age BETWEEN 75 AND 100                                                   AS "age::75-100",
           r.client_risk BETWEEN 0 AND 25                                             AS "client_risk::lowest",
           r.client_risk BETWEEN 25 AND 50                                            AS "client_risk::low",
           r.client_risk BETWEEN 50 AND 75                                            AS "client_risk::med",
           r.client_risk BETWEEN 75 AND 100                                           AS "client_risk::high",
           s.perceived_risk,
           s.recruiter,
           s.eye_test_frequency,
           s.glasses_use,
           s.behaviour_change,
           s.risk_res_id,
           s.id,
           s."createdAt",
           s."updatedAt",
           s.behaviour_change = 'no_change'                                           AS "behaviour_change::no_change",
           s.behaviour_change = 'less_likely'                                         AS "behaviour_change::less_likely",
           s.behaviour_change = 'as_recommended'                                      AS "behaviour_change::as_recommended",
           -- generated:
           -- use `ethnicity2study_res` from glaucoma-risk-calculator-engine AND
           -- use `ethnicities` from `pd.read_sql_query('SELECT DISTINCT(ethnicity)
           --                                            FROM risk_res_tbl;', engine).values.flatten()`
           --  print(',\n'.join('r.ethnicity = \'{e}\' AS "ethnicity::{r}"'.format(e=e,
           --                                                                      r=ethnicity2study_res[e])
           --                   for e in ethnicities))
           r.ethnicity = 'White (German; Norwegian; Irish; English)'                  AS "ethnicity::olmsted",
           r.ethnicity = 'Nepalese'                                                   AS "ethnicity::nepal",
           r.ethnicity = 'Australian Aboriginal'                                      AS "ethnicity::aboriginal",
           r.ethnicity = 'Chinese [Singapore: urban]'                                 AS "ethnicity::singapore",
           r.ethnicity = 'White (Northern European: Australian)'                      AS "ethnicity::bmes",
           r.ethnicity = 'Japanese'                                                   AS "ethnicity::japanese",
           r.ethnicity = 'Korean'                                                     AS "ethnicity::korean",
           r.ethnicity = 'Black African (Ghana)'                                      AS "ethnicity::ghana",
           r.ethnicity = 'Black African (Barbados, Lesser Antilles, Caribbean)'       AS "ethnicity::barbados",
           r.ethnicity = 'White European (Canadian; Italian; Irish; Welsh; Scottish)' AS "ethnicity::framingham",
           r.ethnicity = 'Indian'                                                     AS "ethnicity::indian",
           -- ^generated
           (array ['lowest','low','med','high'])[
               ceil(greatest(client_risk, 1) / 25.0)
               ]                                                                      AS client_risk_mag,
           (array ['lowest','low','med','high'])[
               ceil(greatest(perceived_risk, 1) / 25.0)
               ]                                                                      AS perceived_risk_mag,
           (array ['000–025','025–050','050–075','075–100'])[
               ceil(greatest(perceived_risk, 1) / 25.0)
               ]                                                                      AS age_mag
    FROM survey_tbl s
             FULL JOIN risk_res_tbl r
                       ON s.risk_res_id = r.id
    WHERE recruiter IS NOT NULL
      AND age IS NOT NULL
      AND risk_res_id IS NOT NULL
      AND behaviour_change IS NOT NULL
      AND s."createdAt" BETWEEN 'EVENT_START' AND 'EVENT_END'
    GROUP BY r.ethnicity, r.age, r.client_risk, r.gender, r.other_info, r.email,
             r.sibling, r.parent, r.study, r.myopia, r.diabetes, r.id,
             s.perceived_risk, s.recruiter, s.eye_test_frequency, s.glasses_use,
             s.behaviour_change, s.risk_res_id, s.id
    ORDER BY r.ethnicity, r.gender)
SELECT id,
       age,
       age_mag,
       client_risk,
       client_risk_mag,
       gender,
       perceived_risk,
       perceived_risk_mag,
       behaviour_change,
       "age::0-25",
       "age::25-50",
       "age::50-75",
       "age::75-100",
       "client_risk::lowest",
       "client_risk::low",
       "client_risk::med",
       "client_risk::high",
       "behaviour_change::no_change",
       "behaviour_change::less_likely",
       "behaviour_change::as_recommended",
       "ethnicity::olmsted",
       "ethnicity::nepal",
       "ethnicity::aboriginal",
       "ethnicity::singapore",
       "ethnicity::bmes",
       "ethnicity::japanese",
       "ethnicity::korean",
       "ethnicity::ghana",
       "ethnicity::barbados",
       "ethnicity::framingham",
       "ethnicity::indian"
FROM joint_explosion j
ORDER BY j.client_risk, j.perceived_risk;
