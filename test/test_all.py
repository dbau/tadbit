"""
30 Oct 2012

unittest for pytadbit functions
"""

import unittest
from pytadbit import tadbit, batch_tadbit, Chromosome, load_chromosome
from pytadbit.tad_clustering.tad_cmo import optimal_cmo
from pytadbit.parsers.hic_parser import __check_hic as check_hic
from os import system


class TestTadbit(unittest.TestCase):
    """
    test main tadbit functions
    """
   
    def test_01_tadbit(self):

        global exp1, exp2, exp3, exp4
        exp1 = tadbit('40Kb/chrT/chrT_A.tsv', max_tad_size="auto",
                      verbose=False, no_heuristic=False, n_cpus='max')
        exp2 = tadbit('20Kb/chrT/chrT_B.tsv', max_tad_size="auto",
                      verbose=False, no_heuristic=False, n_cpus='max')
        exp3 = tadbit('20Kb/chrT/chrT_C.tsv', max_tad_size="auto",
                      verbose=False, no_heuristic=False, n_cpus='max')
        exp4 = tadbit('20Kb/chrT/chrT_D.tsv', max_tad_size="auto",
                      n_cpus='max',
                      verbose=False, no_heuristic=False, get_weights=True)

        breaks = [0, 4, 10, 15, 23, 29, 38, 45]
        scores = [8.0, 7.0, 5.0, 7.0, 4.0, 7.0, 7.0, None]
        self.assertEqual(exp1['start'], breaks)
        self.assertEqual(exp1['score'], scores)


    def test_02_batch_tadbit(self):
        global batch_exp
        batch_exp= batch_tadbit('20Kb/chrT/', max_tad_size=20, verbose=False,
                                no_heuristic=True)
        breaks = [0, 4, 9, 15, 20, 29, 36, 44, 50, 62, 67, 76, 90, 95]
        scores = [4.0, 7.0, 3.0, 7.0, 4.0, 4.0, 6.0, 7.0, 10.0, 10.0,
                  8.0, 9.0, 7.0, None]
        self.assertEqual(batch_exp['start'], breaks)
        self.assertEqual(batch_exp['score'], scores)


    def test_03_tad_multi_aligner(self):

        test_chr = Chromosome(name='Test Chromosome',
                              experiment_tads=[exp1, exp2, exp3, exp4],
                              experiment_hic_data=['40Kb/chrT/chrT_A.tsv', '20Kb/chrT/chrT_B.tsv', '20Kb/chrT/chrT_C.tsv', '20Kb/chrT/chrT_D.tsv'],
                              experiment_names=['exp1', 'exp2', 'exp3', 'exp4'],
                              experiment_resolutions=[40000,20000,20000,20000])
        for exp in test_chr.experiments: exp.normalize_hic(method='visibility')

        test_chr.align_experiments(verbose=False, randomize=False,
                                   method='global')
        score1, pval1 = test_chr.align_experiments(verbose=False,method='global',
                                                   randomize=True)
        _, pval2 = test_chr.align_experiments(verbose=False, randomize=True,
                                              rnd_method='shuffle')
        self.assertEqual(round(-26.095, 3), round(score1, 3))
        self.assertEqual(round(0.001, 1), round(pval1, 1))
        self.assertTrue(abs(0.175 - pval2) < 0.2)

                              
    def test_04_chromosome_batch(self):
        test_chr = Chromosome(name='Test Chromosome',
                              experiment_resolutions=[20000]*3,
                              experiment_hic_data=['20Kb/chrT/chrT_A.tsv',
                                                   '20Kb/chrT/chrT_D.tsv',
                                                   '20Kb/chrT/chrT_C.tsv'],
                              experiment_names=['exp1', 'exp2', 'exp3'])
        test_chr.find_tad(['exp1', 'exp2', 'exp3'], batch_mode=True,
                          verbose=False)
        tads = test_chr.get_experiment('batch_exp1_exp2_exp3').tads
        found = [tads[t]['end'] for t in tads if tads[t]['score'] > 0]
        self.assertEqual([3.0, 8.0, 16.0, 21.0, 28.0, 35.0, 43.0,
                          49.0, 61.0, 66.0, 75.0, 89.0, 99.0], found)


    def test_05_save_load(self):
        test_chr = Chromosome(name='Test Chromosome',
                              experiment_tads=[exp1, exp2],
                              experiment_names=['exp1', 'exp2'],
                              experiment_resolutions=[20000,20000])
        test_chr.save_chromosome('lolo', force=True)
        test_chr = load_chromosome('lolo')
        system('rm -f lolo')
        system('rm -f lolo_hic')


    def test_06_tad_clustering(self):
        test_chr = Chromosome(name='Test Chromosome',
                              experiment_tads=[exp4],
                              experiment_names=['exp1'],
                              experiment_hic_data=['20Kb/chrT/chrT_D.tsv'],
                              experiment_resolutions=[20000,20000])
        all_tads = []
        for _, tad in test_chr.iter_tads('exp1'):
            all_tads.append(tad)
        align1, align2, _ = optimal_cmo(all_tads[7], all_tads[10], 7,
                                        method='score')
        self.assertEqual(align1, [0, 1, '-', 2, 3, '-', 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(align2,[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        

    def test_07_forbidden_regions(self):
        test_chr = Chromosome(name='Test Chromosome', max_tad_size=260000)
        test_chr.add_experiment('exp1', 20000, tad_def=exp4,
                                hic_data='20Kb/chrT/chrT_D.tsv')
        brks = [2.0, 7.0, 12.0, 18.0, 49.0,
                61.0, 66.0, 75.0, 89.0, 94.0, 99.0]
        tads = test_chr.experiments['exp1'].tads
        found = [tads[t]['end'] for t in tads if tads[t]['score'] > 0]
        self.assertEqual(brks, found)
        items1 = test_chr.forbidden.keys(), test_chr.forbidden.values()
        test_chr.add_experiment('exp2', 20000, tad_def=exp3,
                                hic_data='20Kb/chrT/chrT_C.tsv')
        items2 = test_chr.forbidden.keys(), test_chr.forbidden.values()
        know1 = ([32, 33, 34, 38, 39, 19, 20, 21, 22,
                  23, 24, 25, 26, 27, 28, 29, 30, 31],
                 [None, None, None, 'Centromere', 'Centromere',
                  None, None, None, None, None, None, None,
                  None, None, None, None, None, None])
        know2 = ([38], ['Centromere'])
        self.assertEqual(items1, know1)
        self.assertEqual(items2, know2)


    def test_08_changing_resolution(self):
        test_chr = Chromosome(name='Test Chromosome', max_tad_size=260000)
        test_chr.add_experiment('exp1', 20000, tad_def=exp4,
                                hic_data='20Kb/chrT/chrT_D.tsv')
        exp = test_chr.experiments['exp1']
        sum20 = sum(exp.hic_data[0])
        exp.set_resolution(80000)
        sum80 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        exp.set_resolution(160000)
        sum160 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        exp.set_resolution(360000)
        sum360 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        exp.set_resolution(2400000)
        sum2400 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        exp.set_resolution(40000)
        sum40 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        exp.set_resolution(20000)
        sum21 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        exp.set_resolution(40000)
        sum41 = sum(exp.hic_data[0])
        check_hic(exp.hic_data[0], exp.size)
        self.assertTrue(sum20 == sum80 == sum160 == sum360 == sum40 \
                        == sum21 == sum2400 == sum41)


    def test_09_hic_normalization(self):
        """
        TODO: check with Davide's script
        """
        test_chr = Chromosome(name='Test Chromosome', max_tad_size=260000)
        test_chr.add_experiment('exp1', 20000, tad_def=exp4,
                                hic_data='20Kb/chrT/chrT_D.tsv')
        exp = test_chr.experiments[0]
        exp.load_experiment('20Kb/chrT/chrT_A.tsv')
        exp.get_hic_zscores()
        exp.get_hic_zscores(zscored=False)


    def test_10_generate_weights(self):
        """
        method names are: 'sqrt' or 'over_tot'
        """
        test_chr = Chromosome(name='Test Chromosome', max_tad_size=260000)
        test_chr.add_experiment('exp1', 20000, tad_def=exp4,
                                hic_data='20Kb/chrT/chrT_D.tsv')
        exp = test_chr.experiments[0]
        tadbit_weigths = exp.norm[:]
        exp.norm = None
        exp.normalize_hic()
        self.assertEqual(tadbit_weigths[0], exp.norm[0])


    def test_11_write_interaction_pairs(self):
        """
        TODO: same as with test 09
        """
        pass


    def test_12_3D_modelling(self):
        """
        quick test to generate 3D coordinates from 3? simple models???
        """
        pass


if __name__ == "__main__":
    unittest.main()
    
