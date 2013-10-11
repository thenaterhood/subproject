#!/usr/bin/python3
"""
Author: Nate Levesque <public@thenaterhood.com>
File: histogram.py
Language: Python3
Description:
    Provides utilities for generating 
    histograms from dictionaries mapping
    strings to numerical values.

"""
def printHistogram( wordsIn ):
    """
    Prints a generated histogram to the terminal

    Arguments:
        wordsIn (list): a list of tuples

    """
    histogram = generateHistogram( wordsIn )

    r = ""
    for i in histogram:
        print(i)

def histToString( histList ):
    """
    Returns a histogram as one long string 

    Arguments:
        histList (list) a list of histogram lines

    Returns:
        r (str) this histogram as a string
    """
    r = ""
    for i in histList:
        r += i + "\n"

    return r

def generateHistogramPresorted( wordsIn ):
    """
    Generates a histogram of words and their
    frequencies from an ordered list of tuples

    Arguments:
        wordsIn (list): a sorted list of tuples

    Returns:
        histogram (list): a histogram of each word
    """

    histogram = []

    if ( len(wordsIn ) < 1):
        return []

    maxOccurances = int( wordsIn[0][0] )
    if ( maxOccurances < 1 ):
        maxOccurances = 1

        
    maxLength = getMaxLength( wordsIn )+1

    for item in wordsIn:
        currOccurances = int( item[0] )

        asterisks = "*" * ( (50 * currOccurances) // maxOccurances ) 

        histoAdd = item[1] + ( " " * ( maxLength - len( item[1] ) ) ) + asterisks

        histogram.append( histoAdd )

    return histogram

def generateHistogram( inputDict ):
    """
    Generates a histogram from an unordered
    dictionary of sort string=>int

    Arguments:
        inputDict: a dictionary of values

    Returns:
        histo (list): a histogram in list form
    """
    if ( len( inputDict ) < 1 ):
        return ""
    else:
        sortedVals = sortDictionary( inputDict )
        return generateHistogramPresorted( sortedVals )

def sortDictionary( inputDict ):
    """
    Sorts a dictionary and returns it
    as a list of tuples

    Arguments:
        inputDict: dictionary

    Returns:
        list of tuples
    """
    sortedVals = sorted([(value,key) for (key,value) in inputDict.items()]) 

    sortedVals.reverse()

    return sortedVals

def getMaxLength( values ):
    maxLength = 0

    for i in values:
        if ( len( i[1] ) >maxLength):
            maxLength = len(i[1])

    return maxLength
