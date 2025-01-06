# Description: This file contains the implementation of the minOCA class which is used to find the minimal OCA for a given DROCA.
# Author: Prince Mathew
# Importing packages
import time
from ctypes import *
import multiprocessing
import dfaminer as DFAM
from collections import deque
from collections import defaultdict

#Classs minOCA
class minOCA:
    #Class Variables
    filePath=""     # Path to store the graphs generated. Create a folder 'Trash' in your working directory
    resultFilePath=""
    inputPath=""
    lang_counter=0
    
    @classmethod
    #Function to set the file paths
    def setFilePaths(cls, inp, trash,output):
        cls.filePath=trash
        cls.inputPath=inp
        cls.resultFilePath=output
        return 
    

    #Constructor Function to initialize the minOCA object
    def __init__(self,langName, noStates, initial, final, alphabet, transitions, modAlph):
        
        
        self.HankelMatrix={}         # Stores the Hankel matrix as a dictionary {(row.column):MembershipValue}
        self.Rows=['ε']              # Stores the row indices
        self.Columns=['ε']           # Stores the column indices
        self.candidateCount=0
        self.Queue=[]
        self.uniqueCounterActions=[]
        self.counterExample='F'
        self.depth=1

        #Input
        self.Lang_name=langName
        self.No_States=noStates        # States
        self.Initial=initial          # Initial
        self.Final_States=final   # Final
        self.Alphabet=alphabet # Alphabet
        
        #Transitions with counter actions
        self.Transitions = transitions     
        self.modAlphabet=modAlph

    #For debugging
    def __repr__(self):
        return "Language('{}','{}','{}','{}','{}','{}','{}')".format(self.Lang_name,self.No_States,self.Initial,self.Final_States,self.Alphabet,self.Transitions,self.modAlphabet)

    #For printing - usage: print(LangObject)
    def __str__(self):
        return "Language = '{}'".format(self.Lang_name)



    #Function to return the membership,counter value, modified word and end state corresponding to an input word
    def getMembershipCounter(self, word):
        counter=0
        transitionIndex=0
        state= self.Initial
        modifiedWord=""
        i=0
        if(word=='ε'):
            if(state in self.Final_States):
                return 1,0,word, state
            else:
                return 0,0,word, state

        #If the word is not epsilon

        while(counter>=0 and i<len(word)):
            #print(word[i])
            letterIndex=self.Alphabet.index(word[i])
            #modifiedWord+=word[i]
            #print("letterIndex=",letterIndex)
            if(counter==0):
                transitionIndex= (letterIndex*2)
                modifiedWord+=word[i]
            else:
                transitionIndex= (letterIndex*2)+1
                modifiedWord+=(word[i].upper())
            #print("transitionIndex=",transitionIndex)
            counter+= self.Transitions[transitionIndex][state][1]
            if(counter<0): #Will not be executed if the system is complete
                break
            #print("counter=",counter)
            state= self.Transitions[transitionIndex][state][0]
            #print("state=",state)
            i+=1
        else:
            if(state in self.Final_States):
                return 1, counter, modifiedWord, state
            else:
                return 0, counter, modifiedWord, state
        #print(word)
        return 0,'x','x','x'
        
    #Function that returns the list of counter actions from a given state and counterSign
    def getCounterActions(self,state, counterSign):
        counterActions=[]
        for alphabet in self.Alphabet:
            letterIndex=self.Alphabet.index(alphabet)
            if(counterSign==0):
                transitionIndex= (letterIndex*2)
                counterActions.append(self.Transitions[transitionIndex][state][1])
                counterActions.append('x')
            else:
                transitionIndex= (letterIndex*2)+1
                counterActions.append('x')
                counterActions.append(self.Transitions[transitionIndex][state][1])
        return counterActions

    #Function to check whether a given word over the modified alphabet has a valid run or not
    def IsValidWord(self,word):
        if(word=='ε'):
            return True
        else:
            counter, i=0, 0
            state= self.Initial
            while(i<len(word)):
                #print(word[i],counter)
                letterIndex=self.Alphabet.index(word[i].lower())
                if(counter==0 and word[i].isupper()):
                    return False
                elif(counter==0):
                    transitionIndex= (letterIndex*2)
                elif(counter>0 and word[i].islower()):
                    return False
                else:
                    transitionIndex= (letterIndex*2)+1

                counter+=self.Transitions[transitionIndex][state][1]
                state= self.Transitions[transitionIndex][state][0]
                i+=1
            return True
        
    #Function to fill the table with the given rows and columns
    def FillTable(self):
        for row in self.Rows:
            for entry in self.Columns:
                word=StringConcat(row,entry)
                #print(word)
                if(not (word in self.HankelMatrix)):
                    #Updating Main Table
                    memb, counter, modWord, state= self.getMembershipCounter(word)
                    counterAction= self.getCounterActions(state,SignOfNumber(counter))
                    self.HankelMatrix.update({word:[memb,counterAction,counter,state,modWord]})
                    if(counterAction not in self.uniqueCounterActions):
                        self.uniqueCounterActions.append(counterAction)

                #Updating extensions

                for letter in self.Alphabet:
                    newWord=StringConcat(StringConcat(row,letter),entry)
                    memb, counter, modWord, state= self.getMembershipCounter(newWord)
                    #print("extensions "+modWord)
                    if(not (newWord in self.HankelMatrix)):
                        counterAction= self.getCounterActions(state,SignOfNumber(counter))
                        self.HankelMatrix.update({newWord:[memb,counterAction,counter,state,modWord]})
                        if(counterAction not in self.uniqueCounterActions):
                            self.uniqueCounterActions.append(counterAction)

    #Function to print the current Hankel matrix into a csv file
    def PrintTableToFile(self):

        fp = open(minOCA.filePath+"HankelMatrix_"+str(self.candidateCount)+".csv", "w", encoding="utf-8")
        printed=[]
        #Printing Row Heading
        fp.write("Counter Value, , ")
        for entry in self.Columns:
            fp.write(entry+", a0, a1, b0, b1, ")
        fp.write("Main Table\n")
        #Printing Main Table
        for row in self.Rows:
            fp.write(str(self.HankelMatrix[row][2])+","+row+", ")
            printed.append(row)
            for entry in self.Columns:
                fp.write(str(self.HankelMatrix[StringConcat(row,entry)][0])+", "+str(self.HankelMatrix[StringConcat(row,entry)][1])+", ")
            fp.write("\n")
        fp.write('#,'*(len(self.Columns)*5+2)+"Extensions\n")
        #Printing Extensions
        for row in self.Rows:
            for letter in self.Alphabet:
                newWord=StringConcat(row,letter)
                if(not(newWord in printed)):
                    fp.write(str(self.HankelMatrix[newWord][2])+","+newWord+", ")
                    printed.append(newWord)
                    for entry in self.Columns:
                        fp.write(str(self.HankelMatrix[StringConcat(newWord,entry)][0])+", "+str(self.HankelMatrix[StringConcat(newWord,entry)][1])+", ")
                    fp.write("\n")
        fp.close()
        #Printing the table in terminal
        import pandas as pd
        data = pd.read_csv(minOCA.filePath+"HankelMatrix_"+str(self.candidateCount)+".csv")
        print(data)
        return

    # Function to check whether two rows are equal
    def IsEqual(self,x, y):
        for entry in self.Columns:
            if(self.HankelMatrix[StringConcat(x,entry)][0]!=self.HankelMatrix[StringConcat(y,entry)][0]):
                #print(HankelMatrix[x+entry],HankelMatrix[y+entry])
                return False
            else: #Membership equal
                if(not equalActions(self.HankelMatrix[StringConcat(x,entry)][1],self.HankelMatrix[StringConcat(y,entry)][1])):
                    return False
        return True

    
    # Function to check whether two rows are similar
    def IsSimilar(self,x, y):
        for entry in self.Columns:
            if((self.HankelMatrix[StringConcat(x,entry)][0]=='x' or self.HankelMatrix[StringConcat(y,entry)][0]=='x')):
                continue
            elif(self.HankelMatrix[StringConcat(x,entry)][0]!=self.HankelMatrix[StringConcat(y,entry)][0]):
                #print(HankelMatrix[x+entry],HankelMatrix[y+entry])
                return False
            else: #Membership equal
                if(not similarActions(self.HankelMatrix[StringConcat(x,entry)][1],self.HankelMatrix[StringConcat(y,entry)][1])):
                    return False
        return True

    #Function to check whether the observation table is depth-closed
    def IsClosed(self):
        for extension in self.Rows:
            for letter in self.Alphabet:
                word=StringConcat(extension,letter)
                if(self.HankelMatrix[word][2]<=self.depth):
                    for entry in self.Rows:
                        #check for a similar row above
                        if((self.HankelMatrix[word][2]==self.HankelMatrix[entry][2])):  #Same counter value
                            if(self.IsEqual(word, entry)): #(HankelMatrix[word][2])>2 and 
                                break
                    else: #No equal row with same counter value
                        #print(word)
                        return False
        return True

    #Function to make the observation table depth-closed
    def MakeClosed(self):
        while(not self.IsClosed()):
            for extension in self.Rows:
                #print("word ",extension)
                for letter in self.Alphabet:
                    word=StringConcat(extension,letter)
                    #print("extension ",word)
                    if(self.HankelMatrix[word][2]<=self.depth):
                        for entry in self.Rows:
                            #check for a similar row above
                            if((self.HankelMatrix[word][2]==self.HankelMatrix[entry][2])): 
                                if(self.IsEqual(word, entry)): 
                                    #print("similar ", word, entry,HankelMatrix[word][2],HankelMatrix[entry][2])
                                    break
                        else:
                            #print("Adding ",word)
                            self.Rows.append(word)
                            self.FillTable()  

            return
        
    #Function to check whether the observation table is depth-consistent. i.e., similar rows have similar extensions
    def IsConsistent(self):
        for entry in self.Rows:
            if(self.HankelMatrix[entry][2]<=self.depth):
                for similar in self.Rows:
                        #check for same counter value
                        if((self.HankelMatrix[similar][2]==self.HankelMatrix[entry][2])):
                            if(self.IsEqual(entry,similar)):
                                for letter in self.Alphabet:
                                    #Need not consider invalid runs because they satisfy these conditions trivially
                                    if(not self.IsEqual(StringConcat(entry,letter),StringConcat(similar,letter))):
                                        #print("Not consistent: "+entry+" similar to "+ similar+" but "+StringConcat(entry,letter)+" not similar to "+StringConcat(similar,letter))
                                        return False
        return True

    #Function to make the observation table depth-consistent. i.e., similar rows have similar extensions
    def MakeConsistent(self):
        while(not self.IsConsistent()):
            self.MakeOneConsistent()
        return

    #Function to rectify the first inconsistency encountered
    def MakeOneConsistent(self):
        for entry in self.Rows:
            if(self.HankelMatrix[entry][2]<=self.depth):
                for similar in self.Rows:
                        #check for same counter value
                        if((self.HankelMatrix[similar][2]==self.HankelMatrix[entry][2])):
                            if(self.IsEqual(entry,similar)):
                                for letter in self.Alphabet:
                                    
                                    x=StringConcat(entry,letter)
                                    y=StringConcat(similar,letter)
                                    
                                    for col in self.Columns:
                                        #Membership different
                                        if(self.HankelMatrix[StringConcat(x,col)][0]!=self.HankelMatrix[StringConcat(y,col)][0]):
                                            if(not(StringConcat(letter,col) in self.Columns)):
                                                #print("1Adding "+StringConcat(letter,col)+" to Columns ", entry, similar)
                                                self.Columns.append(StringConcat(letter,col))
                                                self.FillTable()
                                                return 

                                        else: #Membership equal
                                            if(not equalActions(self.HankelMatrix[StringConcat(x,col)][1],self.HankelMatrix[StringConcat(y,col)][1])):
                                                if(not(StringConcat(letter,col) in self.Columns)):
                                                    #print("2Adding "+StringConcat(letter,col)+" to Columns ",entry, similar)
                                                    self.Columns.append(StringConcat(letter,col))
                                                    self.FillTable()
                                                    return
        return

    #Helper function to add all the prefixes of a given counter example to Rows
    def AddAllValidPrefixes(self,CounterExample):
        word=''
        for letter in CounterExample:
            word+=letter
            if(not(word in self.Rows)):
                #print("Adding "+word+" to Rows")
                self.Rows.append(word)
            #print(CounterAction, letter)
        self.FillTable()
        return
    
    #Function to check equivalence
    def NewExactEquivalenceTest(self, my_dfa, result_queue):

        Final_States= my_dfa.final_states 
        Init_State= my_dfa.init_states.pop()
        Transitions=[]  
        No_States= my_dfa.num_states
        #print(No_States,self.No_States)
        depth= pow(self.No_States*No_States,2)
        length_bound= (self.No_States+No_States)*pow(self.No_States*No_States,2)

        #Keeping track of counter actions from each state
        TransitionDict=dict()  

        # Precompute indices to avoid repeated calls to `.index`
        # Convert each action (list) to a tuple
        uniqueCounterActionsIndices = {tuple(action): i for i, action in enumerate(self.uniqueCounterActions)}
        modAlphabetIndices = {letter: i for i, letter in enumerate(self.modAlphabet)}
        alphabetIndices = {letter: i for i, letter in enumerate(self.Alphabet)}

        # Initialise TransitionDict as a defaultdict for efficient updates
        TransitionDict = defaultdict(list)

        for state in range(my_dfa.num_states):
            for action, letterIndex in uniqueCounterActionsIndices.items():
                tempDest = my_dfa.runState(state, [len(self.modAlphabet) + letterIndex])
                if tempDest in my_dfa.final_states:
                    counterSign = 0 if action[0] != 'x' else 1

                    for letter in self.Alphabet:
                        lowerLetterIndex = alphabetIndices[letter]
                        if counterSign == 0:
                            if (state, letter) not in TransitionDict:
                                destState = my_dfa.runState(state, [modAlphabetIndices[letter]])
                                TransitionDict[(state, letter)] = [destState, action[lowerLetterIndex * 2]]
                        else:
                            upperLetter = letter.upper()
                            if (state, upperLetter) not in TransitionDict:
                                destState = my_dfa.runState(state, [modAlphabetIndices[upperLetter]])
                                TransitionDict[(state, upperLetter)] = [destState, action[lowerLetterIndex * 2 + 1]]
        
        for letter in self.Alphabet:
            for i in range(2):
                tempTrans=[]
                alph=letter
                if(i!=0):
                    alph= letter.upper()
                for state in range(No_States):                  
                    if((state,alph) in TransitionDict.keys()):
                        tempTrans.append(TransitionDict[(state,alph)])
                    else:
                        tempTrans.append([0,0]) #No transitions defined yet. add transition to initial state with counter action 0
                Transitions.append(tempTrans)

        
        queue = deque()  # Use deque for O(1) append and pop from the left
        added = set()    # Use a set for fast lookups (O(1) average case)
        word = ''
        queue.append((word, 0, Init_State, 0, 0))  # word, state1, state2, counter value, word length
        added.add((0, Init_State, 0))

        while queue:
            configPair = queue.popleft()  # Dequeue 
            state1, state2, counter, word_length = configPair[1], configPair[2], configPair[3], configPair[4]

            # Check the condition for equivalence
            if ((state1 in self.Final_States and state2 not in Final_States) or 
                (state1 not in self.Final_States and state2 in Final_States)):
                result_queue.put([configPair[0], 0, 0])  # word
                return

            for letter in self.Alphabet:
                modLetter = letter.upper()
                letterIndex = self.Alphabet.index(letter)

                # Determine destination states and counter actions
                is_zero = (counter == 0)
                trans_type = letterIndex * 2 if is_zero else letterIndex * 2 + 1

                destState1, countAction1 = self.Transitions[trans_type][state1]
                destState2, countAction2 = Transitions[trans_type][state2]

                if countAction1 != countAction2:  # Different counter values on the same word
                    result_queue.put([configPair[0] + modLetter, 0, 0])
                    return
                else:  # Same counter action
                    new_counter = counter + countAction1
                    new_word_length = word_length + 1
                    if new_counter <= depth and new_word_length < length_bound:
                        new_config = (destState1, destState2, new_counter)
                        if new_config not in added:  # Avoid duplicates
                            queue.append((configPair[0] + modLetter, destState1, destState2, new_counter, new_word_length))
                            added.add(new_config)  # Mark as visited

        # Default result if no conditions are met
        result_queue.put(['T', TransitionDict, Init_State])    
        return

    # Function to Construct automaton from observations using SAT solver            
    def HankelToAutomaton(self,remTime):
        accepting=[]
        rejecting=[]
        #print(HankelMatrix)
        for word in self.HankelMatrix.keys():
            #print(word)
            wordLength=0
            NumberWord=[]
            if(word=='ε'):
                newWord=''
                wordLength=0
            else:
                newWord=self.HankelMatrix[word][4]
                #wordLength=len(newWord)
                for letter in newWord:
                    NumberWord.append(self.modAlphabet.index(letter))
            if(self.HankelMatrix[word][0]==0):
                rejecting.append(NumberWord)
            elif(self.HankelMatrix[word][0]==1):
                accepting.append(NumberWord)
            #print(NumberWord)
            #Adding additional transitions to ensure that only states with similar counter actions are merged
            action= self.HankelMatrix[word][1]
            
            #wordLength+=1
            if(action in self.uniqueCounterActions):
                letterIndex=self.uniqueCounterActions.index(action)
                NumWordCopy=NumberWord[:]
                NumWordCopy.append(len(self.modAlphabet)+letterIndex)
                accepting.append(NumWordCopy)
                for others in self.uniqueCounterActions:
                    if(not similarActions(action, others)):
                        newLetterIndex=self.uniqueCounterActions.index(others)
                        #print(newLetterIndex)
                        NumWordCopy=NumberWord[:]
                        NumWordCopy.append(len(self.modAlphabet)+newLetterIndex)
                        rejecting.append(NumWordCopy)
        #print(accepting)
        #print(rejecting)
        try:
            result_queue = multiprocessing.Queue()
            # Create the process
            alphabetSize= len(self.modAlphabet)+len(self.uniqueCounterActions)
            process = multiprocessing.Process(target=run_find_dfa, args=(accepting, rejecting, alphabetSize, result_queue))
            
            # Start the process
            process.start()

            # Wait for the process to complete within remTime
            process.join(remTime)

            # Check if the process is still alive (i.e., it has not finished)
            if process.is_alive():
                print("Time Out")
                process.terminate()  # Terminate the process
                process.join()  # Ensure the process has terminated
                
            else:
                # Get the result from the queue
                resultSDFA = result_queue.get()
                if(resultSDFA!=None):
                    return resultSDFA

        except RecursionError as e:
            print("Maximum recursion depth exceeded")
        return None 
    
    #Function to remove unnecessary transitions and draw the final automaton and save as dot file.
    def removeTransitions(self,transitionDict,Init_state,final_states,filePath):
        
        #print(transitionDict,Init_state,final_states)
        fp = open(filePath+self.Lang_name+"_Final_Automaton.dot", "w")
        fp.write("digraph automaton {\n")
        fp.write('0 [label="", shape=point];\n')
        fp.write("0 -> q_"+str(Init_state)+";\n")
        stateList=[]
        for (state,alph) in transitionDict.keys():
            dest=transitionDict[(state,alph)]
            #print(state,alph,dest)
            if(alph.islower()):
                fp.write("q_"+str(state)+"->q_"+str(dest[0])+'[label="'+alph+", 0, "+str(dest[1])+'"];\n')
            else:
                fp.write("q_"+str(state)+"->q_"+str(dest[0])+'[label="'+alph.lower()+", +, "+str(dest[1])+'"];\n')
            if(not state in stateList):
                stateList.append(state)
        for state in stateList:
            #Marking states
            if(state in final_states): 
                fp.write("q_"+str(state)+" [shape=doublecircle];\n")
            else:
                fp.write("q_"+str(state)+" [shape=circle];\n")
        fp.write("}")
        fp.close()

        #Display the created automaton
        #Uncomment the following block of code to display the automaton while running the code.
        #Make sure you have graphviz installed in your system.
        '''from graphviz import Source
        path=filePath+self.Lang_name+"_Final_Automaton.dot"
        s= Source.from_file(path)
        s.view()'''
        return

