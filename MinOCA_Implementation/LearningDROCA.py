# Importing packages
import minOCA as Learner
import os
import sys
import datetime
from collections import deque
from ctypes import *
import multiprocessing
import time						
import glob
import random
import string



#program to print a menu and ask the user to choose an option
def print_menu():
    print("Menu:")
    print("1. Run minOCA on a representative sample of Dataset1")
    print("2. Run minOCA on Dataset1")
    print("3. Run minOCA on Dataset2")
    print("4. Run minOCA on the test data in the 'inputs' folder")
    print("5. Run minOCA on some commonly known automata")
    print("6. Generate random DROCA")
    print("7. Enable/Disable drawing of the learnt DROCA")
    print("8. Exit")

def GenerateSamples(Alphabet_size, No_States, max_Count):
    Alphabet=[]
    first='a'
    for i in range(Alphabet_size):
        Alphabet.append(string.ascii_lowercase[i])

    fp= open("./inputs/Input_"+str(Alphabet_size)+"_"+str(No_States),"w")
    Initial=0
    count=0
    fp.write(str(max_Count)+"\n")

    while(count<max_Count):
        
        Final=[]
        for i in range(No_States):
            if(random.randint(0,1)==1):
                Final.append(i)
        
        if(len(Final)==No_States or len(Final)==0): #If all states are final states or not final states then recompute.
            continue
        
        Transitions=[]
        counterSign=0
        for i in range(Alphabet_size*2):
            #fp.write("\n")
            alphList=[]
            for j in range(No_States):
                tempList=[]
                
                
                if(counterSign%2==0):   #Counter value zero
                    dest=random.randint(0,No_States-1)
                    tempList.append(dest)
                    if(dest in Final):
                        tempList.append(random.choice([0])) #incoming transition to final state with '0' test & counter action '0'.
                    else:
                        tempList.append(random.choice([1,0]))

                else:
                    #If all states are final states, then there are no positive transitions (Meaning its a dfa): This case won't happen now.
                    dest=random.choice([i for i in range(0, No_States) if i not in Final]) #positive transitions can go only to non-final states
                    tempList.append(dest)
                    tempList.append(random.choice([1,0,-1]))
                #fp.write(str(tempList[0])+" "+str(tempList[1])+" ")
                alphList.append(tempList)
            Transitions.append(alphList)
            counterSign+=1
        #Check for 'n' reachable states
        reachable=[]            #List to store the set of reachable states

        #Perform config graph search upto counter value (No_States)^2 using BFS.
        configAddedToQueue=[(0,0)]
        queue=[(0,0)]

        while(queue):           
            if(len(reachable)==No_States):
                break
            (state,counter)=queue.pop(0)
            if(not state in reachable):
                reachable.append(state)
            for letter in Alphabet:
                letterIndex=Alphabet.index(letter)
                destState=0
                destCounter=0
                if(counter >0): #Counter >0
                    destState= Transitions[letterIndex*2+1][state][0]
                    destCounter= counter+Transitions[letterIndex*2+1][state][1]
                else:
                    destState= Transitions[letterIndex*2][state][0]
                    destCounter= counter+Transitions[letterIndex*2][state][1]
                if(destCounter<= No_States*No_States and (not (destState,destCounter) in configAddedToQueue)):
                    queue.append((destState,destCounter))
                    configAddedToQueue.append((destState,destCounter))
                    


        if(len(reachable)!= No_States):
            continue                        # Number of reachable states is not No_States.
        #Writing test case to file

        Lang_Name="Language_"+str(count)
        

        fp.write(Lang_Name+"\n")
        fp.write(str(No_States)+"\n")
        fp.write(str(Initial)+"\n")
        for i in Final:
            fp.write(str(i)+" ")
        fp.write("\n")
        
        for alp in Alphabet:
            fp.write(alp+" ")

        #Writing transitions to file
        for i in range(Alphabet_size*2):
            fp.write("\n")
            for j in range(No_States):
                fp.write(str(Transitions[i][j][0])+" "+str(Transitions[i][j][1])+" ")

        count+=1
        fp.write("\n")
    fp.close()

