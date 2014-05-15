####### ALL TESTS HERE PROVIDE INPUTS PROPERLY ###########
import unittest
import sys
import numpy as np
from Bio import Seq
from Bio.Alphabet import generic_dna

SRC_CODE = "../src/"  # Path to source code.
sys.path.append(SRC_CODE)
from matrixBuilder import *
from misc import Model


class matrixBuilder_baseClass_tests(unittest.TestCase):
	''' 
		Set of unittests for simple base class functions in matrixBuilder.
		Functions tested here include isTI, orderNucleotidePair. 
		All other functions require full model specification, so they are tested elsewhere.
		Note: stateFreqs specification is required. To test this, all frequencies must be unique!.
	'''
	
	def setUp(self):
		# Do not rely on misc for codons in case something happens to it!
		self.codons = ["AAA", "AAC", "AAG", "AAT", "ACA", "ACC", "ACG", "ACT", "AGA", "AGC", "AGG", "AGT", "ATA", "ATC", "ATG", "ATT", "CAA", "CAC", "CAG", "CAT", "CCA", "CCC", "CCG", "CCT", "CGA", "CGC", "CGG", "CGT", "CTA", "CTC", "CTG", "CTT", "GAA", "GAC", "GAG", "GAT", "GCA", "GCC", "GCG", "GCT", "GGA", "GGC", "GGG", "GGT", "GTA", "GTC", "GTG", "GTT", "TAC", "TAT", "TCA", "TCC", "TCG", "TCT", "TGC", "TGG", "TGT", "TTA", "TTC", "TTG", "TTT"]
		basicModel = Model()
		codonFreqs = [0.01617666, 0.00291771, 0.02664918, 0.02999061, 0.00717921, 0.00700012, 0.01435559, 0.0231568, 0.02403056, 0.00737008, 0.03185765, 0.0193576, 0.03277142, 0.02141258, 0.0127537, 0.00298803, 0.0256333, 0.02312437, 0.01861465, 0.01586447, 0.00373147, 0.02662654, 0.00082524, 0.00048916, 0.01191673, 0.00512658, 0.00050502, 0.01688169, 0.01843001, 0.00215437, 0.02659356, 0.02377742, 0.01169375, 0.00097256, 0.02937344, 0.00268204, 0.01414414, 0.02781933, 0.00070877, 0.02370841, 0.02984617, 0.01828081, 0.01002825, 0.00870788, 0.00728006, 0.02179328, 0.00379049, 0.01978996, 0.00443774, 0.01201798, 0.02030269, 0.01238501, 0.01279963, 0.02094385, 0.02810987, 0.00918507, 0.02880549, 0.0029311, 0.0237658, 0.03194712, 0.06148723]
		basicModel.params = {'stateFreqs': codonFreqs}
		self.baseObject = MatrixBuilder(basicModel)
		self.zero = 1e-8
		
	def test_matrixBuilder_baseClass_isTI(self):	
		''' Test that transitions can be properly identified. '''
				
		self.assertTrue( self.baseObject.isTI('A', 'G'), msg = "matrixBuilder.isTI() does not think A -> G is a transition.")
		self.assertTrue( self.baseObject.isTI('G', 'A'), msg = "matrixBuilder.isTI() does not think G -> A is a transition.")
		self.assertTrue( self.baseObject.isTI('C', 'T'), msg = "matrixBuilder.isTI() does not think C -> T is a transition.")
		self.assertTrue( self.baseObject.isTI('T', 'C'), msg = "matrixBuilder.isTI() does not think C -> T is a transition.")
		self.assertFalse( self.baseObject.isTI('A', 'C'), msg = "matrixBuilder.isTI() mistakenly thinks A -> C is a transition.")
		self.assertFalse( self.baseObject.isTI('C', 'A'), msg = "matrixBuilder.isTI() mistakenly thinks C -> A is a transition.")
		self.assertFalse( self.baseObject.isTI('A', 'T'), msg = "matrixBuilder.isTI() mistakenly thinks A -> T is a transition.")
		self.assertFalse( self.baseObject.isTI('T', 'A'), msg = "matrixBuilder.isTI() mistakenly thinks T -> A is a transition.")
		self.assertFalse( self.baseObject.isTI('G', 'C'), msg = "matrixBuilder.isTI() mistakenly thinks G -> C is a transition.")
		self.assertFalse( self.baseObject.isTI('C', 'G'), msg = "matrixBuilder.isTI() mistakenly thinks C -> G is a transition.")
		self.assertFalse( self.baseObject.isTI('G', 'T'), msg = "matrixBuilder.isTI() mistakenly thinks G -> T is a transition.")
		self.assertFalse( self.baseObject.isTI('T', 'G'), msg = "matrixBuilder.isTI() mistakenly thinks T -> G is a transition.")


	def test_matrixBuilder_baseClass_getCodonFreq(self):
		''' Test that, given a codon, base frequency is properly identified. '''
		for i in range(61):
			codon = self.codons[i]
			correct_freq = self.baseObject.params['stateFreqs'][i]
			self.assertTrue( (abs( self.baseObject.getCodonFreq(codon) - correct_freq ) < self.zero), msg = "codon_MatrixBuilder.getCodonFreq doesn't work properly.")


	def test_matrixBuilder_baseClass_orderNucleotidePair(self):	
		''' Test that nucleotides can properly be ordered. ''' 
		self.assertEqual( self.baseObject.orderNucleotidePair('A', 'G'), 'AG', msg = "matrixBuilder.orderNucleotidePair can't order 'A', 'G' .")
		self.assertEqual( self.baseObject.orderNucleotidePair('G', 'A'), 'AG', msg = "matrixBuilder.orderNucleotidePair can't order 'G', 'A' .")
		self.assertEqual( self.baseObject.orderNucleotidePair('C', 'T'), 'CT', msg = "matrixBuilder.orderNucleotidePair can't order 'C', 'T' .")
		self.assertEqual( self.baseObject.orderNucleotidePair('T', 'C'), 'CT', msg = "matrixBuilder.orderNucleotidePair can't order 'T', 'C' .")
	

	def test_matrixBuilder_baseClass_generalNucDiff(self):
		''' Test that nucleotide differences between codons can be identified properly. '''
		self.assertEqual( self.baseObject.generalNucDiff( 'AAA', 'AAT' ), 'AT',     msg = "matrixBuilder.generalNucDiff can't do one difference." )
		self.assertEqual( self.baseObject.generalNucDiff( 'AAA', 'ATT' ), 'ATAT',   msg = "matrixBuilder.generalNucDiff can't do two differences." )
		self.assertEqual( self.baseObject.generalNucDiff( 'AAA', 'TTT' ), 'ATATAT', msg = "matrixBuilder.generalNucDiff can't do fully distinct." )
		self.assertEqual( self.baseObject.generalNucDiff( 'AAA', 'AAA' ), '',       msg = "matrixBuilder.generalNucDiff can't do same." )
	
	# TO DO - write tests for the functions buildQ and scaleMatrix #
	





