"""Automated tests"""
#!/usr/bin/env python

import os
import sys
import doctest
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends 
                                       # doctest_setup, doctest_teardown)

DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
                                                    '..', '..', 
                                                    '..', '..', 
                                                    '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))



class EncounterViewTestCase(unittest.TestCase):
    '''
    Test Health_Encounter module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('health_encounter')

    def test0001views(self):
        '''
        Test views.
        '''
        test_view('health_encounter')

    def test0002depends(self):
        '''
        Test depends.
        '''
        test_depends()

def suite():
    """Test suites"""
    suite = trytond.tests.test_tryton.suite()
    # suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
    #     EncounterViewTestCase))
    suite.addTests(doctest.DocFileSuite('test_encounter.rst',
                                        setUp=None, 
                                        tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
