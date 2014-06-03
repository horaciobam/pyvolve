import os
import re
import numpy as np
import random as rn
from Bio import SeqIO

from misc import Genetics


class StateFreqs(object):
    '''Will return frequencies. '''
    def __init__(self, **kwargs):
        self.type       = kwargs.get('type') # Type of frequencies to RETURN to user. Either amino, codon, nuc, posNuc.
        self.by         = kwargs.get('by', self.type) # Type of frequencies to base generation on. If amino, get amino acid freqs and convert to codon freqs, with all synonymous having same frequency. If codon, simply calculate codon frequencies independent of their amino acid. If nucleotide, well, yeah.
        self.debug      = kwargs.get('debug', False) # debug mode. some printing. Can likely be removed once parser and more formal sanity checks are implemented.
        self.savefile   = kwargs.get('savefile', None) # for saving the equilibrium frequencies to a file
        self.constraint = kwargs.get('constraint', 1.0) # Constrain provided amino acids to be a certain percentage of total equilbrium frequencies. This allows for non-zero propensities throughout, but non-preferred will be exceptionally rare. Really only used for ReadFreqs and UserFreqs
        
        self.molecules   = Genetics()
        self.aminoFreqs  = np.zeros(20)
        self.codonFreqs  = np.zeros(61)
        self.nucFreqs    = np.zeros(4)
        self.posNucFreqs = np.zeros([3, 4]) # nucleotide frequencies for each codon position. Needed for some MG94 specifications, possibly more, TBD. 
        self.zero        = 1e-10


    def sanityByType(self):
        ''' Confirm that by and type are compatible, and reassign as needed. 
            RULES:
                1. by=amino      any type
                2. by=codon      any type
                3. by=nuc        types = nuc, pos2Nuc
                4. by=posNuc     type = pos2Nuc
               =============================================              
                1. type=amino    by = codon, amino
                2. type=codon    by = codon, amino
                3. type=nuc      by = codon, amino, nuc
                4. type=posNuc   by = codon, amino, posNuc
        
        '''
        # This case must raise an assertion error.
        if self.type == 'amino' or self.type == 'codon':
            assert(self.by == 'amino' or self.by == 'codon'), "Incompatible by! For amino acid or codon frequencies, calculations must use either amino acids or codons, NOT nucleotides."
        
        # These cases can be more flexible since deal with by,type that are both, in some manner, nucleotide.
        elif self.type == 'nuc' and self.by == 'posNuc':
            if debug:
                print "CAUTION: nucleotide frequencies can only be calculated from nucleotide, amino acid (assumes synonynous have equal frequency), or codon."
                print "Specifying positional nucleotide calculations is meaningless in this case, so I will calculate based on nucleotide frequencies alone."
            self.by = 'nuc'
        elif self.type == 'posNuc' and self.by == 'nuc':
            if debug:
                print "CAUTION: positional nucleotide frequencies can only be calculated from positional nucleotide, amino acid (assumes synonynous have equal frequency), or codon."
                print "Specifying global nucleotide calculations is meaningless in this case, so I will calculate based on positional nucleotide frequencies alone."
            self.by = 'posNuc'
        # womp womp.
        else:
            raise AssertionError("The frequency type is unknown. Big bayah.")        
            
  
    def setCodeLength(self):
        ''' Set the codes and lengths once all, if any, "by" issues are resolved ''' 
        if self.by == 'amino':
            self.code = self.molecules.amino_acids
        elif self.by == 'codon':
            self.code = self.molecules.codons
        elif self.by == 'nuc' or self.by == 'posNuc':
            self.code = self.molecules.nucleotides
        self.size = len(self.code)
        
   
    def unconstrainFreqs(self, freqs):
        ''' This function will allow for some frequency constraints to be lessened.
            FUNCTION MAY BE USED BY USERFREQS AND READFREQS ONLY.
            If the constraint value is 0.95, then the preferred (non-zero frequency) entries should only sum to 0.95.
            The remaining 0.05 will be partitioned equally among the non-preferred (freq = 0) entries.
            Therefore, this function allows for some evolutionary "wiggle room" while still enforcing a strong preference.
            
            NB: MAY NOT BE USED IN CONJUNCTION WITH POSITIONAL NUCLEOTIDE FREQUENCIES.
        '''
        assert (self.type != 'posNuc'), "Frequency constraints cannot be used for positional nucleotide frequencies."
        freqs = np.multiply(freqs, self.constraint)
        assert (self.size > np.count_nonzero(freqs)), "All state frequencies are 0! This is problematic for a wide variety of reasons."
        addToZero = float( (1.0 - self.constraint) / (self.size - np.count_nonzero(freqs)) )
        for i in range(len(freqs)):
            if ( abs(freqs[i] - 0.0) < self.zero):
                freqs[i] = addToZero
        assert( abs( np.sum(freqs) - 1.0) < self.zero), "unconstraining frequencies did not work properly - freqs don't sum to 1."
        return freqs
        
    
    
    ############################# FREQUENCY CONVERSIONS #########################################
    def amino2codon(self):
        ''' Calculate codon frequencies from amino acid frequencies. 
            Assumes assumes equal frequencies for synonymous codons.
        '''
        count = 0
        for codon in self.molecules.codons:
            ind = self.molecules.amino_acids.index(self.molecules.codon_dict[codon])    
            if codon in self.molecules.genetic_code[ind]:
                numsyn = float(len(self.molecules.genetic_code[ind]))
                self.codonFreqs[count] = self.aminoFreqs[ind]/numsyn
            count += 1
        assert( abs(np.sum(self.codonFreqs) - 1.) < self.zero), "Codon state frequencies improperly generated from amino acid frequencies. Do not sum to 1."                 
                
                
    def codon2amino(self):
        ''' Calculate amino acid frequencies from codon frequencies. ''' 
        for a in range(len(self.molecules.amino_acids)):
            codons1 = self.molecules.genetic_code[a]
            for c in codons1:
                ind = self.molecules.codons.index(c)
                self.aminoFreqs[a] += self.codonFreqs[ind]
        assert( abs(np.sum(self.aminoFreqs) - 1.) < self.zero), "Amino acid state frequencies improperly generated from codon frequencies. Do not sum to 1." 
    
    def codon2nuc(self):
        ''' Calculate global nucleotide frequencies from the codon frequencies. ''' 
        self.generate() # This will get us the codon frequencies. Now convert those to nucleotide
        for i in range(61):
            codon_freq = self.codonFreqs[i]
            codon = self.molecules.codons[i]
            for n in range(4):
                nuc =  self.molecules.nucleotides[n]
                nuc_freq = float(codon.count(nuc))/3. # number of that nucleotide in the codon
                if nuc_freq > 0 :
                    self.nucFreqs[n] += codon_freq * nuc_freq
        assert( abs(np.sum(self.nucFreqs) - 1.) < self.zero), "Nucleotide state frequencies improperly generated. Do not sum to 1." 


    def codon2posNuc(self):
        ''' Calculate positional nucleotide frequencies from codon frequencies. '''
        
        for i in range(3):
            count = 0
            for codon in self.molecules.codons:
                if codon[i] == 'A':
                    self.posNucFreqs[i][0] += self.codonFreqs[count]
                elif codon[i] == 'C':
                    self.posNucFreqs[i][1] += self.codonFreqs[count]
                elif codon[i] == 'G':
                    self.posNucFreqs[i][2] += self.codonFreqs[count]
                elif codon[i] == 'T':
                    self.posNucFreqs[i][3] += self.codonFreqs[count]
                count += 1
                
    def amino2posNuc(self):
        ''' Calculate positional nucleotide frequencies from amino acid frequencies.
            Assumes that all codons for a given amino acid have the same frequency.
        '''
        self.amino2codon()
        self.codon2posNuc()
    
    def amino2nuc(self):
        ''' Calculate nucleotide frequencies from amino acid frequencies.
             Assumes that all codons for a given amino acid have the same frequency.
        '''
        self.amino2codon()
        self.codon2nuc()  
        
    def nuc2posNuc(self):
        ''' Calculate positional nucleotide frequencies from nucleotide frequencies.
            NOTE: This function will run when type=posNuc and by=nuc. In this case, it is assumed that all positions are the same.
            In effect, these are just global nucleotide frequencies but put into a positional form (3x4 array).
        '''
        for i in range(3):
            for j in range(4):
                self.posNucFreqs[i][j] = self.nucFreqs[j]
  
    
            
    #####################################################################################   

    def assignFreqs(self, freqs):
        ''' For generate() functions when frequencies are created generally, assign to a specific type with this function. '''
        if self.by == 'codon':
            self.codonFreqs = freqs
        elif self.by == 'amino':
            self.aminoFreqs = freqs
        elif self.by == 'nuc':
            self.nucFreqs = freqs
        elif self.by == 'posNuc':
            self.posNucFreqs = freqs
        else:
            raise AssertionError("I don't know how to calculate state frequencies! I'm quitting.")

    def calcFreqs(self):
        ''' Calculate and return state frequencies.            
            State frequencies are calculated for whatever "by specifies. If "type" is different, convert before returning. 
        '''
        self.sanityByType()
        self.setCodeLength()
       
        freqs = self.generate()
        # Separate assertion needed for positional nucleotide frequencies as this is a 2d array, each row of which sums to 1 (total should sum to 3, but that's irrelevant)
        if self.type == 'posNuc' and self.by == 'posNuc':
            for i in range(3):
                assert (abs(np.sum(freqs[i]) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1." 
        else:
            assert( abs(np.sum(freqs) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1." 
        
        self.assignFreqs(freqs)
        
        if self.type == 'codon':
            if self.by == 'amino':
                self.amino2codon()
            return2user = self.codonFreqs
        
        elif self.type == 'amino':
            if self.by == 'codon':
                self.codon2amino()
            return2user = self.aminoFreqs
        
        elif self.type == 'nuc':
            if self.by == 'codon':
                self.codon2nuc()
            if self.by == 'amino':
                self.amino2nuc()
            return2user = self.nucFreqs
        
        elif self.type == 'posNuc':
            if self.by == 'codon':
                self.codon2posNuc()
            if self.by == 'nuc':
                self.nuc2posNuc()
            if self.by == 'amino':
                self.amino2posNuc()
            return2user = self.posNucFreqs
      
        else:
            raise AssertionError("The final type of frequencies you want must be either amino, codon, nucleotide, or positional nucleotide. I don't know which to calculate, so I'm quitting.")
      
        if self.savefile:
            self.save2file()    
        return return2user    
        
        

    def save2file(self):
        if self.type == 'codon':
            np.savetxt(self.savefile, self.codonFreqs)
        elif self.type == 'amino':
            np.savetxt(self.savefile, self.aminoFreqs)
        elif self.type == 'nuc':
            np.savetxt(self.savefile, self.nucFreqs)
        elif self.type == 'posNuc':
            np.savetxt(self.savefile, self.posNucFreqs)
        else:
            raise AssertionError("This error should seriously NEVER HAPPEN. If it does, someone done broke everything. Please email Stephanie.")



    def freq2dict(self):
        ''' Return a dictionary of frequencies, based on self.type .
            Currently only implemented for codons. (!!!)
        '''
        self.freqDict    = {}  # based on TYPE
        if self.type == 'codon':
            for i in range(len(self.molecules.codons)):
                self.freqDict[self.molecules.codons[i]] = round(self.codonFreqs[i], 10)
        return self.freqDict
            



class EmpiricalFreqs(StateFreqs):
    ''' Return state frequencies for empirical models (ones originally used to develop those models).
        The state frequencies are stored in empiricalMatrices.py
        SUPPORTED:
            1. Amino acid: JTT, WAG, LG
            2. Codon:      ECM(un)rest
            
            NB: scg05 codon model is supported BUT IT DOES NOT HAVE OWN FREQUENCIES.
    '''
    
    def __init__(self, **kwargs):
        super(EmpiricalFreqs, self).__init__(**kwargs)
        try:
            self.empiricalModel = kwargs.get('model', None).lower()
        except KeyError:
            print "Need to specify empirical model to get its freqs."
        

    def calcFreqs(self):    
        ''' Overwrite of parent class function. Such an overwrite will happen only for the EmpiricalFreqs child class, as calculations are not needed.
            We are merely reading from a file to assign state frequencies.
            Currently, we do not support converting these frequencies to a different alphabet
        '''
        import empiricalMatrices as em
        try:
            freqs = eval("em."+self.empiricalModel+"_freqs")
        except:
            print "Couldn't figure out your empirical matrix specification."
            print "Note that we currently support only the following empirical models:"
            print "Amino acid: JTT, WAG, LG."
            print "Codon:      ECM (restricted or unrestricted)."
        return freqs


class EqualFreqs(StateFreqs):
    ''' Return equal state frequencies. 
        NOTE: THIS IS THE DEFAULT BEHAVIOR.
    '''
    
    def __init__(self,     **kwargs):
        super(EqualFreqs, self).__init__(**kwargs)
        
    def generate(self):
        if self.by == 'posNuc' and self.type == 'posNuc':
            freqs = np.zeros([3,4])
            for i in range(3):
                freqs[i] = self.equal_generator()
        else:
            freqs = self.equal_generator()
        return freqs
        
        
    def equal_generator(self):
        freqs = np.array(np.repeat(1./float(self.size), self.size))
        assert( abs(np.sum(freqs) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1."
        return freqs
                    
        
                    
class RandFreqs(StateFreqs):
    ''' Return random state frequencies.
        Will return essentially flat distributions, but with noise.
    '''
    def __init__(self, **kwargs):
        super(RandFreqs, self).__init__(**kwargs)

    def generate(self):
        if self.by == 'posNuc' and self.type == 'posNuc':
            freqs = np.zeros([3,4])
            for i in range(3):
                freqs[i] = self.random_generator()
        else:
            freqs = self.random_generator()
        return freqs
            

    def random_generator(self):
        freqs = np.zeros(self.size)
        max = 2./self.size
        min = 1e-5
        sum = 0.
        for i in range(int(self.size) - 1):
            freq = rn.uniform(min,max)
            while (sum + freq > 1):
                freq = rn.uniform(min,max)
            sum += freq
            freqs[i] = freq
        freqs[-1] = (1.-sum)    
        assert( abs(np.sum(freqs) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1."
        return freqs
    
    
    




class UserFreqs(StateFreqs):
    ''' Assign frequencies based on user input. Assume that if not specified, the frequency is zero. 
        Note that 'by' should correspond to the sort of frequencies that they've entered. 'type' should correspond to what they want at the end.
        For instance, it is possible to provide amino acid frequencies and ultimately obtain codon frequencies (with synonymous treated equally, in this circumstance).
        
        NOTE: UNCONSTRAINING IS POSSIBLE HERE.
    
    '''
    def __init__(self, **kwargs):
        super(UserFreqs, self).__init__(**kwargs)    
        self.givenFreqs = kwargs.get('freqs', {}) # Dictionary of desired frequencies.    
        self.checkBy()


    
    def checkBy(self):
        ''' To make sure that self.by is the same alphabet as provided in the dictionary.
            This function will probably eventually be replaced in a parser/sanity check mechanism.
        '''
        keysize = len( str(self.givenFreqs.keys()[0]) ) # Size of first key. All other keys should be the same size as this one. NOTE THAT IF THIS IS REALLY NOT A STRING, IT WILL BE CAUGHT LATER!! Perhaps/definitely this is inelegant, but I'll deal w/ it later.
        assert(keysize == 1 or keysize == 3), "Bad dictionary keys for userfreqs."
        if keysize == 3:
            self.by == 'codon'
        elif keysize == 1:
            if self.type == 'nuc' or (self.by == 'nuc' and self.type == 'posNuc'):
                self.by == 'nuc'
            else:
                self.by == 'amino' 
        
    def generate_posNuc(self):
        ''' Need separate function for when both self.by and self.type are posNuc, since its dictionary is rather different.
            dictionary: {'A':[pos1, pos2, pos3], 'C':[pos1, pos2, pos3] etc... }
        '''
        freqs = np.zeros([3,4])
        count=0
        for nuc in self.code:
            try:
                tempFreqs = self.givenFreqs[nuc]
            except KeyError:
                print "womp womp. come back to this when sanity checking for parser later!"
            assert type(tempFreqs) is list, "womp womp again! future sanity checking"
            assert len(tempFreqs) == 3, "Silly rabbit, codons have 3 positions"
            freqs[0][count] = tempFreqs[0]
            freqs[1][count] = tempFreqs[1]
            freqs[2][count] = tempFreqs[2]
            count += 1
        for i in range(3):
            assert( abs(np.sum(freqs[1]) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1."     
        return freqs      
        

    
    def generate(self):
        if self.type == 'posNuc' and self.by == 'posNuc':
            freqs = self.generate_posNuc()
        else:
            freqs = np.zeros(self.size)
            for i in range(self.size):
                element = self.code[i]
                if element in self.givenFreqs:
                    freqs[i] = self.givenFreqs[element]
            if self.constraint < 1.0:
                freqs = self.unconstrainFreqs(freqs)
            assert( abs(np.sum(freqs) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1."
        return freqs
       









class ReadFreqs(StateFreqs):
    ''' Retrieve frequencies from a file. Can either do global or specify a particular column/group of columns.
        NOTE: UNCONSTRAINING IS POSSIBLE HERE.
     ''' 
    def __init__(self, **kwargs):
        super(ReadFreqs, self).__init__(**kwargs)
        self.seqfile  = kwargs.get('file', None)   # Can also read frequencies from a sequence file
        self.format   = kwargs.get('format', 'fasta') # Default for that file is fasta
        self.whichCol = kwargs.get('columns', None)     # Which columns we are collecting frequencies from. Default is all columns combined. IF YOU GIVE IT A NUMBER, INDEX AT 0!!!!
        self.seqs     = [] # Sequence records obtained from sequence file
        self.fullSeq  = '' # Single sequence string from which to obtain frequencies
        self.keepDNA  = re.compile(r"[^ACGT]") # DNA regexp for what to keep
        self.keepPROT = re.compile(r"[^ACDEFGHIKLMNPQRSTVWY]") # protein regexp for what to keep
       
        
    def makeSeqList(self):
        ''' Set up sequences and relevent variables for frequency collection. '''
        raw = list(SeqIO.parse(self.seqfile, self.format))
        self.seqs = []
        self.numseq = len(raw)
        self.alnlen = len(raw[0]) # This will only come into play if we're collecting columns.
        for entry in raw:
            self.seqs.append(str(entry.seq))            
 
    
    def processSeqList(self):
        ''' If we want columns, we must get a string of the specific columns we're collecting from.
            Otherwise, we can just turn the whole alignment into a single string.
        '''
        # THIS WHOLE THING NEEDS TO BE SERIOUSLY CLEANED UP WHEN SANITY CHECKING IS IMPLEMENTED!!!!!! #
        if self.by == "codon" or self.by == "posNuc":    
            for seq in self.seqs:
                assert( len(seq) % 3 == 0 ), "Your provided file from which to read state frequencies does not appear to be codon data. Number of columns is not multiple of three."
        
        if self.whichCol:
            for i in range(1, len(self.seqs)):
                assert ( len(self.seqs[i]) == self.alnlen),  "Are you sure this is an alignment? Number of columns differs among sequences."           
            
            # Loop in increments of 3 in these cases
            if self.by == "codon" or self.by == "posNuc":
                for col in self.whichCol:
                    start = col*3
                    for row in self.seqs:
                        self.fullSeq += row[start:start+3]
            else:
                for col in self.whichCol:
                    for row in self.seqs:
                        self.fullSeq += row[col]
        else:
            for entry in self.seqs:
                self.fullSeq += entry
        
        # Uppercase and processing.
        self.fullSeq = self.fullSeq.upper()
        if self.by != 'amino':
            self.fullSeq = re.sub(self.keepDNA, '', self.fullSeq)
        else:
            self.fullSeq = re.sub(self.keepPROT, '', self.fullSeq)
        
        # Quick check to ensure that there are actually sequences to use
        if self.by == 'codon' or self.by == 'posNuc':
            assert( len(self.fullSeq) >=3 ), "No sequences from which to obtain equilibrium frequencies!"
        else:
            assert( len(self.fullSeq) >=1 ), "No sequences from which to obtain equilibrium frequencies!"
        
    
    def generate_nuc_amino(self, freqs, sequence):
        ''' Function for cases when self.by == nuc or self.by == amino '''
        for i in range(0, len(sequence)):
            try:
                ind = self.code.index(sequence[i])
            except:
                raise AssertionError("Your sequences contain non-canonical genetics. Sorry, I'm quitting!")
            freqs[ind]+=1
        return np.divide(freqs, len(sequence))
      
      
    def generate_codon(self, freqs):
        ''' Function for case when self.by == codon ''' 
        for i in range(0, len(self.fullSeq),3):
            codon = self.fullSeq[i:i+3]
            try:
                ind = self.code.index(codon)
            except:
                if codon in self.molecules.stop_codons:
                    if self.debug:
                        print "There are stop codons in your dataset. I will ignore these, but you should double check your sequences if this was unexpected!"
                        continue
                    else:
                        raise AssertionError("There is a non-canonical codon triplet in your sequences. Sorry, I'm quitting!")
            freqs[ind]+=1
        return np.divide(freqs, len(self.fullSeq)/3)
                
      
    def generate_posNuc(self, freqs):
        ''' Function for case when self.by == posNuc and self.type == posNuc '''
        p1 = ''
        p2 = ''
        p3 = ''
        for i in range(0,len(self.fullSeq),3):
            p1 += self.fullSeq[i]
            p2 += self.fullSeq[i+1]
            p3 += self.fullSeq[i+2]
        
        freqs[0] = self.generate_nuc_amino(np.zeros(4), p1)          
        freqs[1] = self.generate_nuc_amino(np.zeros(4), p2)
        freqs[2] = self.generate_nuc_amino(np.zeros(4), p3)
        
        for i in range(3):        
            assert( abs(np.sum(freqs[1]) - 1.) < self.zero), "State frequencies (positional nucleotide) improperly generated. Do not sum to 1."   
        return freqs
        
        
        
        
    def generate(self):
        ''' Crux function extraordinaire! '''
        # Create fullSeq (a single string) for frequency calculations. 
        self.makeSeqList()    
        self.processSeqList()
        
        if self.by == 'posNuc' and self.type == 'posNuc':
            freqs = np.zeros([3,4])
            freqs = self.generate_posNuc(freqs)
        else:
            freqs = np.zeros(self.size)
            if self.by == 'codon':
                freqs = self.generate_codon(freqs)
            elif self.by == 'nuc' or self.by == 'amino':
                freqs = self.generate_nuc_amino(freqs, self.fullSeq) # Note that we provide an attribute as an argument because that function is also used for generate_posNuc, and for that function we will NOT be providing an attribute.
            
            # Note - no constraints for for positional nucleotide frequencies. That would be obscenely unnecessary.
            if self.constraint < 1.0:
                freqs = self.unconstrainFreqs(freqs)
            assert( abs(np.sum(freqs) - 1.) < self.zero), "State frequencies improperly generated. Do not sum to 1."   
        
        return freqs
        
  