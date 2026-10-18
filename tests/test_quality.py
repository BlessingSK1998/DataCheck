import unittest
import pandas as pd
from quality import load_csv, inspect, clean, safe_csv, report_json

class QualityTests(unittest.TestCase):
    def test_identifiers_and_missing(self):
        df = load_csv(b'id,value\n001,NA\n002, \n003,\n')
        self.assertEqual(df.iloc[0,0], '001')
        self.assertEqual(inspect(df)['summary']['missing_cells'], 2)

    def test_mixed_outlier_and_variants(self):
        df = pd.DataFrame({'n':['1','2','3','4','5','6','7','1000','oops','inf'], 'city':['Harare',' harare ']*5})
        report = inspect(df)
        self.assertEqual(report['columns'][0]['numeric_parse_failures'], 1)
        self.assertEqual(report['columns'][0]['nonfinite_numbers'], 1)
        self.assertEqual(report['columns'][0]['potential_outliers'], 1)
        self.assertEqual(report['columns'][1]['category_variant_groups'], 1)
        report_json(report)

    def test_clean_is_opt_in_and_non_destructive(self):
        df = pd.DataFrame({'a':[' x','x','x']})
        clean_df, log = clean(df, True, True)
        self.assertEqual(len(clean_df),1)
        self.assertEqual(df.iloc[0,0],' x')
        self.assertEqual(log[1]['rows_removed'],2)
        self.assertTrue(clean(df)[0].equals(df))

    def test_empty_and_constant(self):
        self.assertIsNone(inspect(pd.DataFrame(columns=['x']))['summary']['completeness_pct'])
        self.assertEqual(inspect(pd.DataFrame({'x':['1']*8}))['columns'][0]['potential_outliers'],0)

    def test_formula_export(self):
        df = pd.DataFrame({'x':['=1+1',' @SUM(A1)','001']})
        result = safe_csv(df).decode('utf-8-sig')
        self.assertIn("'=1+1",result)
        self.assertEqual(df.iloc[0,0],'=1+1')


class SchemaTests(unittest.TestCase):
    def test_student_rules(self):
        from quality import validate_schema
        df = pd.DataFrame({'student_id':['01','01'], 'city':['X',''],
            'weekly_study_hours':['169','oops'], 'final_score':['100','inf'],
            'internet_access':['Yes','yes'], 'school_type':['Public','Private']})
        findings = validate_schema(df)
        rules = {(f['column'],f['rule']) for f in findings}
        self.assertIn(('student_id','unique_value'),rules)
        self.assertIn(('weekly_study_hours','max_168'),rules)
        self.assertIn(('final_score','finite_number'),rules)
        self.assertIn(('city','required_value'),rules)
        self.assertIn(('internet_access','allowed_category'),rules)

    def test_missing_columns_and_general_schema(self):
        from quality import validate_schema
        df = pd.DataFrame({'unrelated':['x']})
        self.assertEqual(len(validate_schema(df)),6)
        self.assertEqual(validate_schema(df,{}),[])

    def test_valid_student(self):
        from quality import validate_schema
        df = pd.DataFrame({'student_id':['001'], 'city':['Harare'],
            'weekly_study_hours':['12'], 'final_score':['80'],
            'internet_access':['Yes'], 'school_type':['Public']})
        self.assertEqual(validate_schema(df),[])

    def test_alternate_csv_format(self):
        self.assertEqual(load_csv('id;city\n001;Bremen'.encode(), ';').iloc[0,0], '001')
        self.assertEqual(load_csv('city\nMünchen'.encode('latin-1'), encoding='latin-1').iloc[0,0], 'München')

if __name__ == '__main__':
    unittest.main()
