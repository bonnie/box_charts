# Copyright (c) 2016 Bonnie Schulkin. All Rights Reserved.
#
# This file is part of box_charts.
#
# box_charts is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# box_charts is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with box_charts. If not, see <http://www.gnu.org/licenses/>.


#######################################################################################
# imports
#######################################################################################

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase.pdfmetrics import stringWidth 
from reportlab.lib.utils import simpleSplit 
from reportlab.platypus.paragraph import ParaLines, FragLine
# http://www.reportlab.com/apis/reportlab/2.4/platypus.html

import os, sys
from math import floor
import time

#######################################################################################
# constants
#######################################################################################
# scaled constants to be set later in set_scaled_constants
SECTION_START = '+'
MEASURE_SPLIT = '|'
SECTION_LINE_SPLIT = '~'
TITLE_START = '^'
METADATA_START = '>'
REPEAT_CHAR = ':'
SCALE_START = '*'
KEY_CHANGE_START = '}'
KEY_CHANGE_SPLIT = '~'

DEFAULT_FONT = 'Helvetica'
DEFAULT_BOLD_FONT = 'Helvetica-Bold'
LYRIC_FONT = DEFAULT_FONT

CHORD_TABLE_BORDER_COLOR = colors.black
LYRIC_BACK_COLOR = colors.Color(.75,.75,.75,1) # light gray

TOP_MARGIN = 0.25*inch
LEFT_MARGIN = 0.75*inch

CELL_MARGIN_H = 6 # default
CELL_MARGIN_V = 3 # default

DEBUG = False

PDF_DIR = 'pdf'
TEXT_DIR = 'text'

SCALE_DEGREES = {}
SCALE_DEGREES['Ab'] = ['Ab', 'Bb', 'C', 'Db', 'Eb', 'F', 'G']
SCALE_DEGREES['A'] = ['A', 'B', 'C#', 'D', 'E', 'F#', 'G#']
SCALE_DEGREES['Bb'] = ['Bb', 'C', 'D', 'Eb', 'F', 'G', 'A']
SCALE_DEGREES['B'] = ['B', 'C#', 'D#', 'E', 'F#', 'G#', 'A#']
SCALE_DEGREES['C'] = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
SCALE_DEGREES['Db'] = ['Db', 'Eb', 'F', 'Gb', 'Ab', 'Bb', 'C']
SCALE_DEGREES['D'] = ['D', 'E', 'F#', 'G', 'A', 'B', 'C#']
SCALE_DEGREES['Eb'] = ['Eb', 'F', 'G', 'Ab', 'Bb', 'C', 'D']
SCALE_DEGREES['E'] = ['E', 'F#', 'G#', 'A', 'B', 'C#', 'D#']
SCALE_DEGREES['F'] = ['F', 'G', 'A', 'Bb', 'C', 'D', 'E']
SCALE_DEGREES['F#'] = ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#']
SCALE_DEGREES['G'] = ['G', 'A', 'B', 'C', 'D', 'E', 'F#']

#######################################################################################
# globals
#######################################################################################
global doc, dwidth, dheight, elements, styles, sizes, spacers

#######################################################################################
# pdf styles
#######################################################################################

def create_styles():

	global styles
	
	# paragraph styes
	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(
			'title_text',
			fontName=DEFAULT_BOLD_FONT, 
			fontSize=sizes['TITLE_FONT_SIZE'],
			alignment=TA_CENTER))
	styles.add(ParagraphStyle(
			'mdata_text',
			fontName=DEFAULT_FONT, 
			fontSize=sizes['MDATA_FONT_SIZE'],
			alignment=TA_CENTER))
	styles.add(ParagraphStyle(
			'section_header_text',
			fontName=DEFAULT_BOLD_FONT, 
			fontSize=sizes['SECTION_FONT_SIZE'],
			alignment=TA_LEFT))
	styles.add(ParagraphStyle(
			'chord_text',
			fontName=DEFAULT_BOLD_FONT, 
			fontSize=sizes['CHORD_FONT_SIZE'],
			alignment=TA_CENTER))
	styles.add(ParagraphStyle(
			'lyric_text',
			fontName=LYRIC_FONT, 
			fontSize=sizes['LYRIC_FONT_SIZE'],
			alignment=TA_LEFT))

