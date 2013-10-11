#!/usr/bin/python3
"""
Author: Nate Levesque <public@thenaterhood.com>
File: csv.py
Language: Python3
Description:
	Deals with creating and reading csv data.
	Creates (and parses) well-formed CSV data where
	no field takes up multiple lines and where each
	field is quoted as text.

"""
class Csv:

	__slots__ = ('delimeter', 'headers', 'dataMatrix', 'numCols' )

	def __init__( self, delimeter="," ):

		self.delimeter = delimeter
		self.headers = None
		self.dataMatrix = []

	def setMatrix( self, dataArray ):
		"""
		Sets the data stored in the class

		Arguments:
			dataArray: a 2-dimensional array 
			of tabular data to store in the class
		"""
		self.dataMatrix = dataArray

	def writeCSV( self, filename ):
		"""
		Writes the csv data to a csv file 
		or other file with the delimeter set 

		Arguments:
			filename: the name of the file to write
		"""

		csvFile = open( filename, 'w' )
		
		csvLines = self.createCSV()

		for line in csvLines:
			csvFile.write( line + "\n" )

		csvFile.close()


	def createCSV( self ):
		"""
		Creates the csv data and returns
		it as an array of lines
		"""
		csvLines = [ self.createHeader() ]

		for row in self.dataMatrix:
			csvRow = ""
			for cell in row:
				csvRow += self.sanitizeString( cell ) + self.delimeter

			# We need to remove the extra comma from the end
			csvLines.append( csvRow[0:len( csvRow )-1 ] )

		return csvLines


	def createHeader( self ):

		if ( self.headers != None ):
			header = ""

			for h in self.headers:
				header += self.sanitizeString(h) + self.delimeter

		else:
			header = ""

		return header[0:len( header )-1]

	def sanitizeString( self, dirty ):
		"""
		Sanitizes a string for writing to csv 
		by adding quotes and escaping the delim 
		and quotes within the string

		Arguments:
			dirty: the unsanitized string

		"""
		clean = '"'
		dirty = str( dirty )

		for c in dirty:

			if ( c == '"'):
				clean += '"'
			if ( c == '\n'):
				pass
			else:
				clean += c

		clean += '"'

		return clean

	def unsanitizeString( self, clean ):
		"""
		Reverses the CSV sanitization on a string 

		Arguments:
			clean - the sanitized string
		"""
		dirty = ""
		clean = str( clean )

		prev_c = ""
		for c in clean:

			if ( c == '"' and c == prev_c ):
				pass
			else:
				dirty += c

			prev_c = c

		return dirty[1:len(dirty)]

	def readCSVLine( self, line ):
		"""
		Parses a single line of csv data 
		"""

		data = []
		parsedData = []
		for item in line.strip().split( '"'+self.delimeter ):
			data.append( item )

		data[-1] = data[-1][0:len(data[-1])-1]


		for i in range( 0, len(data) ):

			data[i] = self.unsanitizeString( data[i] )


		return data



	def readCSV( self, filename, header=False ):
		"""
		Reads a csv file into the data array

		Arguments:
			filename - the name of the file to read
			header - whether the file contains a header
		"""
		self.dataMatrix = []
		csvFile = open(filename)
		for line in csvFile:

			self.dataMatrix.append( self.readCSVLine( line ) )

		if ( header ):
			self.headers = self.dataMatrix[0]
			self.dataMatrix = self.dataMatrix[1:]

		csvFile.close()



	


				