#Function to find minimal seperating DFA using DFAMiner
def run_find_dfa(accepting, rejecting,alphSize, result_queue):
    try:
        miner=DFAM.dfa_miner()
        result_DFA= miner.samples_from_data(accepting,rejecting,alphSize)
        result_queue.put(result_DFA)
        return
    except Exception as e:
        print(f"Task Interrupted: {e}")
        result_queue.put(None)
    
#Function to concat two strings. eg. 'ε'+'abc' = 'abc'
def StringConcat(str1, str2):
    if(str1=='ε'):
        return str2
    elif(str2=='ε'):
        return str1
    else:
        return str1+str2
    
#Function to find the sign of a number, sign is 1 if the number is positive and 0 if it is zero
def SignOfNumber(num):
    if(num>0):
        return 1
    elif(num==0):
        return 0
    else:
        return -1

# Function to check whether the counter actions are equal after reading a word
def equalActions(listA,listB):
    for i in range(len(listA)):
        if(listA[i]!=listB[i]):
            return False
    return True
    
# Function to check whether the counter actions are similar after reading a word
def similarActions(listA,listB):
    for i in range(len(listA)):
        if(listA[i]=='x' or listB[i]=='x'):
            continue
        elif(listA[i]!=listB[i]):
            return False
    return True