class matrixBuilder_codon_MatrixBuilder_tests(unittest.TestCase):
	''' 
		Set of unittests for the codon_MatrixBuilder subclass of matrixBuilder.
		Functions tested here include isSyn, getCodonFreq, calcSynProb, calcNonsynProb, calcInstProb.
	'''
	
	def setUp(self):
		# Do not rely on misc for codons in case something happens to it!
		self.codons = ["AAA", "AAC", "AAG", "AAT", "ACA", "ACC", "ACG", "ACT", "AGA", "AGC", "AGG", "AGT", "ATA", "ATC", "ATG", "ATT", "CAA", "CAC", "CAG", "CAT", "CCA", "CCC", "CCG", "CCT", "CGA", "CGC", "CGG", "CGT", "CTA", "CTC", "CTG", "CTT", "GAA", "GAC", "GAG", "GAT", "GCA", "GCC", "GCG", "GCT", "GGA", "GGC", "GGG", "GGT", "GTA", "GTC", "GTG", "GTT", "TAC", "TAT", "TCA", "TCC", "TCG", "TCT", "TGC", "TGG", "TGT", "TTA", "TTC", "TTG", "TTT"]
		self.genetic_code = [["GCA", "GCC", "GCG", "GCT"], ["TGC","TGT"], ["GAC", "GAT"], ["GAA", "GAG"], ["TTC", "TTT"], ["GGA", "GGC", "GGG", "GGT"], ["CAC", "CAT"], ["ATA", "ATC", "ATT"], ["AAA", "AAG"], ["CTA", "CTC", "CTG", "CTT", "TTA", "TTG"], ["ATG"], ["AAC", "AAT"], ["CCA", "CCC", "CCG", "CCT"], ["CAA", "CAG"], ["AGA", "AGG", "CGA", "CGC", "CGG", "CGT"] , ["AGC", "AGT", "TCA", "TCC", "TCG", "TCT"], ["ACA", "ACC", "ACG", "ACT"], ["GTA", "GTC", "GTG", "GTT"], ["TGG"], ["TAC", "TAT"]]
	
		codonFreqs = [0.01617666, 0.00291771, 0.02664918, 0.02999061, 0.00717921, 0.00700012, 0.01435559, 0.0231568, 0.02403056, 0.00737008, 0.03185765, 0.0193576, 0.03277142, 0.02141258, 0.0127537, 0.00298803, 0.0256333, 0.02312437, 0.01861465, 0.01586447, 0.00373147, 0.02662654, 0.00082524, 0.00048916, 0.01191673, 0.00512658, 0.00050502, 0.01688169, 0.01843001, 0.00215437, 0.02659356, 0.02377742, 0.01169375, 0.00097256, 0.02937344, 0.00268204, 0.01414414, 0.02781933, 0.00070877, 0.02370841, 0.02984617, 0.01828081, 0.01002825, 0.00870788, 0.00728006, 0.02179328, 0.00379049, 0.01978996, 0.00443774, 0.01201798, 0.02030269, 0.01238501, 0.01279963, 0.02094385, 0.02810987, 0.00918507, 0.02880549, 0.0029311, 0.0237658, 0.03194712, 0.06148723]
		muCodonParams = {'AG': 4.0, 'CT': 2.0, 'AC': 1.75, 'AT': 1.5, 'CG': 1.56, 'GT': 4.65}
		mycodon = Model()
		mycodon.params = {'stateFreqs': codonFreqs, 'alpha':1.83, 'beta':5.7, 'mu': muCodonParams}
		self.codonMatrix = codon_MatrixBuilder( mycodon )
		self.zero = 1e-8
		
	def test_codon_MatrixBuilder_isSyn(self):	
		''' Test that synonymous vs nonsynymous changes can be properly identified. 
			Assumes that biopython is not broken. This is (theoretically...) a very safe assumption.
		'''
		for source in self.codons:
			for target in self.codons:
				source_aa = str( Seq.Seq(source, generic_dna).translate() )
				target_aa = str( Seq.Seq(target, generic_dna).translate() )
				if source_aa == target_aa:
					self.assertTrue( self.codonMatrix.isSyn(source, target), msg = ("codon_MatrixBuilder.isSyn() does not think", source, " -> ", target, " is synonymous.") )
				else:
					self.assertFalse( self.codonMatrix.isSyn(source, target), msg = ("codon_MatrixBuilder.isSyn() mistakenly thinks", source, " -> ", target, " is synonymous.") )

	def test_codon_MatrixBuilder_calcSynProb(self):
		''' Test that instantaneous substitution probabilities are properly calculated for synonymous codons. 
			For tractability, just test a few synonymous changes.
		'''
		# GCA -> GCT
		correctProb1 =  0.02370841 * 1.5 * 1.83
		self.assertTrue( abs(self.codonMatrix.calcSynProb("GCT", "A", "T") - correctProb1) < self.zero, msg = "codon_MatrixBuiler.calcSynProb can't do GCA -> GCT.")
		# TTT -> TTC
		correctProb2 = 0.0237658 * 2.0 * 1.83
		self.assertTrue( abs(self.codonMatrix.calcSynProb("TTC", "T", "C") - correctProb2) < self.zero, msg = "codon_MatrixBuiler.calcSynProb can't do TTT -> TTC.")
		# CAA -> CAG
		correctProb3 = 0.01861465 * 4.0 * 1.83 
		self.assertTrue( abs(self.codonMatrix.calcSynProb("CAG", "A", "G") - correctProb3) < self.zero, msg = "codon_MatrixBuiler.calcSynProb can't do CAA -> CAG.")
		# CAG -> CAA (reverse of above.)
		correctProb4 = 0.0256333 * 4.0 * 1.83 
		self.assertTrue( abs(self.codonMatrix.calcSynProb("CAA", "A", "G") - correctProb4) < self.zero, msg = "codon_MatrixBuiler.calcSynProb can't do CAG -> CAA.")
	
	
	def test_codon_MatrixBuilder_calcNonsynProb(self):
		''' Test that instantaneous substitution probabilities are properly calculated for nonsynonymous codons. 
			For tractability, just test a few nonsynonymous changes.
		'''
		# TTA -> ATA
		correctProb1 =  0.03277142 * 1.5 * 5.7
		self.assertTrue( abs(self.codonMatrix.calcNonsynProb("ATA", "T", "A") - correctProb1) < self.zero, msg = "codon_MatrixBuiler.calcNonsynProb can't do TTA -> ATA.")
		# CGT -> AGT
		correctProb2 =  0.0193576 * 1.75 * 5.7
		self.assertTrue( abs(self.codonMatrix.calcNonsynProb("AGT", "C", "A") - correctProb2) < self.zero, msg = "codon_MatrixBuiler.calcNonsynProb can't do CGT -> AGT.")
		# TCC -> TGC
		correctProb3 =  0.02810987 * 1.56 * 5.7
		self.assertTrue( abs(self.codonMatrix.calcNonsynProb("TGC", "C", "G") - correctProb3) < self.zero, msg = "codon_MatrixBuiler.calcNonsynProb can't do TCC -> TGC.")
		# TGC -> TCC, reverse of above.
		correctProb4 =  0.01238501 * 1.56 * 5.7
		self.assertTrue( abs(self.codonMatrix.calcNonsynProb("TCC", "G", "C") - correctProb4) < self.zero, msg = "codon_MatrixBuiler.calcNonsynProb can't do TGC -> TCC.")
		
		


	'''
	def test_codon_MatrixBuilder_calcSynProb(self):	
	
	def test_codon_MatrixBuilder_calcNonsynProb(self):	

	def test_codon_MatrixBuilder_calcInstProb(self):	
	'''


if __name__ == '__main__':
	run_tests = unittest.TextTestRunner()
	

	#print "Testing the simple functions in the base class matrixBuilder"
	#test_suite_baseMatrix = unittest.TestLoader().loadTestsFromTestCase(matrixBuilder_baseClass_tests)
	#run_tests.run(test_suite_baseMatrix)
	
	print "Testing codon_MatrixBuilder, a subclass of the parent matrixBuilder"
	test_suite_codonMatrix = unittest.TestLoader().loadTestsFromTestCase(matrixBuilder_codon_MatrixBuilder_tests)
	run_tests.run(test_suite_codonMatrix)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	