# vim: ts=4 ai noexpandtab
# Class that deals with AAC+
import os
import sys
from shell import shell
from flac import flac, flacdecode
from config import ipath
from time import time

# This is for the open source implementation. In this case we went for the
# Open Source Fraunhofer AAC Encoder (fdk-aac)


class aacplus(object):
	def __init__(self, aacopts):
		self.opts = aacopts
		if os.path.exists("%saac-enc" % ipath.aacpath) is False:
			print "Error: %saac-enc not found (is fdk-aac installed?)\
			Cannot convert" % ipath.aacpath
			sys.exit(-1)

	def AACPconvert(self, infile, outfile, logq):
		decoder = flacdecode(infile, outfile)()
		encoder = os.popen("%saac-enc %s - \"%s.aac\" > /tmp/aacplusLog" % (
			ipath.aacpath,
			self.opts,
			outfile,
		), 'wb', 8192
		)

		# while data exists in the decoders buffer
		for line in decoder.readlines():
			encoder.write(line)  # write it to the encoders buffer

		decoder.flush()
		decoder.close()
		encoder.flush()
		encoder.close()


# For the binary-only Nero AAC encoder
class aacplusNero(object):
	def __init__(self, aacopts):
		self.opts = aacopts
		if not os.path.exists("%sneroAacEnc" % ipath.neropath):
			print "ERROR: NeroAacEnc not found! Cannot convert."
			sys.exit(-1)

	def generateNeroTags(self, indata):
		'''
		The new versions of nero AAC encoder for Linux provides neroAacTag
		'''
		tags = ""

		# NeroTag format (for 'standard Nero Digital') along with 'indata' keys
		#  title = TITLE
		#  artist = ARTIST
		#  year = DATE
		#  album = ALBUM
		#  genre = GENERE
		#  track = TRACKNUMBER
		#  totaltracks =
		#  disc
		#  totaldiscs
		#  url = URL
		#  copyright = PUBLISHER
		#  comment = COMMENT (if blank, put in something like
		#     'converted by flac2all ($url)' )
		#  lyrics
		#  credits = ENCODEDBY
		#  rating
		#  label = PUBLISHER
		#  composer = COMPOSER
		#  isrc
		#  mood
		#  tempo
		# In format: -meta:<name>=<value>
		# User-defined fields are -meta-user:<name>=<value>

		validnerotags = {
			'title': 'TITLE',
			'artist': 'ARTIST',
			'year': 'DATE',
			'album': 'ALBUM',
			'genre': 'GENRE',
			'track': 'TRACKNUMBER',
			'copyright': 'PUBLISHER',
			'comment': 'COMMENT',
			'credits': 'ENCODEDBY',
			'label': 'PUBLISHER',
			'composer': 'COMPOSER',
			'url': 'URL',
		}

		for nerokey in validnerotags:
			try:
				tag = indata[validnerotags[nerokey]]
			except KeyError as e:
				if e.message == 'COMMENT':
					tag = "Converted by flac2all,\
					https://github.com/ZivaVatra/flac2all/"
				else:
					continue
			tags += " -meta:\"%s\"=\"%s\" " % (nerokey.strip(), tag.strip())

		return tags

	def AACPconvert(self, infile, outfile, logq):
		startTime = time()
		inmetadata = flac().getflacmeta("\"" + infile + "\"")

		tagcmd = "%sneroAacTag " % ipath.neropath
		try:
			metastring = self.generateNeroTags(inmetadata)
		except(UnboundLocalError):
			metastring = ""

		decoder = flacdecode(infile)()
		encoder = os.popen("%sneroAacEnc %s -if - -of %s.mp4 >/tmp/neroLog" % (
			ipath.neropath,
			self.opts,
			shell().parseEscapechars(outfile),
		), 'wb', 8192)

		# while data exists in the decoders buffer
		for line in decoder.readlines():
			encoder.write(line)  # write it to the encoders buffer

		decoder.flush()  # if there is any data left in the buffer, clear it
		decoder.close()  # somewhat self explanetory

		encoder.flush()
		encoder.close()

		# Now as the final event, load up the tags
		rc = os.system("%s \"%s.mp4\" %s" % (tagcmd, outfile, metastring))
		if rc != 0:
			logq.put([
				infile,
				outfile,
				"aacNero",
				"WARNING: Could not tag AAC file",
				rc,
				time() - startTime
			])
		else:
			logq.put([
				infile,
				outfile,
				"aacNero",
				"SUCCESS",
				0,
				time() - startTime
			])