#Function to get the configuration graph
def NewGetConfigGraph(No_States, Initial, Final_States, Alphabet, Transitions, depth):
    new_dfa=dict()
    for j in range(depth+1):
        for i in range(No_States):
            state_name=str(j)+'q'+str(i)
            final_flag=False
            if(i in Final_States):
                final_flag=True
            
            temp_transitions=dict()
            for letter in Alphabet:
                letterIndex=Alphabet.index(letter)
                destState=0
                countAction=0
                if(j==0): #Counter value zero
                    destState= Transitions[letterIndex*2][i][0]
                    countAction= Transitions[letterIndex*2][i][1]
                else:             #Positive counter value
                    destState= Transitions[letterIndex*2+1][i][0]
                    countAction= Transitions[letterIndex*2+1][i][1]
                #print(destState,countAction)
                newCounterValue=0
                newLetter=''
                if(countAction==0):
                    newLetter=letter+'0'
                    newCounterValue=j
                elif(countAction==1):
                    newLetter=letter+'+'
                    newCounterValue=j+1
                else:
                    newLetter=letter+'-'
                    newCounterValue=j-1
                if(newCounterValue<=depth):
                    newState=str(newCounterValue)+'q'+str(destState)
                    temp_transitions.update({newLetter:newState})
            new_dfa.update({state_name:(final_flag,temp_transitions)})
    #print(new_dfa)
    return new_dfa

