# Official CDC public-use files. Optional files are logged if not available in a cycle.
CYCLE_CONFIGS = {
    '2017_mar2020': {'label': '2017–March 2020 pre-pandemic', 'base_url': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/', 'prefix': 'P_', 'suffix': ''},
    '2021_2023': {'label': 'August 2021–August 2023', 'base_url': 'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/', 'prefix': '', 'suffix': '_L'},
}
FILE_STEMS = ('DEMO', 'DIQ', 'GHB', 'BMX', 'BPXO', 'BPQ', 'SMQ', 'PAQ', 'MCQ', 'HDL')
ESSENTIAL_STEMS = {'DEMO', 'DIQ', 'GHB', 'BMX'}
FILE_VARIABLES = {
    'DEMO': ['SEQN','RIDAGEYR','RIAGENDR','RIDRETH3','DMDEDUC2','INDFMPIR','WTMECPRP','WTMEC2YR','SDMVSTRA','SDMVPSU'],
    'DIQ': ['SEQN','DIQ010','DIQ160'],
    'GHB': ['SEQN','LBXGH'],
    'BMX': ['SEQN','BMXBMI','BMXWAIST'],
    'BPXO': ['SEQN','BPXOSY1','BPXOSY2','BPXOSY3','BPXOSY4','BPXODI1','BPXODI2','BPXODI3','BPXODI4'],
    'BPQ': ['SEQN','BPQ020','BPQ030','BPQ040A'],
    'SMQ': ['SEQN','SMQ020'],
    'PAQ': ['SEQN','PAQ650','PAQ665','PAD660','PAD675','PAD680','PAD800','PAD820'],
    'MCQ': ['SEQN','MCQ160B','MCQ160C','MCQ160D','MCQ160E','MCQ160F','MCQ300C'],
    'HDL': ['SEQN','LBDHDD'],
}

def read_xpt(url: str, cache_path: Path, timeout: int = 90) -> pd.DataFrame:
    if cache_path.exists():
        return pd.read_sas(cache_path, format='xport', encoding='utf-8')
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(response.content)
    return pd.read_sas(BytesIO(response.content), format='xport', encoding='utf-8')

def load_cycle(cycle: str):
    cfg = CYCLE_CONFIGS[cycle]
    merged, report = None, {'cycle': cycle, 'label': cfg['label'], 'loaded_files': [], 'skipped_files': [], 'missing_variables': {}}
    for stem in FILE_STEMS:
        filename = f"{cfg['prefix']}{stem}{cfg['suffix']}.xpt"
        url = cfg['base_url'] + filename
        try:
            data = read_xpt(url, CACHE_DIR / cycle / filename)
        except Exception as exc:
            if stem in ESSENTIAL_STEMS:
                raise RuntimeError(f'Could not load essential CDC file {url}: {exc}') from exc
            report['skipped_files'].append({'file': filename, 'reason': str(exc)})
            print(f'Optional source skipped: {filename} ({exc})')
            continue
        wanted = FILE_VARIABLES[stem]
        report['missing_variables'][stem] = [c for c in wanted if c not in data.columns]
        data = data[[c for c in wanted if c in data.columns]].copy()
        if 'SEQN' not in data.columns:
            if stem in ESSENTIAL_STEMS:
                raise RuntimeError(f'Essential file {filename} does not contain SEQN')
            report['skipped_files'].append({'file': filename, 'reason': 'SEQN missing'})
            continue
        if merged is None:
            merged = data
        else:
            duplicate = (set(merged.columns) & set(data.columns)) - {'SEQN'}
            if duplicate:
                data = data.drop(columns=list(duplicate))
            merged = merged.merge(data, on='SEQN', how='left', validate='one_to_one')
        report['loaded_files'].append(filename)
    if merged is None:
        raise RuntimeError(f'No data loaded for cycle {cycle}')
    merged['cycle'] = cycle
    report['rows_after_merge'] = int(len(merged))
    return merged, report

def numeric(frame, col):
    if col not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype='float64')
    return pd.to_numeric(frame[col], errors='coerce')

def clean_response(series, invalid=None):
    x = pd.to_numeric(series, errors='coerce').astype('float64')
    for bad in (invalid if invalid is not None else {7,9,77,99,777,999}):
        x = x.mask(x == bad)
    return x

def mean_available(frame, cols):
    usable = [c for c in cols if c in frame.columns]
    if not usable:
        return pd.Series(np.nan, index=frame.index, dtype='float64')
    return frame[usable].apply(pd.to_numeric, errors='coerce').mean(axis=1, skipna=True)

