ONTOLOGY_TTL_EMBEDDED = '__ONTOLOGY_TTL__'

ontology_candidates = [Path.cwd() / 'ontology' / 'diabetes_screening.ttl', Path.cwd().parent / 'ontology' / 'diabetes_screening.ttl']
ontology_path = next((p for p in ontology_candidates if p.exists()), None)
ontology_graph = Graph()
if ontology_path:
    ontology_graph.parse(ontology_path, format='turtle')
    print('Loaded repository ontology:', ontology_path)
else:
    ontology_graph.parse(data=ONTOLOGY_TTL_EMBEDDED, format='turtle')
    ontology_path = ARTIFACT_DIR / 'diabetes_screening.ttl'
    ontology_path.write_text(ONTOLOGY_TTL_EMBEDDED, encoding='utf-8')
    print('Loaded embedded ontology and wrote a copy to:', ontology_path)

EX_NS = 'https://w3id.org/clinontoscreen/ontology#'
def ontology_parameter(subject_name, predicate_name, default):
    from rdflib import URIRef
    subject = URIRef(EX_NS + subject_name)
    predicate = URIRef(EX_NS + predicate_name)
    values = list(ontology_graph.objects(subject, predicate))
    return float(values[0]) if values else float(default)
def ontology_text(subject_name, predicate_name, default=''):
    from rdflib import URIRef
    values = list(ontology_graph.objects(URIRef(EX_NS + subject_name), URIRef(EX_NS + predicate_name)))
    return str(values[0]) if values else default
AGE_THRESHOLD = ontology_parameter('Age35Criterion', 'thresholdValue', 35)
BMI_GENERAL = ontology_parameter('BMIOverweightGeneralCriterion', 'thresholdValue', 25)
BMI_ASIAN = ontology_parameter('BMIOverweightAsianCriterion', 'thresholdValue', 23)
SBP_THRESHOLD = ontology_parameter('HypertensionRiskCriterion', 'systolicThreshold', 130)
DBP_THRESHOLD = ontology_parameter('HypertensionRiskCriterion', 'diastolicThreshold', 80)
INACTIVITY_MAX_MINUTES = ontology_parameter('PhysicalInactivityRiskCriterion', 'thresholdValue', 0)
from rdflib import URIRef
_codes = list(ontology_graph.objects(URIRef(EX_NS+'HigherRiskEthnicityCriterion'), URIRef(EX_NS+'categoryCodes')))
HIGHER_RISK_ETHNICITY_CODES = [int(x.strip()) for x in (str(_codes[0]) if _codes else '1,2,4,6').split(',')]
RULE_SECTIONS = {rule: ontology_text(rule, 'sectionReference', 'unspecified') for rule in ['AgeBasedScreeningRule','YoungerAdultRiskBasedRule']}
print('Ontology triples:', len(ontology_graph), '| thresholds:', AGE_THRESHOLD, BMI_GENERAL, BMI_ASIAN, SBP_THRESHOLD, DBP_THRESHOLD)
for rule, section in RULE_SECTIONS.items():
    print(f'  {rule} -> {section}')

RAW_NUMERIC = ['age_years','income_poverty_ratio','bmi','waist_cm','hdl_chol_mgdl','leisure_activity_minutes','sedentary_minutes','systolic_bp_mean','diastolic_bp_mean']
RAW_CATEGORICAL = ['sex_code','race_ethnicity_code','education_code','hypertension_history','hypertension_treatment','ever_smoked_100_cigs','heart_failure_history','coronary_heart_disease_history','angina_history','heart_attack_history','stroke_history']
RAW_FEATURES = RAW_NUMERIC + RAW_CATEGORICAL
ONTOLOGY_FEATURES = ['onto_age_based_screening','onto_bmi_threshold_met','onto_hypertension_risk','onto_cvd_history','onto_physical_inactivity','onto_higher_risk_ethnicity','onto_additional_risk_factor_count','onto_screening_eligible','onto_criteria_observed_count','onto_criteria_missing_count','onto_rule_priority_score']
MANUAL_FEATURES = [c.replace('onto_', 'manual_') for c in ONTOLOGY_FEATURES]
FORBIDDEN_FEATURE_TOKENS = ('hba1c','glucose','reported_diabetes','reported_prediabetes','target','diabetes_medication')
assert not any(any(token in c.lower() for token in FORBIDDEN_FEATURE_TOKENS) for c in RAW_FEATURES + ONTOLOGY_FEATURES)
assert 'SEQN' not in RAW_FEATURES
assert all(len(section) > 20 for section in RULE_SECTIONS.values()), 'Every executable rule must carry a guideline section reference'

def yes_no_flag(frame, col):
    vals = pd.to_numeric(frame[col], errors='coerce') if col in frame else pd.Series(np.nan,index=frame.index,dtype='float64')
    return vals.map({1.0:1.0,2.0:0.0}).astype('float64')

def any_flag(flags, index):
    values = pd.concat(flags, axis=1)
    result = pd.Series(np.nan,index=index,dtype='float64')
    any_yes = values.eq(1).any(axis=1); any_known = values.notna().any(axis=1)
    result.loc[any_yes] = 1.0; result.loc[~any_yes & any_known] = 0.0
    return result

