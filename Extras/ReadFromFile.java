package de.learnlib.examples.oca;

// Importing the File class
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;
import java.util.concurrent.*;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;


import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;

import de.learnlib.algorithms.lstar.roca.LStarROCA;
import de.learnlib.algorithms.lstar.roca.ROCAExperiment;
import de.learnlib.api.algorithm.MultipleHypothesesLearningAlgorithm;
import de.learnlib.api.oracle.EquivalenceOracle;
import de.learnlib.api.oracle.SingleQueryOracle;
import de.learnlib.datastructure.observationtable.OTUtils;
import de.learnlib.datastructure.observationtable.StratifiedObservationTable;
import de.learnlib.filter.cache.roca.CounterValueHashCacheOracle;
import de.learnlib.filter.statistic.oracle.CounterValueCounterOracle;
import de.learnlib.filter.statistic.oracle.ROCACounterOracle;
import de.learnlib.filter.statistic.oracle.roca.ROCACounterEQOracle;
import de.learnlib.oracle.equivalence.roca.ROCARandomEQOracle;
import de.learnlib.oracle.equivalence.roca.RestrictedAutomatonCounterEQOracle;
import de.learnlib.oracle.equivalence.roca.RestrictedAutomatonROCASimulatorEQOracle;
import de.learnlib.oracle.membership.SimulatorOracle.ROCASimulatorOracle;
import de.learnlib.oracle.membership.roca.CounterValueOracle;
import de.learnlib.util.statistics.SimpleProfiler;
import net.automatalib.automata.oca.DefaultROCA;
import net.automatalib.automata.oca.ROCA;
import net.automatalib.automata.oca.ROCALocation;
import net.automatalib.serialization.dot.GraphDOT;
import net.automatalib.visualization.Visualization;
import net.automatalib.words.Alphabet;
import net.automatalib.words.impl.Alphabets;

/**
 *
 * @Author: Prince Mathew
 * Date: 17-05-2024
 *
 */

public class ReadFromFile {
    static double TTimeElapsed;
    static int TEqQueries;
    static long TLongestCELength;
    static int Trows;
    static int Tcolumns;
    static int TStateNo;

    private void ROCAExample() {
    }

