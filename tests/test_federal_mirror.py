import unittest
from scripts.prepare_federal_mirror import extract_record
from scripts.generate_theme_benchmark import COMMENTS, generate_benchmark

class FederalArchiveTests(unittest.TestCase):
    def payload(self,**updates):
        attrs={'docketId':'FAA-2018-1084','commentOnDocumentId':'FAA-2018-1084-0001',
               'comment':'<p>A public comment.</p><p>More detail.</p>','postedDate':'2019-02-13',
               'firstName':'private','email':'private@example.org'}
        attrs.update(updates)
        return {'data':{'id':'FAA-2018-1084-0003','type':'comments','attributes':attrs}}
    def test_only_text_date_and_public_record_id_retained(self):
        r=extract_record(self.payload(),'FAA-2018-1084-0001')
        self.assertEqual(r,{'source_id':'FAA-2018-1084-0003','comment_text':'A public comment. More detail.','hearing_date':'2019-02-13'})
    def test_wrong_parent_withdrawn_restricted_empty_records_excluded(self):
        for update in ({'commentOnDocumentId':'FAA-2018-1084-0002'}, {'docketId':'other'},
                       {'withdrawn':True},{'restrictReason':'restricted'},{'comment':'<p> </p>'}):
            self.assertIsNone(extract_record(self.payload(**update),'FAA-2018-1084-0001'))
    def test_wrong_identifier_rejected(self):
        p=self.payload();p['data']['id']='../private'
        with self.assertRaises(ValueError):extract_record(p,'FAA-2018-1084-0001')

class RichBenchmarkTests(unittest.TestCase):
    def test_planted_categories_are_separate_from_source_text_and_reproducible(self):
        rows=generate_benchmark()
        self.assertEqual(len(rows),1000);self.assertEqual(rows,generate_benchmark())
        self.assertEqual(len({r['hearing_date'] for r in rows}),3)
        self.assertEqual(len({r['respondent_id'] for r in rows}),1000)
    def test_each_category_has_varied_eligible_substantive_sentences(self):
        for texts in COMMENTS.values():
            self.assertEqual(len(texts),len(set(texts)))
            self.assertGreaterEqual(len(texts),3)
            self.assertTrue(all(12<=len(t.split())<=60 for t in texts))