def derive_ontology_features(frame, include_ethnicity=True):
    out = frame.copy()
    age = pd.to_numeric(out.get('age_years',pd.Series(np.nan,index=out.index)),errors='coerce')
    bmi = pd.to_numeric(out.get('bmi',pd.Series(np.nan,index=out.index)),errors='coerce')
    race = pd.to_numeric(out.get('race_ethnicity_code',pd.Series(np.nan,index=out.index)),errors='coerce')
    asian = race.eq(6); cutoff = pd.Series(BMI_GENERAL,index=out.index,dtype='float64'); cutoff.loc[asian] = BMI_ASIAN
    bmi_flag = pd.Series(np.nan,index=out.index,dtype='float64'); known_bmi = bmi.notna() & race.notna(); bmi_flag.loc[known_bmi] = (bmi.loc[known_bmi] >= cutoff.loc[known_bmi]).astype(float)
    age_flag = pd.Series(np.nan,index=out.index,dtype='float64'); age_flag.loc[age.notna()] = (age.loc[age.notna()] >= AGE_THRESHOLD).astype(float)
    sbp = pd.to_numeric(out.get('systolic_bp_mean',pd.Series(np.nan,index=out.index)),errors='coerce')
    dbp = pd.to_numeric(out.get('diastolic_bp_mean',pd.Series(np.nan,index=out.index)),errors='coerce')
    measured_bp = pd.Series(np.nan,index=out.index,dtype='float64'); bp_known = sbp.notna() | dbp.notna()
    measured_bp.loc[bp_known] = (((sbp >= SBP_THRESHOLD) | (dbp >= DBP_THRESHOLD)).loc[bp_known]).astype(float)
    hypertension = any_flag([measured_bp,yes_no_flag(out,'hypertension_history'),yes_no_flag(out,'hypertension_treatment')],out.index)
    cvd = any_flag([yes_no_flag(out,c) for c in ['heart_failure_history','coronary_heart_disease_history','angina_history','heart_attack_history','stroke_history']],out.index)
    minutes = pd.to_numeric(out.get('leisure_activity_minutes',pd.Series(np.nan,index=out.index)),errors='coerce')
    inactivity = pd.Series(np.nan,index=out.index,dtype='float64')
    inactivity.loc[minutes.notna() & (minutes <= INACTIVITY_MAX_MINUTES)] = 1.0
    inactivity.loc[minutes.notna() & (minutes > INACTIVITY_MAX_MINUTES)] = 0.0
    ethnicity = pd.Series(np.nan,index=out.index,dtype='float64')
    if include_ethnicity:
        ethnicity.loc[race.notna()] = race.loc[race.notna()].isin(HIGHER_RISK_ETHNICITY_CODES).astype(float)
    else:
        ethnicity = pd.Series(0.0,index=out.index,dtype='float64')
    risk_columns = [hypertension,cvd,inactivity]
    if include_ethnicity: risk_columns.append(ethnicity)
    risks = pd.concat(risk_columns,axis=1); risk_count = risks.fillna(0).sum(axis=1).astype(float); risk_count.loc[risks.notna().sum(axis=1)==0] = np.nan
    eligible = pd.Series(np.nan,index=out.index,dtype='float64'); eligible.loc[age >= AGE_THRESHOLD] = 1.0
    younger = age.notna() & (age < AGE_THRESHOLD) & bmi_flag.notna(); eligible.loc[younger & bmi_flag.eq(0)] = 0.0
    eligible.loc[younger & bmi_flag.eq(1) & (risk_count >= 1)] = 1.0; eligible.loc[younger & bmi_flag.eq(1) & risk_count.eq(0)] = 0.0
    criteria_columns = [age_flag,bmi_flag,hypertension,cvd,inactivity]
    if include_ethnicity: criteria_columns.append(ethnicity)
    criteria = pd.concat(criteria_columns,axis=1); observed = criteria.notna().sum(axis=1).astype(float); missing = criteria.isna().sum(axis=1).astype(float)
    priority = criteria.fillna(0).sum(axis=1).astype(float) / observed.replace(0,np.nan)
    vals = [age_flag,bmi_flag,hypertension,cvd,inactivity,ethnicity,risk_count,eligible,observed,missing,priority.fillna(0.0)]
    for name,val in zip(ONTOLOGY_FEATURES,vals): out[name]=val
    return out

