import sdfa as SDFA
import strunion
import minimiser

from functools import cmp_to_key
import sys
import time



class dfa_miner:

    def __init__(self):
        self.positve_samples = []
        self.negative_samples = []
        self.num_samples = 0
        self.num_letters = 0
        self.has_emptysample= False
        self.accept_empty = False
    
    # need to check whether the DFA accepts odd word
    # or reject some even word
    # a word is even iff all the cylcles in it are even
    # similarly a word is odd iff all the cylces are odd
    # so there are some word that is neither even nor odd
    def verify_conjecture_dfa(self, dfa):
        # we verify by enumerating all possible words
        init = None
        for i in dfa.init_states:
            init = i
            break

        for p in self.positve_samples:
            # print("word: = " + str(p))
            res = dfa.run(init, p)
            # print("label: = " + str( res == strunion.word_type.ACCEPT))
            if res != strunion.word_type.ACCEPT:
                print("ERROR classification: ", p, " Sample value: ", True)
                sys.exit(-1)
        for p in self.negative_samples:
            # print("word: = " + str(p))
            res = dfa.run(init, p)
            # print("label: = " + str( res == strunion.word_type.ACCEPT))
            if res == strunion.word_type.ACCEPT:
                print("ERROR classification: ", p, " Sample value: ", False)
                sys.exit(-1)
        
        #print("DFA verification passed")

    def get_word(self, line_brk):
        # print("break lines: ", list(line_brk), " #", len(line_brk))
        mq = int(line_brk[0])
        num = int(line_brk[1])
        w = [int(i) for i in line_brk[2:(2+ num)]]
        return (mq, w)

    #MinOCA: New function added to initalise miner from data and find DFA
    def samples_from_data(self, accepting, rejecting,alphSize):
        import argparse

        parser = argparse.ArgumentParser(
            description='Mining a minimal DFA consistent with samples')
        parser.add_argument('--file', metavar='path', required=False,
                            help='path to input sample file')
        parser.add_argument('--out', metavar='path', required=False,
                            help='path to output DFA')
        parser.add_argument('--solver', type=str.lower, required=False,
                            choices=minimiser.solver_choices, default="cadical153",
                            help='choose the SAT solver')
        parser.add_argument('--lower', type=int, required=False,
                            default=1,
                            help='the lower bound for the DFA')
        parser.add_argument('--upper', type=int, required=False,
                            default=sys.maxsize,
                            help='the upper bound for the DFA')
        parser.add_argument('--sdfa', action="store_true", required=False,
                            default=False,
                            help='use SDFA for inference')
        parser.add_argument('--nobfs', action="store_true", required=False,
                            default=False,
                            help='disable the constraints for BFS tree')
        parser.add_argument('--safety', action="store_true", required=False,
                            default=False,
                            help='construct safety DFA for solving parity games')
        parser.add_argument('--verify', action="store_true", required=False,
                            default=False,
                            help='verify resultant DFA')
        args = parser.parse_args()
        
        
        self.has_emptysample= True #epsilon is always there in the table
        if([] in accepting):
            self.accept_empty=True
            accepting.remove([])
        else:
            rejecting.remove([])
        self.positve_samples=accepting
        self.negative_samples=rejecting
        self.num_letters=alphSize
        self.num_samples=len(accepting)+len(rejecting)
        self.positve_samples.sort(key=cmp_to_key(strunion.dfa_builder.LEXICOGRAPHIC_ORDER))
        self.negative_samples.sort(key=cmp_to_key(strunion.dfa_builder.LEXICOGRAPHIC_ORDER))



        #print(miner.positve_samples, miner.negative_samples)
        #print("Input alphabet size: ", self.num_letters)
        result_dfa = None
        sdfa = None
        #print("Finding DFA")
        if args.sdfa:
            # create the SDFA
            samples = [ (sample, True) for sample in self.positve_samples]
            samples.extend([(sample, False) for sample in self.negative_samples])
            WORD_ORDER = lambda s1, s2: strunion.dfa_builder.LEXICOGRAPHIC_ORDER(s1[0], s2[0])
            # now we sort them in place
            samples.sort(key=cmp_to_key(WORD_ORDER))
            builder = strunion.dfa_builder()
            for sample in samples:
                builder.add(sample[0], strunion.word_type.ACCEPT 
                            if sample[1] else strunion.word_type.REJECT)
            sdfa = strunion.dfa_builder.build(builder, self.num_letters)
        else:
            # create two regular DFAs
            builder = strunion.dfa_builder()
            # positive examples
            for sample in self.positve_samples:
                builder.add(sample, strunion.word_type.ACCEPT)
            pos_dfa = strunion.dfa_builder.build(builder, self.num_letters)
            #print("# of states in positive DFA: ", pos_dfa.num_states)
            
            
            builder = strunion.dfa_builder()
            
            # negative examples
            #print("Negative samples")
            #print(self.negative_samples)
            for sample in self.negative_samples:
                builder.add(sample, strunion.word_type.ACCEPT)
          
            neg_dfa = strunion.dfa_builder.build(builder, self.num_letters)
            
            #print("# of states in negative DFA: ", neg_dfa.num_states)
            # print(neg_dfa.dot())
            
            sdfa = SDFA.sdfa.combine(pos_dfa, neg_dfa, self.num_letters)
            # print(sdfa.dot())
            
        # handle possible empty sample
        if self.has_emptysample:
            func = lambda x: sdfa.add_final_state(x) if self.accept_empty else sdfa.add_reject_state(x)
            # initial states would not have incoming edges
            for init in sdfa.init_states:
                func(init)
            
        # now minimise
        min = minimiser.sdfa_minimiser()
        result_dfa = min.minimise(input_sdfa=sdfa, sat=args.solver
            , lbound=args.lower, ubound=args.upper, nobfs=args.nobfs, safety=args.safety)
        
        if args.verify:
            self.verify_conjecture_dfa(result_dfa)
        #print("Done")     
        return(result_dfa)
        
        

    # read the competition files
    def read_samples(self, file_name):
        with open(file_name, "r") as f:
            # read line by line
            line_idx = 0
            for line in f:
                line_brk = line.split()
                if len(line_brk) < 2:
                    continue
                elif line_brk[0] == "-1":
                    continue
                elif line_idx <= 0:
                    self.num_samples = int(line_brk[0]) #1
                    self.num_letters = int(line_brk[1]) #2
                else:
                    mq, w = self.get_word(line_brk)
                    #print(mq, w)

                    # special case for empty sample
                    if len(w) == 0:
                        self.has_emptysample = True #3
                        self.accept_empty = (mq == 1) #4
                        continue
                    if mq == 1:
                        self.positve_samples.append(w) #5
                    elif mq == 0:
                        self.negative_samples.append(w) #6
                line_idx += 1

        # now sort them in place
        self.positve_samples.sort(key=cmp_to_key(strunion.dfa_builder.LEXICOGRAPHIC_ORDER))
        self.negative_samples.sort(key=cmp_to_key(strunion.dfa_builder.LEXICOGRAPHIC_ORDER))