    public static void main(String[] args) throws IOException {
        String inputPath= "./inputs/";
        String outputPath="./ResultsCSV/";
        File folder = new File(inputPath);
        File[] fileList = folder.listFiles();

        if (fileList != null) {
            for (File file : fileList) {
                if (file.isFile()) { // Ensure it's a file and not a directory
                    String filename = file.getName();
                    if(filename.equals(".DS_Store")) {
                        continue;
                    }
                    System.out.println();
                    System.out.println(filename);
                    TTimeElapsed=0;
                    TEqQueries=0;
                    TLongestCELength=0;
                    Trows=0;
                    Tcolumns=0;
                    TStateNo=0;
                    try {
                        // Create f1 object of the file to read data
                        //File f1 = new File("/Users/prince/Desktop/T6/learnlib-learnlib-0.17.0-roca-fork/examples/src/main/java/de/learnlib/examples/oca/test.txt");
                        Scanner dataReader = new Scanner(file);

                        int LangNo=0, index=0;

                        if (dataReader.hasNextLine()) {
                            String fileData = dataReader.nextLine();
                            String[] splitted= fileData.split(" ");
                            LangNo=Integer.valueOf(splitted[0]);
                        }
                        try (FileWriter writer = new FileWriter(outputPath+filename+".csv")) {
                            writer.write("LangName ,  TimeElapsed  , totalEqQueries , LongestCELength, rows, columns, #States"+ System.lineSeparator());
                            AtomicInteger SCounter = new AtomicInteger(0);
                            while (index < LangNo) {
                                // Get the current time
                                LocalTime currentTime = LocalTime.now();

                                // Define a formatter for the time string
                                DateTimeFormatter formatter = DateTimeFormatter.ofPattern("HH:mm:ss");

                                // Format the time as a string
                                String timeString = currentTime.format(formatter);

                                // Print the formatted time
                                System.out.println(timeString);

                                String fileData = dataReader.nextLine();
                                String[] splitted = fileData.split(" ");
                                String LangName = splitted[0];
                                System.out.println(LangName);

                                fileData = dataReader.nextLine();
                                splitted = fileData.split(" ");
                                int NoStates = Integer.valueOf(splitted[0]);
                                //System.out.println(NoStates);


                                fileData = dataReader.nextLine();
                                splitted = fileData.split(" ");
                                int Initial = Integer.valueOf(splitted[0]);
                                //System.out.println(Initial);

                                fileData = dataReader.nextLine();

                                splitted = fileData.split(" ");
                                int finalSize=0;
                                boolean isEmpty = true;
                                for (String s : splitted) {
                                    if (!s.isEmpty()) {
                                        isEmpty = false;
                                        break;
                                    }
                                }
                                if(!isEmpty)
                                    finalSize=splitted.length;
                                int[] FinalStates = new int[finalSize];
                                for (int i = 0; i < finalSize; i++) {

                                    FinalStates[i] = Integer.valueOf(splitted[i]);
                                    //System.out.print(FinalStates[i] + " ");
                                }
                                System.out.println();
                                fileData = dataReader.nextLine();
                                splitted = fileData.split(" ");
                                Character[] Alphabet = new Character[splitted.length];
                                for (int i = 0; i < splitted.length; i++) {
                                    Alphabet[i] = splitted[i].charAt(0);
                                    //System.out.print(Alphabet[i] + " ");
                                }
                                //System.out.println();

                                ArrayList<int[]> Transitions = new ArrayList<>();
                                for (int i = 0; i < Alphabet.length * 2; i++) {
                                    int[] tempTransitions = new int[NoStates * 2];
                                    fileData = dataReader.nextLine();
                                    splitted = fileData.split(" ");
                                    for (int j = 0; j < NoStates * 2; j++) {
                                        tempTransitions[j] = Integer.valueOf(splitted[j]);
                                        //System.out.print(tempTransitions[j] + " ");
                                    }
                                    //System.out.println();
                                    Transitions.add(tempTransitions);
                                }
                                index++;
                                //System.out.println();
                                ROCA<?, Character> target = constructSUL(NoStates, Initial, FinalStates, Alphabet, Transitions);

                                    // Create a ScheduledExecutorService to manage the timeout
                                    ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
                                    // Create an ExecutorService to run the actual task
                                    ExecutorService executor = Executors.newSingleThreadExecutor();

                                    // Define the task you want to run
                                    Runnable task = new Runnable() {
                                        @Override
                                        public void run() {
                                            try {
                                            runExample(writer,LangName, target, target.getAlphabet());
                                            System.out.println("Task completed");
                                            // Increment the counter upon successful completion
                                                SCounter.incrementAndGet();

                                            }
                                            catch (IOException e) {
                                                System.out.println("Task failed");
                                            }
                                        }
                                    };

                                    // Submit the task to the executor
                                    Future<?> future = executor.submit(task);
                                    // Schedule a timeout after 5 minute
                                    scheduler.schedule(new Runnable() {
                                        @Override
                                        public void run() {
                                            if (!future.isDone()) {
                                                System.out.println("TimeOut 5 minutes. Canceling...");
                                                future.cancel(true); // Cancel the task
                                            }
                                        }
                                    }, 5, TimeUnit.MINUTES); // 10 minute timeout

                                    //Block the main thread.
                                    try {
                                        // Optionally wait for the task to complete or be canceled
                                        future.get(5, TimeUnit.MINUTES);

                                    } catch (TimeoutException e) {
                                        System.out.println("Task timed out");
                                        writer.write(LangName + ", TimeOut"+System.lineSeparator());
                                    } catch (CancellationException e) {
                                        System.out.println("Task was canceled");
                                        writer.write(LangName + ", Cancelled"+System.lineSeparator());
                                    } catch (InterruptedException e) {
                                        System.out.println("Task was interrupted");
                                        writer.write(LangName + ", Interrupt"+System.lineSeparator());
                                    } catch (ExecutionException e) {
                                        System.out.println("Task threw an exception: " + e.getMessage());
                                        writer.write(LangName + ", Failed"+System.lineSeparator());
                                    } finally {
                                        // Shutdown the executors
                                        writer.flush();
                                        executor.shutdownNow();
                                        scheduler.shutdownNow();
                                    }
                                try {
                                    if (!scheduler.awaitTermination(1, TimeUnit.MINUTES)) {
                                        System.out.println("Scheduler did not terminate");
                                    }
                                    if (!executor.awaitTermination(1, TimeUnit.MINUTES)) {
                                        System.out.println("Executor did not terminate");
                                    }
                                } catch (InterruptedException e) {
                                    System.out.println("Await termination was interrupted");
                                    Thread.currentThread().interrupt();
                                }


                                System.out.println("Completed " + LangName);
                            }
                            dataReader.close();
                            writer.write(System.lineSeparator());
                            int SuccessCounter= SCounter.get();
                            writer.write(", "+(float)TTimeElapsed/SuccessCounter+", "+ (float)TEqQueries/SuccessCounter+", "+ (float)TLongestCELength/SuccessCounter+", "+ (float)Trows/SuccessCounter+", "+ (float)Tcolumns/SuccessCounter+", "+ (float)TStateNo/SuccessCounter+", "+ SuccessCounter);
                        }
                        catch (IOException e) {
                            System.out.println("Cannot open output file");
                        }
                    } catch (OutOfMemoryError exception) { // FileNotFoundException
                        System.out.println("Unexpected error occurred!");
                        //exception.printStackTrace();
                    }

                }
            }


        } else {
            System.out.println("The specified folder does not exist or is not a directory.");
        }



    }

