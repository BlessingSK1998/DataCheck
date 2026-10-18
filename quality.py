"""Explainable, non-destructive CSV quality checks."""
import io
import json
import numpy as np
import pandas as pd


def load_csv(data, separator=',', encoding='utf-8-sig'):
    # Preserve identifiers, leading zeros, and literal 'NA' category values.
    return pd.read_csv(io.BytesIO(data), sep=separator, encoding=encoding,
                       dtype=str, keep_default_na=False, on_bad_lines='error')


def missing(series):
    return series.isna() | series.astype('string').str.strip().eq('').fillna(False)


def inspect(df):
    columns = []
    issues = []
    for name in df.columns:
        s = df[name]
        absent = missing(s)
        text = s.astype('string')
        valid = text[~absent]
        spaces = int((valid != valid.str.strip()).sum())
        numeric = pd.to_numeric(valid, errors='coerce')
        numeric_count = int(numeric.notna().sum())
        outliers = 0
        nonfinite = 0
        numeric_like = len(valid) > 0 and numeric_count / len(valid) >= .8
        if numeric_like:
            finite = numeric[np.isfinite(numeric)]
            nonfinite = int((numeric.notna() & ~np.isfinite(numeric)).sum())
            if len(finite) >= 4:
                q1, q3 = finite.quantile([.25, .75])
                iqr = q3 - q1
                if iqr > 0:
                    outliers = int(((finite < q1 - 1.5*iqr) | (finite > q3 + 1.5*iqr)).sum())
        folded = valid.str.strip().str.casefold()
        variants = int((pd.DataFrame({'raw': valid, 'key': folded}).groupby('key')['raw'].nunique() > 1).sum())
        row = {'column': str(name), 'missing': int(absent.sum()),
               'missing_pct': round(float(absent.mean()*100), 2) if len(s) else 0,
               'distinct_nonempty': int(valid.nunique()), 'whitespace': spaces,
               'category_variant_groups': variants,
               'numeric_parse_failures': int(numeric.isna().sum()) if numeric_like else 0,
               'nonfinite_numbers': nonfinite, 'potential_outliers': outliers,
               'inferred_type': 'numeric-like' if numeric_like else 'text / mixed'}
        columns.append(row)
        for key, explanation in {
            'missing': 'Blank or whitespace-only cells; decide whether to recover, retain, or impute.',
            'whitespace': 'Leading or trailing spaces may break joins and grouping.',
            'category_variant_groups': 'Values differ only by case or surrounding spaces; review before standardizing.',
            'numeric_parse_failures': 'At least 80% of nonblank values parse as numbers; inspect the remaining values.',
            'nonfinite_numbers': 'Infinite values require review before numerical analysis.',
            'potential_outliers': 'Outside 1.5 × IQR fences; unusual does not mean incorrect.'
        }.items():
            if row[key]:
                issues.append({'column': str(name), 'check': key, 'count': row[key], 'explanation': explanation})
    total = int(df.size)
    blank = sum(c['missing'] for c in columns)
    return {'summary': {'rows': len(df), 'columns': len(df.columns), 'missing_cells': blank,
                        'completeness_pct': round(100*(1-blank/total), 2) if total else None,
                        'duplicate_rows': int(df.duplicated().sum()), 'check_findings': len(issues)},
            'columns': columns, 'issues': issues,
            'methodology': 'Completeness measures blank cells only, not overall quality. Duplicates are exact repeated rows after the first. Outliers use finite values and 1.5×IQR; skipped when IQR=0 or fewer than four finite values. Numeric-like threshold: 80% parseable nonblank values. No domain validity or factual accuracy is established.'}


def clean(df, trim=False, remove_duplicates=False):
    result = df.copy(deep=True)
    log = []
    if trim:
        changed = 0
        for name in result.columns:
            s = result[name]
            if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
                trimmed = s.map(lambda v: v.strip() if isinstance(v, str) else v)
                changed += int((s.fillna('') != trimmed.fillna('')).sum())
                result[name] = trimmed
        log.append({'action': 'trim_surrounding_whitespace', 'cells_changed': changed})
    if remove_duplicates:
        before = len(result)
        result = result.drop_duplicates().reset_index(drop=True)
        log.append({'action': 'remove_exact_duplicate_rows_after_trimming_if_selected', 'rows_removed': before-len(result)})
    return result, log


def safe_csv(df):
    """Escape spreadsheet formulas on export; original dataframe is untouched."""
    safe = df.copy()
    for name in safe.columns:
        safe[name] = safe[name].map(lambda v: "'"+v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v)
    return safe.to_csv(index=False).encode('utf-8-sig')


def report_json(report):
    return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)


STUDENT_SCHEMA = {
    'student_id': {'required': True, 'unique': True},
    'city': {'required': True},
    'weekly_study_hours': {'required': True, 'numeric': True, 'min': 0, 'max': 168},
    'final_score': {'required': True, 'numeric': True, 'min': 0, 'max': 100},
    'internet_access': {'required': True, 'allowed': ['Yes', 'No']},
    'school_type': {'required': True, 'allowed': ['Public', 'Private']},
}


def validate_schema(df, schema=None):
    """Validate exact column names/categories; row positions are 1-based data rows."""
    schema = STUDENT_SCHEMA if schema is None else schema
    findings = []
    def record(column, rule, mask=None):
        positions = [] if mask is None else (np.flatnonzero(mask.to_numpy()) + 1).tolist()
        findings.append({'column': column, 'rule': rule,
                         'count': 1 if mask is None else len(positions),
                         'data_rows_first_20': positions[:20]})
    for column, rules in schema.items():
        if column not in df:
            if rules.get('required'):
                record(column, 'missing_column')
            continue
        s = df[column]
        absent = missing(s)
        if rules.get('required') and absent.any():
            record(column, 'required_value', absent)
        if rules.get('unique'):
            bad = ~absent & s.duplicated(keep=False)
            if bad.any(): record(column, 'unique_value', bad)
        if rules.get('numeric'):
            nums = pd.to_numeric(s, errors='coerce')
            bad = ~absent & (nums.isna() | ~np.isfinite(nums))
            if bad.any(): record(column, 'finite_number', bad)
            valid = ~absent & nums.notna() & np.isfinite(nums)
            for bound, op in [('min', lambda a,b: a < b), ('max', lambda a,b: a > b)]:
                if bound in rules:
                    bad = valid & op(nums, rules[bound])
                    if bad.any(): record(column, f'{bound}_{rules[bound]}', bad)
        if 'allowed' in rules:
            bad = ~absent & ~s.isin(rules['allowed'])
            if bad.any(): record(column, 'allowed_category', bad)
    return findings