def derive_manual_control(frame):
    out = frame.copy(); age=pd.to_numeric(out['age_years'],errors='coerce'); bmi=pd.to_numeric(out['bmi'],errors='coerce'); race=pd.to_numeric(out['race_ethnicity_code'],errors='coerce')
    threshold=np.where(race.eq(6),BMI_ASIAN,BMI_GENERAL); bmi_flag=pd.Series(np.where(bmi.notna()&race.notna(),(bmi>=threshold).astype(float),np.nan),index=out.index)
    age_flag=pd.Series(np.where(age.notna(),(age>=AGE_THRESHOLD).astype(float),np.nan),index=out.index)
    sbp=pd.to_numeric(out['systolic_bp_mean'],errors='coerce'); dbp=pd.to_numeric(out['diastolic_bp_mean'],errors='coerce')
    measured=pd.Series(np.where(sbp.notna()|dbp.notna(),((sbp>=SBP_THRESHOLD)|(dbp>=DBP_THRESHOLD)).astype(float),np.nan),index=out.index)
    def yn(col): return pd.to_numeric(out[col],errors='coerce').map({1.0:1.0,2.0:0.0}).astype('float64')
    def or_flags(items):
        z=pd.concat(items,axis=1); a=z.eq(1).any(axis=1); known=z.notna().any(axis=1); r=pd.Series(np.nan,index=out.index,dtype='float64'); r.loc[a]=1.0; r.loc[~a&known]=0.0; return r
    hypertension=or_flags([measured,yn('hypertension_history'),yn('hypertension_treatment')])
    cvd=or_flags([yn(c) for c in ['heart_failure_history','coronary_heart_disease_history','angina_history','heart_attack_history','stroke_history']])
    mins=pd.to_numeric(out['leisure_activity_minutes'],errors='coerce')
    inactive=pd.Series(np.nan,index=out.index,dtype='float64'); inactive.loc[mins.notna()&(mins<=INACTIVITY_MAX_MINUTES)]=1.; inactive.loc[mins.notna()&(mins>INACTIVITY_MAX_MINUTES)]=0.
    ethnicity=pd.Series(np.nan,index=out.index,dtype='float64'); ethnicity.loc[race.notna()]=race.loc[race.notna()].isin(HIGHER_RISK_ETHNICITY_CODES).astype(float)
    risks=pd.concat([hypertension,cvd,inactive,ethnicity],axis=1); count=risks.fillna(0).sum(axis=1).astype(float); count.loc[risks.notna().sum(axis=1)==0]=np.nan
    eligible=pd.Series(np.nan,index=out.index,dtype='float64'); eligible.loc[age>=AGE_THRESHOLD]=1.; younger=age.notna()&(age<AGE_THRESHOLD)&bmi_flag.notna(); eligible.loc[younger&bmi_flag.eq(0)]=0.; eligible.loc[younger&bmi_flag.eq(1)&(count>=1)]=1.; eligible.loc[younger&bmi_flag.eq(1)&count.eq(0)]=0.
    criteria=pd.concat([age_flag,bmi_flag,hypertension,cvd,inactive,ethnicity],axis=1); observed=criteria.notna().sum(axis=1).astype(float); missing=criteria.isna().sum(axis=1).astype(float); priority=criteria.fillna(0).sum(axis=1).astype(float)/observed.replace(0,np.nan)
    vals=[age_flag,bmi_flag,hypertension,cvd,inactive,ethnicity,count,eligible,observed,missing,priority.fillna(0.)]
    for name,val in zip(MANUAL_FEATURES,vals): out[name]=val
    return out

def cdc_ada_risk_score(frame):
    age = pd.to_numeric(frame.get('age_years', pd.Series(dtype='float64')), errors='coerce')
    score = pd.Series(0.0, index=frame.index, dtype='float64')
    score += np.where(age >= 60, 3, np.where(age >= 50, 2, np.where(age >= 40, 1, 0)))
    sex = pd.to_numeric(frame.get('sex_code', pd.Series(dtype='float64')), errors='coerce')
    score += (sex == 1).astype(float)
    bp_hist = pd.to_numeric(frame.get('hypertension_history', pd.Series(dtype='float64')), errors='coerce')
    score += (bp_hist == 1).astype(float)
    minutes = pd.to_numeric(frame.get('leisure_activity_minutes', pd.Series(dtype='float64')), errors='coerce')
    score += (minutes.notna() & (minutes <= INACTIVITY_MAX_MINUTES)).astype(float)
    bmi = pd.to_numeric(frame.get('bmi', pd.Series(dtype='float64')), errors='coerce')
    race = pd.to_numeric(frame.get('race_ethnicity_code', pd.Series(dtype='float64')), errors='coerce')
    overweight_cut = np.where(race == 6, 23.0, 25.0)
    score += np.where(bmi >= 40, 3, np.where(bmi >= 30, 2, np.where(bmi >= overweight_cut, 1, 0)))
    return score

CDC_ADA_UNAVAILABLE_ITEMS = ['gestational_diabetes_history', 'family_diabetes_history']
rule_base='https://w3id.org/clinontoscreen/ontology#'
for rn in ['AgeBasedScreeningRule','YoungerAdultRiskBasedRule']:
    r=URIRef(rule_base+rn)
    assert list(ontology_graph.objects(r,URIRef(rule_base+'hasSource'))), f'{rn} has no source'
    assert list(ontology_graph.objects(r,URIRef(rule_base+'ruleExpression'))), f'{rn} has no expression'
    assert list(ontology_graph.objects(r,URIRef(rule_base+'sectionReference'))), f'{rn} has no section reference'
print('Ontology source, expression and section-reference checks passed.')