    private static ROCA<?, Character> constructSUL(int NoStates, int Initial, int[] FinalStates, Character[] Alphabet, ArrayList<int[]> Transitions) {
        // L = {a^n b^m | n is odd and m > n}

        final Alphabet<Character> alphabet = Alphabets.fromArray(Alphabet);
        //Alphabet<Character> alphabet = Alphabets.characters('a', 'b');
        DefaultROCA<Character> roca = new DefaultROCA<>(alphabet);

        List<ROCALocation> locations = new ArrayList<>();
        for(int i=0;i<NoStates;i++){
            if(i==Initial){
                int finalI = i;
                if(Arrays.stream(FinalStates).anyMatch(j -> j == finalI)){
                    locations.add(roca.addInitialLocation(true));
                }
                else{
                    locations.add(roca.addInitialLocation(false));
                }
            }
            else{
                int finalI = i;
                if(Arrays.stream(FinalStates).anyMatch(j -> j == finalI)){
                    locations.add(roca.addLocation(true));
                }
                else{
                    locations.add(roca.addLocation(false));
                }
            }
        }
        //Transitions.get(rowIndex)[columnIndex];
        int locationIndex=0;
        for (ROCALocation start : locations) {
            int symbolIndex=0;
            for (Character symbol : alphabet) {
                ROCALocation target = locations.get(Transitions.get(symbolIndex*2)[locationIndex*2]);
                int counterOperation = Transitions.get(symbolIndex*2)[locationIndex*2+1];
                roca.setSuccessor(start, 0, symbol, counterOperation, target);

                target = locations.get(Transitions.get(symbolIndex*2+1)[locationIndex*2]);
                counterOperation = Transitions.get(symbolIndex*2+1)[locationIndex*2+1];
                roca.setSuccessor(start, 1, symbol, counterOperation, target);
                symbolIndex++;
            }
            locationIndex++;
        }
        return roca;
    }