def create_spacers():

	global spacers
	spacers = {}
	
	spacers['section_title'] = Spacer(1, sizes['MDATA_FONT_SIZE']/2)
	spacers['section'] = Spacer(1, sizes['TABLE_SPACER_SIZE'])
	spacers['title'] = Spacer(1, scale_it(0.8*sizes['TITLE_FONT_SIZE'])) # double scale
	spacers['mdata'] = Spacer(1, scale_it(sizes['MDATA_FONT_SIZE'])) # double scale
	spacers['post_chord-lyric'] = Spacer(0,sizes['LYRIC_FONT_SIZE'])

#######################################################################################
# functions  
#######################################################################################

def set_scaled_constants():

	global sizes
	sizes = {}
	
	sizes['TITLE_FONT_SIZE'] = scale_it(24)
	sizes['MDATA_FONT_SIZE'] = scale_it(12)
	sizes['CHORD_FONT_SIZE'] = scale_it(16)
	sizes['LYRIC_FONT_SIZE'] = scale_it(11)
	sizes['SECTION_FONT_SIZE'] = scale_it(14)

	sizes['CHORD_TABLE_BORDER_WIDTH'] = scale_it(1)

	sizes['LYRIC_ROW_HEIGHT'] = sizes['LYRIC_FONT_SIZE'] * 1.2
	sizes['CHORD_ROW_HEIGHT'] = sizes['CHORD_FONT_SIZE'] * 2
	sizes['CHORD_RIGHT_PADDING'] = sizes['CHORD_FONT_SIZE']/1.6

	sizes['TABLE_SPACER_SIZE'] = scale_it(20)

	# for multi-chord cells
	sizes['MINICHORD_RIGHT_PADDING'] = scale_it(0)
	sizes['MINICHORD_LEFT_PADDING'] = scale_it(0)
	sizes['MINICHORD_BOTTOM_PADDING'] = sizes['CHORD_FONT_SIZE']/1.6 
	sizes['MINICHORD_TOP_PADDING'] = scale_it(0)
	sizes['MINICHORD_TABLE_STYLE'] = [
	# 				('GRID', (0,0), (-1,-1), 1, colors.black),
					('ALIGN', (0, 0), (-1,-1), 'CENTER'),
					('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
					('LEFTPADDING', (0,0), (-1,-1), sizes['MINICHORD_LEFT_PADDING']),
					('RIGHTPADDING', (0,0), (-1,-1), sizes['MINICHORD_RIGHT_PADDING']),
					('BOTTOMPADDING', (0,0), (-1,-1), sizes['MINICHORD_BOTTOM_PADDING']),
					('TOPPADDING', (0,0), (-1,-1), sizes['MINICHORD_TOP_PADDING'])
					]

def print_debug(string):
	if debug:
		print(string)

def get_list(filename): 
	scriptDir = os.path.dirname(os.path.realpath(__file__))
	with open(os.path.join(scriptDir, filename)) as f:
		lines = f.read()
	f.close()
	return lines.split('\n')

def measure_split(line, chords):
	l = line
	if chords:
		l = line.strip(MEASURE_SPLIT)
	return l.split(MEASURE_SPLIT)

def get_col_array(colcount, total_colcount):
	colwidth = (dwidth - 2*LEFT_MARGIN) / total_colcount
	return (colwidth, [colwidth] * colcount)

def initialize_rows(rowcount):
	r = {}
	for rownum in range(rowcount):
		r[rownum] = []
	return r

def get_lyric_lines(lyric_array, measure_start, column_count):
	# do we need to print all the lyrics rows? 
	lyric_total = 0
	lyric_count = len(lyric_array)
	
	# test each line individually, backward
	for n in range(1, lyric_count + 1):
		lyric_line = lyric_count + 1 - n
		for column in range(column_count):
			lyricblob = ''.join(lyric_array[lyric_line][measure_start:measure_start + column_count])
			if lyricblob != '':
				return lyric_line

	# if we got this far, no lines are good
	return 0

def get_cols(chord_array, measure_number, col_count, default_col_array):
	# will there be an incomplete line? 
	hanging_line = len(chord_array) % col_count

	# short last line? 
	if hanging_line and len(chord_array) - measure_number < col_count:
		this_col_count = len(chord_array) % col_count
		(this_width, this_col_array) = get_col_array(this_col_count, col_count)
	else:
		this_col_count = col_count
		this_col_array = default_col_array
		
	return (this_col_count, this_col_array)

def scale_it(number):
	return scale * number

def create_paragraph(texttype, input_text, fontsize, fontstyle, maxwidth, align):

# 	if texttype == 'lyric' or len(input_text) <= 1: 
# 		text = input_text
#   		small_fontsize = fontsize
# 	else:
# 		text = input_text[0]
# 		small_fontsize = str(fontsize*0.7)
# 		for i in range(1,len(input_text)):
# 			if input_text[i] in ['#', 'b']:
# 				text += '<super>' + input_text[i] + '</super>'
# 			else:
# 				text += input_text[i]
# 	
# 	if '<super>' in text:
# 		print text

	text = input_text
		
	text_width = stringWidth(text, fontstyle, fontsize)
	new_fontsize = fontsize
	line_count = len(simpleSplit(text, fontstyle, new_fontsize, maxwidth)) 

	while (line_count > 1 or text_width > maxwidth) and new_fontsize > 0: 

		new_fontsize = new_fontsize - scale_it(0.5)
		text_width = stringWidth(text, fontstyle, new_fontsize)
		line_count = len(simpleSplit(text, fontstyle, new_fontsize, maxwidth)) 
	
# 	if text == 'something from the':
# 		print "text width: " + str(text_width) + " font size: " + str(fontsize)
	
	if fontsize <= 0:
		print("error: can't print this " + texttype + ": [" + text + "] too wide at any size. Exiting.")
		exit()

	# make a new style based on this new size
	uniq = str(time.time())
	style_name = texttype + uniq
	styles.add(ParagraphStyle(
			style_name,
			fontName=fontstyle,
			fontSize=new_fontsize,
			alignment=align))

	return Paragraph(text, styles[style_name])

#######################################################################################
# create_table
#######################################################################################

def create_table(data, cols, mnum): 
#  	tstyles_start = [('VALIGN', (0,0), (-1,-1), 'MIDDLE')]
	tstyles_start = [('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0, 0), (-1,-1), 'CENTER')]

	# get col width and make an array for the table
	(col_width, col_array) = get_col_array(cols, cols)

	# for easier future reference
	chords = data['chords']
	lyrics = data['lyrics']

	# initialize rows
	rows = initialize_rows(len(lyrics) + 1)

	# initialize column count and lyric lines for the first go-around
	(this_col_count, this_col_array) = get_cols(chords, 0, cols, col_array)
	lyric_total = get_lyric_lines(lyrics, 0, this_col_count)
	row_count = lyric_total + 1 
	col_counter = 0
	# track repeat measures
	start_repeat_measures = []
	end_repeat_measures = []

	# process the data
	for i in range(len(chords)):

		rnum = int(floor (i / cols))
		cnum = col_counter
# 		print "i" + str(i) + " rnum" + str(rnum) + " cnum" + str(cnum)
		
		# look for repeats
		chord_text = chords[i]
		if chord_text[0] == REPEAT_CHAR:
			start_repeat_measures.append(cnum)
			chord_text = chord_text[1:]
		elif chord_text[-1] == REPEAT_CHAR:
			end_repeat_measures.append(cnum)
			chord_text = chord_text[:-1]
		
		# make a mini table to contain the multi-chords
		chord_list = chord_text.split(' ')
		chordnum = len(chord_list)	
		
		mini_table_data = []
		for chd in chord_list:
			chord_width = (col_width - sizes['CHORD_RIGHT_PADDING'])/chordnum
			avail_width = chord_width - sizes['MINICHORD_RIGHT_PADDING'] - sizes['MINICHORD_LEFT_PADDING']
			chord_para = create_paragraph('chord', chd, sizes['CHORD_FONT_SIZE'], DEFAULT_BOLD_FONT, avail_width, TA_CENTER)
			mini_table_data.append(chord_para)
# 			http://www.reportlab.com/apis/reportlab/2.4/platypus.html

		rows[0].append(Table([mini_table_data], 
								colWidths=[chord_width]*chordnum, 
								rowHeights=[sizes['CHORD_ROW_HEIGHT']], 
								style=sizes['MINICHORD_TABLE_STYLE'], 
								hAlign='CENTER'))
# 		rows[0].append(Paragraph(','.join([str(cnum),str(rnum)]), styles['chord_text']))

		# then the lyrics
		for l in range(1,row_count):
			if i >= len(lyrics[l]):
				lyric_text = ''
			else:
				lyric_text = lyrics[l][i]

			# is it too wide? Get the right font size
			this_lyric_para = create_paragraph('lyric', lyric_text, sizes['LYRIC_FONT_SIZE'], LYRIC_FONT, col_width - 2*CELL_MARGIN_H, TA_LEFT)
			rows[l].append(this_lyric_para)

		# increment column counter
		col_counter += 1

		# time to draw the measure row? 
		if col_counter == this_col_count:
				
			tdata = []
			tstyles = []
			tstyles += tstyles_start # can't just say tstyles = tstyles_start; tstyles_start starts changin'
			
			# row heights
			rheights = [sizes['CHORD_ROW_HEIGHT']] + [sizes['LYRIC_ROW_HEIGHT']] * lyric_total

			# chords style
			tstyles.append(('GRID', (0, 0), (this_col_count - 1, 0), sizes['CHORD_TABLE_BORDER_WIDTH'],CHORD_TABLE_BORDER_COLOR))
			tstyles.append(('RIGHTPADDING', (0, 0), (this_col_count - 1, 0), sizes['CHORD_RIGHT_PADDING']))

			# lyrics shading every other row
			for lnum in range(1,row_count):
				if lnum % 2 == 0:				
					tstyles.append(('BACKGROUND', (0, lnum), (this_col_count - 1, lnum), LYRIC_BACK_COLOR))

			# repeat measures
			#line commands are like 
			#op, start, stop, weight, colour, cap, dashes, join, linecount, linespacing 
			for coord in start_repeat_measures:
				tstyles.append(('LINEBEFORE', (coord,0), (coord,0), 3*sizes['CHORD_TABLE_BORDER_WIDTH'], CHORD_TABLE_BORDER_COLOR, 2))
# 				tstyles.append(('LINEBEFORE', (coord,0), (coord,0), 3*sizes['CHORD_TABLE_BORDER_WIDTH'], CHORD_TABLE_BORDER_COLOR, 2, [], 2, 2, 3*sizes['CHORD_TABLE_BORDER_WIDTH']))
			for coord in end_repeat_measures:
				tstyles.append(('LINEAFTER', (coord,0), (coord,0), 3*sizes['CHORD_TABLE_BORDER_WIDTH'], CHORD_TABLE_BORDER_COLOR, 2))

			# add rows to the table data
			for r in range(row_count):
				tdata.append(rows[r]) 
			
			elements.append(Table(tdata, 
									colWidths=this_col_array, 
									rowHeights=rheights, 
									style=tstyles, 
									hAlign='LEFT'))
			elements.append(spacers['post_chord-lyric'])
	
			# re-initialize rows
			rows = initialize_rows(len(lyrics) + 1)

			# re-initialize column count and lyric lines for the next go-around
			(this_col_count, this_col_array) = get_cols(chords, i+1, cols, col_array)
			lyric_total = get_lyric_lines(lyrics, i+1, this_col_count)
			row_count = lyric_total + 1 
			col_counter = 0
			start_repeat_measures = []
			end_repeat_measures = []

# 			if rnum == 4:
# 				print i + 1
# 				print "thi_cols" + str(this_col_count)
# 				print "lyric_total" + str(lyric_total)

#######################################################################################
# start pdf
#######################################################################################
def start_pdf(mdata):
	global doc, elements, dwidth, dheight

	pdf_file = os.path.join(PDF_DIR, mdata['title'] + '.pdf')
	doc = SimpleDocTemplate(pdf_file, pagesize=letter)
	elements = []
	dwidth, dheight = letter

	# margins
	doc.topMargin = TOP_MARGIN
	doc.leftMargin = LEFT_MARGIN
	doc.bottomMargin = TOP_MARGIN
	doc.rightMargin = LEFT_MARGIN
	
def transpose(key1, key2, raw_chord):
	scale1 = SCALE_DEGREES[key1]
	scale2 = SCALE_DEGREES[key2]
	
	if raw_chord in ['%', '']:
		return(raw_chord)
		
	after_stuff = ''
	before_stuff = ''
	if raw_chord[0] == REPEAT_CHAR:
		before_stuff = REPEAT_CHAR
		chord = raw_chord[1:]
	else:
		chord = raw_chord	
	
	# find the scale degree
	if chord in scale1:
		index = scale1.index(chord)
	elif chord[0:2] in scale1:
		index = scale1.index(chord[0:2])
		after_stuff = chord[2:]
	elif chord[0] in scale1:
		index = scale1.index(chord[0])
		after_stuff = chord[1:]
	elif chord[0] + '#' in scale1:
		index = scale1.index(chord[0] + '#')
		after_stuff = '#' + chord[1:]
	elif chord[0] + 'b' in scale1:
		index = scale1.index(chord[0] + 'b')
		after_stuff = 'b' + chord[1:]
	else:
		print("bad chord: [" + chord + "]. Exiting.")
		exit()
	
	# translate it to the new key
	new_chord = before_stuff + scale2[index] + after_stuff
	
	# eliminate nonsense like b# or #b
	new_chord = new_chord.replace('b#', '')
	new_chord = new_chord.replace('#b', '')
	
	return new_chord
	
def transpose_list(key1, key2, old_chords):
	if key1 == '':
		return old_chords
		
	new_chords = []
	for raw_chord in old_chords:
		if ' ' in raw_chord:
			new_chord = ' '.join(transpose_list(key1, key2, raw_chord.split(' ')))
		elif '/' in raw_chord:
			new_chord = '/'.join(transpose_list(key1, key2, raw_chord.split('/')))			
		else:
			new_chord = transpose(key1, key2, raw_chord)
		
		new_chords.append(new_chord)
		
	return new_chords

#######################################################################################
# parse file
#######################################################################################

def parse_file(data_file):

	global scale
	sections = {}
	mdata = {}
	new_measure = False
	lyrics_line_next = False
	snum = 0
	lnum = 1
	first_measure = True
	scale = 1
	from_key = ''
	to_key = ''

	for line in get_list(data_file):
		# new measure line
		if line == '':
			new_measure = True
			lyrics_line_next = False
	# 		print("blank line: [" + line + "]")
		
		# title line
		elif line[0] == TITLE_START:	
			mdata['title'] = line[1:]

		#  metadata line
		elif line[0] == METADATA_START:
			if 'other' not in mdata:
				mdata['other'] = []			
			mdata['other'].append(line[1:])
	
		elif line[0] == SCALE_START:
			scale = float(line[7:])

		elif line[0] == KEY_CHANGE_START:
			from_key, to_key = line[1:].split(KEY_CHANGE_SPLIT)

		# new section
		elif line[0] == SECTION_START:
	# 		print("section line: [" + line + "]")
			snum = snum + 1
			sections[snum] = {}
			sections[snum]['measures'] = {}
			sections[snum]['measures']['chords'] = []

			if SECTION_LINE_SPLIT in line:
				tokens = line[1:].split(SECTION_LINE_SPLIT)
				sections[snum]['name'] = tokens[0]
		
			if len(tokens) > 1:
				for item in tokens[1:]:
					if '=' not in item:
						print("Bad section line [" + line + "]. Exiting.")
						exit()
					(key, val) = item.split('=')
					if key == 'width':
						width = int(val)
						sections[snum]['width'] = width
					elif key == 'lyrics':
						lcount = int(val)
						sections[snum]['lcount'] = lcount
					elif key == 'pickup':
						sections[snum]['pickup'] = int(val)
					else:
						print("Bad section data: [" + item + "]. Exiting.")
						exit()
			
			else:
				sections[snum]['name'] = ''
				print_debug('WARNING: section ' + str(snum) + ' has no name')

			new_measure = True
			first_measure = True
			lyrics_line_next = False
		
		# measure line
		elif new_measure:
	# 		print("measure first line: [" + line + "]")

			if first_measure:
				first_measure = False
			else:
			# clean up from previous measure
				while lcount >= lnum:
					if lnum not in sections[snum]['measures']['lyrics']:
						sections[snum]['measures']['lyrics'][lnum] = []
					sections[snum]['measures']['lyrics'][lnum] += [''] * width
					lnum += 1
		
			raw_chords = measure_split(line, chords=True)
			chords = transpose_list(from_key, to_key, raw_chords)
			sections[snum]['measures']['chords'] += chords
			linelength = len(chords)
			new_measure = False
			lyrics_line_next = True
			lnum = 1
		
		# lyrics line
		elif lyrics_line_next:
	# 		print("lyrics line: [" + line + "]")
			lyrics = measure_split(line, chords=False)
			if len(lyrics) > linelength:
				print("lyrics line [" + line + "] has too many measures. Exiting.")
				exit()
		
			while len(lyrics) < linelength:
				lyrics.append('')
		
			if 'lyrics' not in sections[snum]['measures']:
				sections[snum]['measures']['lyrics'] = {}
			if lnum not in sections[snum]['measures']['lyrics']:
				sections[snum]['measures']['lyrics'][lnum] = []
			sections[snum]['measures']['lyrics'][lnum] += lyrics
			lnum += 1
		
		# should never get here
		else: 
			print("bad line: [" + line + "]. Exiting.")
			exit()

	return (mdata, sections)

#######################################################################################
# print metadata 
#######################################################################################
def print_metadata(mdata):
	# title
	if len(mdata) > 0: 
		if 'title' in mdata:
			elements.append(Paragraph(mdata['title'], styles['title_text']))
		else:
			print_debug("WARNING: no title")

		if 'other' in mdata:
			elements.append(spacers['title'])
			for line in mdata['other']:
				elements.append(Paragraph(line, styles['mdata_text']))
				elements.append(spacers['mdata'])

#######################################################################################
# print measures 
#######################################################################################

def print_measures(sections):
	running_count = 0
	mcount = 0

	for index in sorted(sections):
		data = sections[index]
		name = data['name']
		cols = int(data['width'])
		meas = data['measures']
		chords = meas['chords']

		# print section title
		elements.append(spacers['section'])
		if name:
			elements.append(Paragraph(name, styles['section_header_text']))
			elements.append(spacers['section_title'])
	
		# make tables for the measure lines
		t = create_table(meas, cols, running_count)

		running_count += len(chords)

#######################################################################################
# finish pdf
#######################################################################################
def finish_pdf():
	doc.build(elements)

#######################################################################################
#######################################################################################
# MAIN 
#######################################################################################
#######################################################################################


if len(sys.argv) != 2:
	print("Usage: chord_chart.py datafile.txt")
	exit()
	
filename = sys.argv[1]

mdata, sections = parse_file(filename)
set_scaled_constants()
create_styles()
create_spacers()
start_pdf(mdata)
print_metadata(mdata)
print_measures(sections)
finish_pdf()