# sorted(data, key=cmp_to_key(custom_comparator))
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Mining a minimal DFA consistent with samples')
    parser.add_argument('--file', metavar='path', required=True,
                        help='path to input sample file')
    parser.add_argument('--out', metavar='path', required=True,
                        help='path to output DFA')
    parser.add_argument('--solver', type=str.lower, required=False,
                        choices=minimiser.solver_choices, default="cadical153",
                        help='choose the SAT solver')
    parser.add_argument('--lower', type=int, required=False,
                        default=1,
                        help='the lower bound for the DFA')
    parser.add_argument('--upper', type=int, required=False,
                        default=sys.maxsize,
                        help='the upper bound for the DFA')
    parser.add_argument('--sdfa', action="store_true", required=False,
                        default=False,
                        help='use SDFA for inference')
    parser.add_argument('--nobfs', action="store_true", required=False,
                        default=False,
                        help='disable the constraints for BFS tree')
    parser.add_argument('--safety', action="store_true", required=False,
                        default=False,
                        help='construct safety DFA for solving parity games')
    parser.add_argument('--verify', action="store_true", required=False,
                        default=False,
                        help='verify resultant DFA')
    args = parser.parse_args()
    
    start_time = time.time()
    miner = dfa_miner()
    miner.read_samples(args.file)
    #print(miner.positve_samples, miner.negative_samples)
    #print("Input alphabet size: ", miner.num_letters)
    result_dfa = None
    sdfa = None
    if args.sdfa:
        # create the SDFA
        samples = [ (sample, True) for sample in miner.positve_samples]
        samples.extend([(sample, False) for sample in miner.negative_samples])
        WORD_ORDER = lambda s1, s2: strunion.dfa_builder.LEXICOGRAPHIC_ORDER(s1[0], s2[0])
        # now we sort them in place
        samples.sort(key=cmp_to_key(WORD_ORDER))
        builder = strunion.dfa_builder()
        for sample in samples:
            builder.add(sample[0], strunion.word_type.ACCEPT 
                        if sample[1] else strunion.word_type.REJECT)
        sdfa = strunion.dfa_builder.build(builder, miner.num_letters)
    else:
        # create two regular DFAs
        builder = strunion.dfa_builder()
        # positive examples
        for sample in miner.positve_samples:
            builder.add(sample, strunion.word_type.ACCEPT)
        pos_dfa = strunion.dfa_builder.build(builder, miner.num_letters)
        #print("# of states in positive DFA: ", pos_dfa.num_states)
        
        builder = strunion.dfa_builder()
        # positive examples
        for sample in miner.negative_samples:
            builder.add(sample, strunion.word_type.ACCEPT)
        neg_dfa = strunion.dfa_builder.build(builder, miner.num_letters)
        #print("# of states in negative DFA: ", neg_dfa.num_states)
        # print(neg_dfa.dot())
        
        sdfa = SDFA.sdfa.combine(pos_dfa, neg_dfa, miner.num_letters)
        # print(sdfa.dot())
        
    # handle possible empty sample
    if miner.has_emptysample:
        func = lambda x: sdfa.add_final_state(x) if miner.accept_empty else sdfa.add_reject_state(x)
        # initial states would not have incoming edges
        for init in sdfa.init_states:
            func(init)
        
    # now minimise
    min = minimiser.sdfa_minimiser()
    result_dfa = min.minimise(input_sdfa=sdfa, sat=args.solver
         , lbound=args.lower, ubound=args.upper, nobfs=args.nobfs, safety=args.safety)
    
    if args.verify:
        miner.verify_conjecture_dfa(result_dfa)
        
    #print("Output to " + args.out)
    with open(args.out, "w") as file:
        #print(result_dfa)
        file.write(result_dfa.dot())
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 4)
    #print(f"Elapsed time in miner: {elapsed_time} secs")