# Function to initialise a DROCA from the input file
def initFromFile(file):
    try:
        #file=minOCA.file
        line=file.readline()
        #print(line)
        word = line.split()
        Lang_name= word[0]

        line=file.readline()
        #print(line)
        word = line.split()
        No_States= int(word[0])
        #print(No_States)

        line=file.readline()
        #print(line)
        word = line.split()
        Initial= int(word[0])
        #print(Initial)

        line=file.readline()
        #print(line)
        word = line.split()
        Final_States=[]
        for state in word:
            if(state[0]=='#'):
                break
            else:
                Final_States.append(int(state))
        #print(Final_States)
                
        line=file.readline()
        #print(line)
        word = line.split()
        Alphabet=[]
        for letter in word:
            if(letter[0]=='#'):
                break
            else:
                Alphabet.append(letter)
        #print(Alphabet)


        Transitions = []

        for i in range(2*len(Alphabet)):
            line=file.readline()
            word = line.split()
            #print (word)
            k=0
            letterTransition=[]
            for j in range(No_States):
                tempList= [int(word[k]), int(word[k+1])]
                letterTransition.append(tempList)
                k+=2
            Transitions.append(letterTransition)
        #print(Transitions)
    except Exception as e:
        print("\nLanguage "+Lang_name+" - Input not in the required format!\n")
        print(e)
    else:
        print("\nLanguage "+Lang_name+" - input read successfully.")
        
        
    modAlphabet=[]
    for letter in Alphabet:
        modAlphabet.append(letter)
        modAlphabet.append(letter.upper())
    #print(modAlphabet)

    return Learner.minOCA(Lang_name,No_States, Initial, Final_States, Alphabet, Transitions, modAlphabet)