def canonicalize(raw, cycle):
    out = pd.DataFrame(index=raw.index)
    out['SEQN'] = raw['SEQN']
    out['cycle'] = cycle
    out['age_years'] = numeric(raw, 'RIDAGEYR')
    out['sex_code'] = clean_response(raw['RIAGENDR'] if 'RIAGENDR' in raw else pd.Series(np.nan,index=raw.index), invalid=set())
    out['race_ethnicity_code'] = clean_response(raw['RIDRETH3'] if 'RIDRETH3' in raw else pd.Series(np.nan,index=raw.index), invalid=set())
    out['education_code'] = clean_response(raw['DMDEDUC2'] if 'DMDEDUC2' in raw else pd.Series(np.nan,index=raw.index))
    out['income_poverty_ratio'] = numeric(raw, 'INDFMPIR')
    out['bmi'] = numeric(raw, 'BMXBMI')
    out['waist_cm'] = numeric(raw, 'BMXWAIST')
    out['hdl_chol_mgdl'] = numeric(raw, 'LBDHDD')
    out['systolic_bp_mean'] = mean_available(raw, [f'BPXOSY{i}' for i in range(1,5)])
    out['diastolic_bp_mean'] = mean_available(raw, [f'BPXODI{i}' for i in range(1,5)])
    mapping = {
        'BPQ020':'hypertension_history','BPQ040A':'hypertension_treatment','SMQ020':'ever_smoked_100_cigs',
        'MCQ160B':'heart_failure_history','MCQ160C':'coronary_heart_disease_history','MCQ160D':'angina_history',
        'MCQ160E':'heart_attack_history','MCQ160F':'stroke_history'
    }
    for source, target in mapping.items():
        out[target] = clean_response(raw[source] if source in raw else pd.Series(np.nan,index=raw.index))
    # Harmonized leisure-time activity minutes. The two cycles use different instruments, so the
    # yes/no recreation items are unavailable in the later cycle; minutes are harmonized instead.
    special_minutes = {7777,9999,77777,99999}
    if cycle == '2017_mar2020':
        vigorous = clean_response(raw['PAD660'] if 'PAD660' in raw else pd.Series(np.nan,index=raw.index), special_minutes)
        vigorous = vigorous.where(clean_response(raw['PAQ650'] if 'PAQ650' in raw else pd.Series(np.nan,index=raw.index), invalid={7,9}) != 2, 0.0)
        moderate = clean_response(raw['PAD675'] if 'PAD675' in raw else pd.Series(np.nan,index=raw.index), special_minutes)
        moderate = moderate.where(clean_response(raw['PAQ665'] if 'PAQ665' in raw else pd.Series(np.nan,index=raw.index), invalid={7,9}) != 2, 0.0)
    else:
        vigorous = clean_response(raw['PAD820'] if 'PAD820' in raw else pd.Series(np.nan,index=raw.index), special_minutes).fillna(0.0)
        moderate = clean_response(raw['PAD800'] if 'PAD800' in raw else pd.Series(np.nan,index=raw.index), special_minutes).fillna(0.0)
    out['leisure_activity_minutes'] = (vigorous.fillna(0.0) + moderate.fillna(0.0)).where(vigorous.notna() | moderate.notna())
    out['sedentary_minutes'] = clean_response(raw['PAD680'] if 'PAD680' in raw else pd.Series(np.nan,index=raw.index), special_minutes)
    out['reported_diabetes'] = clean_response(raw['DIQ010'] if 'DIQ010' in raw else pd.Series(np.nan,index=raw.index), invalid=set())
    out['reported_prediabetes'] = clean_response(raw['DIQ160'] if 'DIQ160' in raw else pd.Series(np.nan,index=raw.index), invalid=set())
    out['hba1c_percent'] = numeric(raw, 'LBXGH')
    for weight_col in ('WTMECPRP','WTMEC2YR','SDMVSTRA','SDMVPSU'):
        if weight_col in raw.columns:
            out[weight_col.lower()] = numeric(raw, weight_col)
    return out

def make_cohort(frame):
    flow = {'rows_in_file': int(len(frame))}
    x = frame.loc[frame['age_years'] >= 18].copy()
    flow['adults_18_plus'] = int(len(x))
    x = x.loc[x['reported_diabetes'] == 2].copy()
    flow['no_reported_diabetes'] = int(len(x))
    x = x.loc[x['reported_prediabetes'] == 2].copy()
    flow['no_reported_prediabetes'] = int(len(x))
    x = x.loc[x['hba1c_percent'].notna()].copy()
    flow['valid_hba1c'] = int(len(x))
    x['target'] = (x['hba1c_percent'] >= 5.7).astype('int8')
    x['target_diabetes_range'] = (x['hba1c_percent'] >= 6.5).astype('int8')
    flow['screen_positive'] = int(x['target'].sum())
    return x.reset_index(drop=True), flow

historical_raw, historical_report = load_cycle('2017_mar2020')
temporal_raw, temporal_report = load_cycle('2021_2023')
historical, historical_flow = make_cohort(canonicalize(historical_raw, '2017_mar2020'))
temporal_test, temporal_flow = make_cohort(canonicalize(temporal_raw, '2021_2023'))
del historical_raw, temporal_raw

COHORT_FLOW = {'historical': historical_flow, 'temporal_test': temporal_flow}
print('Historical eligible cohort:', len(historical), '| positives:', int(historical['target'].sum()), '| prevalence:', round(float(historical['target'].mean()), 4))
print('Temporal test eligible cohort:', len(temporal_test), '| positives:', int(temporal_test['target'].sum()), '| prevalence:', round(float(temporal_test['target'].mean()), 4))
print('Cohort flow:', json.dumps(COHORT_FLOW, indent=2))
print('Files loaded historical:', historical_report['loaded_files'])
print('Files loaded temporal:', temporal_report['loaded_files'])
if len(historical) < 200 or len(temporal_test) < 100:
    warnings.warn('Cohort is smaller than expected. Inspect codebooks, source availability and exclusions before interpreting metrics.')
if historical['target'].nunique() < 2 or temporal_test['target'].nunique() < 2:
    raise ValueError('Both outcome classes are required in historical and temporal cohorts; inspect the source data and cohort rules.')