    private static <I> void runExample(FileWriter writer, String LangName, ROCA<?, I> target, Alphabet<I> alphabet) throws IOException {
        long StartTime = System.nanoTime();
        SingleQueryOracle.SingleQueryOracleROCA<I> sul = new ROCASimulatorOracle<>(target);
        ROCACounterOracle<I> membershipOracle = new ROCACounterOracle<>(sul, "membership queries");

        SingleQueryOracle.SingleQueryCounterValueOracle<I> counterValue = new CounterValueOracle<>(target);
        CounterValueHashCacheOracle<I> counterValueCache = new CounterValueHashCacheOracle<>(counterValue);
        CounterValueCounterOracle<I> counterValueOracle = new CounterValueCounterOracle<>(counterValueCache,
                "counter value queries");

        EquivalenceOracle.ROCAEquivalenceOracle<I> eqOracle = new ROCARandomEQOracle<>(target);
        ROCACounterEQOracle<I> equivalenceOracle = new ROCACounterEQOracle<>(eqOracle, "equivalence queries");

        RestrictedAutomatonROCASimulatorEQOracle<I> resEqOracle = new RestrictedAutomatonROCASimulatorEQOracle<>(target,
                alphabet);
        RestrictedAutomatonCounterEQOracle<I> restrictedEquivalenceOracle = new RestrictedAutomatonCounterEQOracle<>(
                resEqOracle, "partial equivalence queries");

        LStarROCA<I> lstar_roca = new LStarROCA<>(membershipOracle, counterValueOracle, restrictedEquivalenceOracle,
                alphabet);

        ROCAExperiment<I> experiment = new ROCAExperiment<>(lstar_roca, equivalenceOracle, alphabet);
        experiment.setLogModels(false);
        experiment.setProfile(true);

        experiment.run();

        ROCA<?, I> result = experiment.getFinalHypothesis();

        System.out.println("-------------------------------------------------------");
        long endTime = System.nanoTime();

        // Convert the difference to seconds
        double TimeElapsed = (endTime - StartTime)/ 1.0e9;;

        //System.out.println("Lang Name: " + LangName);
        //System.out.println("Total time (Sec): " + TimeElapsed);
        // profiling
        //System.out.println(SimpleProfiler.getResults());



        // learning statistics

        int totalEqQueries=0;
        String temp= String.valueOf(equivalenceOracle.getStatisticalData());
        String lastWord=temp.substring(temp.lastIndexOf(" ")+1);
        totalEqQueries=totalEqQueries+Integer.parseInt(lastWord);
        //System.out.println("Equivalence queries "+lastWord);
        temp= String.valueOf(restrictedEquivalenceOracle.getStatisticalData());
        lastWord=temp.substring(temp.lastIndexOf(" ")+1);
        //System.out.println("Partial Equiv.Queries "+lastWord);
        totalEqQueries=totalEqQueries+Integer.parseInt(lastWord);
        //System.out.println("Total Eq.Queries "+totalEqQueries);

        long LongestCELength=lstar_roca.getLengthOfTheLongestCounterexample();
        //System.out.println("Longest Counter Example Length: "+LongestCELength);
        int rows=lstar_roca.getObservationTable().toClassicObservationTable().numberOfShortPrefixRows();
        //int rows1=lstar_roca.getObservationTable().toClassicObservationTable().numberOfLongPrefixRows();
        //int rows2=lstar_roca.getObservati9onTable().toClassicObservationTable().numberOfRows();
        //System.out.println(rows2+" "+rows+" "+rows1);
        int columns=lstar_roca.getObservationTable().toClassicObservationTable().numberOfSuffixes();
        //System.out.println("Total number of rows: "+rows);
        //System.out.println("Total number of columns: "+columns);
        // model statistics
        //System.out.println("States: " + result.size());
        DecimalFormat df = new DecimalFormat("###.################");
        writer.write(LangName + ", " + df.format(TimeElapsed) + ", " + totalEqQueries + ", "+LongestCELength+", "+rows+", "+columns+", "+result.size()+ System.lineSeparator());
        writer.flush();
        TTimeElapsed+=TimeElapsed;
        TEqQueries+=totalEqQueries;
        TLongestCELength+=LongestCELength;
        Trows+=rows;
        Tcolumns+=columns;
        TStateNo+=result.size();
        //System.out.println("Sigma: " + alphabet.size());


        // show model
        //System.out.println();
        //System.out.println("Model: ");
        //GraphDOT.write(result, System.out); // may throw IOException!

        //Visualization.visualize(result);

        //System.out.println("-------------------------------------------------------");

        //OTUtils.displayHTMLInBrowser(lstar_roca.getObservationTable().toClassicObservationTable());
    }
}