#Main Function 
def main_function(file):
    filename=file.split("/")[-1]						# Getting the filename
    print(filename)

    InputFileName=filename
    
    #Initialising Class Variables
    #Language.TimeOut= int(input("Enter the time-out for equivalence query (in minutes): "))

    file = open(Learner.inputPath+InputFileName, 'r')
    fp = open(Learner.resultFilePath+InputFileName+".csv", "w")
    fp.write("Lang_name, Total_time, #Equiv. Queries, LongestCounterExampleLength, |P|, |S|, NoStates, Sat_Time, Time_perSAT, AvgCounter_Example_Length, Total_Equiv_Time, Last_Equiv_Time, MaxNoEquiv, SuccessCount\n")

    #Reading first line - number of languages - from the input file
    try:
        line=file.readline()
        word = line.split()
        no_of_inputs = int(word[0])
    except:
        print("Invalid input!\nThe first line should specify the number of languages present in the input file.")
        exit(0)
    #assert no_of_inputs>0
    lang_counter=0
    colTime,colSat,colEq,colAvgSAT, colAvgCE, colLongCE, colRows,colColumns, colNoStates, colTotalEquiv, colLastEquiv=0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    successCount=0
    maxEquiv=0
    while(lang_counter<no_of_inputs):
        try:
            
            #Function to initialise object
            lang=initFromFile(file)
            lang_counter+=1

            Total_time=0
            Counter_Example_Length=0
            Sat_Time=0
            Equivalence_Count=0
            LongestCounterExLength=0
            Total_Equiv_Time=0
            Last_Equiv_Time=0
            # Get the current time
            current_time =datetime.datetime.now()

            # Format the time as a string
            time_string = current_time.strftime('%H:%M:%S')
            print(time_string)
            begin=time.time()
            
            while(lang.counterExample!='T'):
                lang.FillTable()
                #lang.PrintTableToFile()
                while(not lang.IsClosed() or not lang.IsConsistent()):
                    #PrintTableToFile()
                    closedConsistentFlag=1
                    if(not lang.IsClosed()):
                        #print("not closed")
                        lang.MakeClosed()
                    if(not lang.IsConsistent()):
                        #print("not consistent")
                        #PrintTableToFile()
                        lang.MakeConsistent()
                
                #lang.PrintTableToFile()
                currentTime=time.time()-begin  # Time elapsed
                if(currentTime>=Learner.TimeOut*60):
                    fp.write(lang.Lang_name+", Time Out, "+str(currentTime)+"\n")
                    print("TimeOut")
                    break

                print("Querying SAT solver")
                Sat_begin=time.time()
                remTime=Learner.TimeOut*60-currentTime # Remaining time for execution
                my_dfa=lang.HankelToAutomaton(remTime)
                if(my_dfa==None):   #Sat solver did not succeed
                    fp.write(lang.Lang_name+", SAT Failed\n")
                    print("SAT Failed")
                    fp.flush()
                    break
                Sat_Time+=time.time()-Sat_begin

                print("DFA obtained from SAT solver")
                lang.Queue.clear()
                lang.Queue.append('ε')
                lang.candidateCount+=1
                start_time= time.time()
                lang.counterExample='T'

                print("Starting equivalence check")
                
                # equivalence test

                Equivalence_Count+=1
                result_queue = multiprocessing.Queue()
                # Create the process
                remTime=Learner.TimeOut*60-currentTime
                process = multiprocessing.Process(target=lang.NewExactEquivalenceTest, args=(my_dfa, result_queue))
                
                # Start the process
                Equiv_Start_time=time.time()
                process.start()

                # Wait for the process to complete within remTime
                process.join(remTime)

                # Check if the process is still alive (i.e., it has not finished)
                if process.is_alive():
                    print("Time Out")
                    process.terminate()  # Terminate the process
                    process.join()  # Ensure the process has terminated
                    fp.write(lang.Lang_name+", Time Out, "+str(currentTime)+"\n")
                    break
                else:
                    Last_Equiv_Time=time.time()-Equiv_Start_time
                    Total_Equiv_Time+=Last_Equiv_Time
                    # Get the result from the queue
                    resultEq = result_queue.get()
                    if(resultEq!=None):
                        lang.counterExample,transitionDict,Init_state= resultEq

                        #print("equivalence check done")
                        if(lang.counterExample==''):
                            lang.counterExample='ε'
                        print("Counter-example :",lang.counterExample)
                
                
                        #x=input("Enter something")
                        if(lang.counterExample!='T'):
                            if(len(lang.counterExample)>LongestCounterExLength):
                                LongestCounterExLength=len(lang.counterExample)
                            Counter_Example_Length+=len(lang.counterExample)
                            
                            lang.AddAllValidPrefixes(lang.counterExample.lower())
                        else:  
                            Total_time=time.time()-begin
                            successCount+=1
                            print("Language "+lang.Lang_name+" Learnt Successfully!")
                            avgCounterExLength=0
                            if(Equivalence_Count>1):
                                avgCounterExLength= Counter_Example_Length/(Equivalence_Count-1)
                            stateList=[]
                            for i in transitionDict.keys():
                                if(not i[0] in stateList):
                                    stateList.append(i[0])
                            stateCount=len(stateList)
                            if(Learner.testFlag==1):
                                lang.removeTransitions(transitionDict,Init_state,my_dfa.final_states,Learner.filePath) 
                            
                            fp.write(lang.Lang_name+", "+str(Total_time)+", "+str(Equivalence_Count)+", "+str(LongestCounterExLength)+", "+str(len(lang.Rows))+", "+str(len(lang.Columns))+", "+str(stateCount)+", "+str(Sat_Time)+", "+str(Sat_Time/Equivalence_Count)+", "+str(avgCounterExLength)+", "+str(Total_Equiv_Time)+", "+str(Last_Equiv_Time)+"\n")
                            
                            fp.flush()

                            #For calculating average
                            if(Equivalence_Count>maxEquiv):
                                maxEquiv=Equivalence_Count
                            colTime+=Total_time
                            colSat+=Sat_Time
                            colEq+=Equivalence_Count
                            colAvgSAT+=(Sat_Time/Equivalence_Count)
                            colAvgCE+=avgCounterExLength
                            colLongCE+=LongestCounterExLength
                            colRows+=len(lang.Rows)
                            colColumns+=len(lang.Columns)
                            colNoStates+=stateCount
                            colTotalEquiv+=Total_Equiv_Time
                            colLastEquiv+=Last_Equiv_Time
                        lang.depth+=1
                    else:
                        print("Error in equivalence query")
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Reading next input.")
            fp.write(lang.Lang_name+", Cancelled, "+str(currentTime)+"\n")
        
    fp.write("\n")    
    if(successCount!=0):          #Prevent divide by zero error                                                                                                 
        fp.write("Average, "+str(colTime/successCount)+", "+str(colEq/successCount)+", "+str(colLongCE/successCount)+", "+str(colRows/successCount)+", "+str(colColumns/successCount)+", "+str(colNoStates/successCount)+", "+str(colSat/successCount)+", "+str(colAvgSAT/successCount)+", "+str(colAvgCE/successCount)+", "+str(colTotalEquiv/successCount)+", "+str(colLastEquiv/successCount)+", " +str(maxEquiv)+", "+str(successCount)+"\n")
    else:
        fp.write("Average, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 \n")         
    fp.close()    
    file.close()

