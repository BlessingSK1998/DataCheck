"""Small in-memory OOXML fixtures exercise real Excel parsing."""
import io
import unittest
import zipfile
from unittest.mock import patch
from quality import excel_sheets, load_excel, _excel_engine, inspect


def workbook_bytes():
    parts = {
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        '_rels/.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Students" sheetId="1" r:id="rId1"/><sheet name="Other" sheetId="2" r:id="rId2"/></sheets></workbook>',
        'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>',
        'xl/worksheets/sheet1.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>id</t></is></c><c r="B1" t="inlineStr"><is><t>value</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>001</t></is></c><c r="B2" t="inlineStr"><is><t>NA</t></is></c></row><row r="3"><c r="A3" t="inlineStr"><is><t>002</t></is></c></row></sheetData></worksheet>',
        'xl/worksheets/sheet2.xml': '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>score</t></is></c></row><row r="2"><c r="A2"><v>75</v></c></row></sheetData></worksheet>'
    }
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,text in parts.items(): z.writestr(name,text)
    return out.getvalue()


class ExcelTests(unittest.TestCase):
    def test_sheet_names_and_text_identifiers(self):
        data=workbook_bytes()
        self.assertEqual(excel_sheets(data,'test.XLSX'),['Students','Other'])
        df=load_excel(data,'test.xlsx','Students')
        self.assertEqual(df.iloc[0,0],'001')
        self.assertEqual(df.iloc[0,1],'NA')
        self.assertEqual(inspect(df)['summary']['missing_cells'],1)

    def test_sheet_selection(self):
        df=load_excel(workbook_bytes(),'test.xlsx','Other')
        self.assertEqual(df.columns.tolist(),['score'])
        self.assertEqual(df.iloc[0,0],'75')

    def test_bad_workbook_and_missing_sheet(self):
        with self.assertRaises(Exception): excel_sheets(b'not excel','x.xlsx')
        with self.assertRaises(ValueError): load_excel(workbook_bytes(),'x.xlsx','Absent')
        with self.assertRaises(ValueError): _excel_engine('x.xlsm')

    def test_legacy_engine_routing(self):
        with patch('quality.pd.read_excel') as reader:
            load_excel(b'fixture','old.XLS','Data')
            self.assertEqual(reader.call_args.kwargs['engine'],'xlrd')

if __name__=='__main__': unittest.main()