#Function to get the configuration graph upto counter value 'depth' as a dfa over input alphabet {a0,a+,a-,b0,b+,b-}. 
def GetConfigurationGraph(No_States, Initial, Final_States, Alphabet, Transitions, depth):

    queue=[(Initial,0)]
    visited=[]
    new_dfa=dict()
    while(queue):
        config=queue.pop()
        visited.append(config)      #Already visited configurations
        state_name=str(config[1])+'q'+str(config[0])
        #print(state_name)
        final_flag=False
        if(config[0] in Final_States):
            final_flag=True
        #print(final_flag)
        temp_transitions=dict()
        for letter in Alphabet:
            letterIndex=Alphabet.index(letter)
            destState=0
            countAction=0
            if(config[1]==0): #Counter value zero
                destState= Transitions[letterIndex*2][config[0]][0]
                countAction= Transitions[letterIndex*2][config[0]][1]
            else:             #Positive counter value
                destState= Transitions[letterIndex*2+1][config[0]][0]
                countAction= Transitions[letterIndex*2+1][config[0]][1]
            #print(destState,countAction)
            newCounterValue=0
            newLetter=''
            if(countAction==0):
                newLetter=letter+'0'
                newCounterValue=config[1]
            elif(countAction==1):
                newLetter=letter+'+'
                newCounterValue=config[1]+1
            else:
                newLetter=letter+'-'
                newCounterValue=config[1]-1
            if(newCounterValue<=depth):
                newState=str(newCounterValue)+'q'+str(destState)
                temp_transitions.update({newLetter:newState})

                if(not (destState,newCounterValue) in visited):
                    queue.append((destState,newCounterValue))
        new_dfa.update({state_name:(final_flag,temp_transitions)})
    return new_dfa
    