# Main Function

if __name__ == "__main__":
    sys.setrecursionlimit(pow(10,8))  #Setting recursion limit to a high value for dfa-identify.

    Learner.filePath='./Trash/'
   
    Learner.resultFilePath='./outputs/'
    Learner.TimeOut=5                                                  #Time-out for Learning
    Learner.testFlag=0 

    while True:
        print_menu()
        choice = input("Please choose an option (1-4): ")
        if choice == '1' or choice=='2' or choice=='3':
            if(choice=='1'):
                Learner.inputPath='./TestCases/Representative_SampleDS1/'
                print("This operation will take approximately 1 hour to complete.")
                confirm= input("Do you want to continue? (y/n): ")
            elif(choice=='2'):
                Learner.inputPath='../Datasets/Dataset1/' 
                print("This operation will take days to complete. Do you want to continue? (y/n): ")
                confirm= input("")
            else:
                Learner.inputPath='../Datasets/Dataset2/' 
                print("This operation will take days to complete. Do you want to continue? (y/n): ")
                confirm= input("")
            if confirm == 'y':
                #print("yes")
                file_list=(glob.glob(Learner.inputPath+"*"))						
                linux_format_list= [path.replace('\\','/') for path in file_list]                                                 
                for file in linux_format_list:
                    main_function(file)
                print("The data corresponding to the learnt DROCAs has been saved in the folder './outputs/'.")
                Learner.testFlag = 0
        elif choice == '4':
            Learner.inputPath='./inputs/'
            file_list=(glob.glob(Learner.inputPath+"*"))					
            linux_format_list= [path.replace('\\','/') for path in file_list]                                                 
            for file in linux_format_list:
                main_function(file)
            print("The data corresponding to the learnt DROCAs has been saved in the folder './outputs/'.")
            Learner.testFlag = 0
        elif choice == '5':
            #minOCA("known", draw_automaton)
            Learner.inputPath='./TestCases/Known/'
            file_list=(glob.glob(Learner.inputPath+"*"))						
            linux_format_list= [path.replace('\\','/') for path in file_list]                                                 
            for file in linux_format_list:
                main_function(file)
            print("The data corresponding to the learnt DROCAs has been saved in the folder './outputs/'.")
            Learner.testFlag = 0
        elif choice == '6':
            Alphabet_size = int(input("Enter the alphabet size: "))
            No_States = int(input("Enter the number of states: "))
            max_Count = int(input("Enter the number of automata to be generated: "))
            print("This operation will delete all contents in the folder './inputs'.")
            confirm = input("Do you want to continue? (y/n): ")
            if confirm == 'y':
                folder = './inputs/'
                for the_file in os.listdir(folder):
                    file_path = os.path.join(folder, the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(e)
                GenerateSamples(Alphabet_size, No_States, max_Count)

                print("Random DROCAs has been generated and saved in the folder './inputs'.")
        elif choice == '7':
            if Learner.testFlag==0:
                print("Enabling this option will write the learnt DROCA as a dot file for the next set of inputs and save it in the folder './Trash/'.")
                print("One can use a graph visualisation software such as Graphviz to view to file as a graph")
                print("This is not recommended when handling large sets of data")
                confirm = input("Do you want to continue? (y/n): ")
                if(confirm == 'y'):
                    Learner.testFlag = 1
            else:
                confirm = input("Do you want to disable drawing of the learnt DROCA? (y/n): ")
                if confirm == 'y':
                    Learner.testFlag = 0

        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

    
