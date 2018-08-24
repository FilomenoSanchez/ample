"""Test functions for util.ample_util"""
import unittest
from ample.util import reference_manager


class Test(unittest.TestCase):

    def test_construct_references(self):
        #import argparse
        from ample.util import config_util, argparse_util
        options = config_util.AMPLEConfigOptions()
        argso = argparse_util.process_command_line(args=['-mtz', 'foo',
                                                         '-fasta', 'bar'])
        options.populate(argso)
        
        refMgr = reference_manager.ReferenceManager(options.d)
        ref_references = '* Bibby et al. (2012). AMPLE: A cluster-and-truncate approach to solve the crystal structures of small proteins using rapidly computed ab initio models. Acta Crystallogr. Sect. D Biol. Crystallogr. 68(12), 1622-1631. [doi:10.1107/S0907444912039194]\n\n* Winn et al. (2011). Overview of the CCP4 suite and current developments. Acta Crystallographica Section D 67(4), 235-242. [doi:10.1107/S0907444910045749]\n\n* Thomas et al. (2015). Routine phasing of coiled-coil protein crystal structures with AMPLE. IUCrJ 2(2), 198-206. [doi:10.1107/S2052252515002080]\n\n* Simkovic et al. (2016). Residue contacts predicted by evolutionary covariance extend the application of ab initio molecular replacement to larger and more challenging protein folds. IUCrJ 3(4), 259-270. [doi:10.1107/S2052252516008113]\n\n* Bradley et al. (2005). Toward High-Resolution de Novo Structure Prediction for Small Proteins. Science 309(5742), 1868-1871. [doi:10.1126/science.1113801]\n\n* Grosse-Kunstleve et al. (2002). The Computational Crystallography Toolbox: crystallographic algorithms in a reusable software framework. Journal of Applied Crystallography 35(1), 126-136. [doi:10.1107/S0021889801017824]\n\n* Theobald et al. (2006). THESEUS: maximum likelihood superpositioning and analysis of macromolecular structures. Bioinformatics 22(17), 2171-2172. [doi:10.1093/bioinformatics/btl332]\n\n* Krissinel et al. (2012). Enhanced fold recognition using efficient short fragment clustering. Journal of molecular biochemistry 1(2), 76-85. [doi:]\n\n* Zhang et al. (2004). SPICKER: A clustering approach to identify near-native protein folds. Journal of Computational Chemistry 25(6), 865-871. [doi:10.1002/jcc.20011]\n\n* Keegan et al. (2018). Recent developments in MrBUMP: better search-model preparation, graphical interaction with search models, and solution improvement and assessment. Acta Crystallographica Section D 74(3), 167-182. [doi:10.1107/S2059798318003455]\n\n* Murshudov et al. (1997). Refinement of macromolecular structures by the maximum-likelihood method. Acta Crystallogr. Sect. D Biol. Crystallogr. 53(3), 240-255. [doi:10.1107/S0907444996012255]\n\n* Thorn et al. (2013). Extending molecular-replacement solutions with SHELXE. Acta Crystallogr. Sect. D Biol. Crystallogr. 69(11), 2251-2256. [doi:10.1107/S0907444913027534]\n\n* Cohen et al. (2008). ARP/wARP and molecular replacement: the next generation. Acta Crystallogr. Sect. D Biol. Crystallogr. 64(1), 49-60. [doi:10.1107/S0907444907047580]\n\n'
        self.assertEqual(refMgr.citation_list_as_text, ref_references)
        
        options.d['nmr_model_in'] = 'foo'
        options.d['transmembrane'] = True
        options.d['use_scwrl'] = True
        options.d['do_mr'] = False
        refMgr = reference_manager.ReferenceManager(options.d)
        ref_references = '<h3>References</h3><ol><li> Bibby et al. (2012). AMPLE: A cluster-and-truncate approach to solve the crystal structures of small proteins using rapidly computed ab initio models. Acta Crystallogr. Sect. D Biol. Crystallogr. 68(12), 1622-1631. [doi:10.1107/S0907444912039194]</li><li> Winn et al. (2011). Overview of the CCP4 suite and current developments. Acta Crystallographica Section D 67(4), 235-242. [doi:10.1107/S0907444910045749]</li><li> Thomas et al. (2015). Routine phasing of coiled-coil protein crystal structures with AMPLE. IUCrJ 2(2), 198-206. [doi:10.1107/S2052252515002080]</li><li> Simkovic et al. (2016). Residue contacts predicted by evolutionary covariance extend the application of ab initio molecular replacement to larger and more challenging protein folds. IUCrJ 3(4), 259-270. [doi:10.1107/S2052252516008113]</li><li> Bradley et al. (2005). Toward High-Resolution de Novo Structure Prediction for Small Proteins. Science 309(5742), 1868-1871. [doi:10.1126/science.1113801]</li><li> Bibby et al. (2013). Application of the AMPLE cluster-and-truncate approach to NMR structures for molecular replacement. Acta Crystallogr. Sect. D Biol. Crystallogr. 69(11), 2194-2201. [doi:10.1107/S0907444913018453]</li><li> Thomas et al. (2017). Approaches to ab initio molecular replacement of alpha-helical transmembrane proteins. Acta Crystallographica Section D 73(12), 985-996. [doi:10.1107/S2059798317016436]</li><li> Grosse-Kunstleve et al. (2002). The Computational Crystallography Toolbox: crystallographic algorithms in a reusable software framework. Journal of Applied Crystallography 35(1), 126-136. [doi:10.1107/S0021889801017824]</li><li> Theobald et al. (2006). THESEUS: maximum likelihood superpositioning and analysis of macromolecular structures. Bioinformatics 22(17), 2171-2172. [doi:10.1093/bioinformatics/btl332]</li><li> Krissinel et al. (2012). Enhanced fold recognition using efficient short fragment clustering. Journal of molecular biochemistry 1(2), 76-85. [doi:]</li><li> Krivov et al. (2009). Improved prediction of protein side-chain conformations with SCWRL4. Proteins: Struct., Funct., Bioinf. 77(4), 778-795. [doi:10.1002/prot.22488]</li></ol>'
        self.assertEqual(refMgr.citations_as_html, ref_references)

if __name__ == "__main__":
    unittest.main()
