import unittest
import pyasn
from best_asns import get_asn_by_domain


class TestBestASNs(unittest.TestCase):
    def test_get_asn_by_domain(self):
        domain = 'example.com'
        ipasn_db_path = 'data/ipasn_20190425.dat'
        asndb = pyasn.pyasn(ipasn_db_path)
        self.assertEqual(get_asn_by_domain(asndb, domain), 15133)
