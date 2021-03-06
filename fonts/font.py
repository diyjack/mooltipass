#!/usr/bin/env python
#
# Copyright (c) 2014 Darran Hunt (darran [at] hunt dot net dot nz)
# All rights reserved.
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at src/license_cddl-1.0.txt
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at src/license_cddl-1.0.txt
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#/

import sys
import png, math
import xml.etree.ElementTree as ET
import numpy as np
from optparse import OptionParser

parser = OptionParser(usage = 'usage: %prog [options]')
parser.add_option('-n', '--name', help='name for font', dest='name', default=None)
parser.add_option('-p', '--png', help='png file for font', dest='png', default=None)
parser.add_option('-x', '--xml', help='xml file for font', dest='xml', default=None)
(options, args) = parser.parse_args()

if options.name == None or options.png == None or options.xml == None:
    parser.error('name, png, and xml options are required')

def generateHeader(fontName, pngFilename, xmlFilename):
    ''' Output C code tables for the specified font
    '''
    font = png.Reader(pngFilename)
    xml = ET.parse(xmlFilename)

    chars = xml.findall('Char')
    root = xml.getroot()
    glyphd = {}
    maxWidth = 0
    for char in chars:
        glyphd[char.attrib['code']] = char.attrib
        if int(char.attrib['width']) > maxWidth:
            maxWidth = int(char.attrib['width'])

    width, height, pixels, meta = font.asDirect()

    print '/*'
    print ' * Font {}'.format(fontName)
    print ' */'
    print
    print '#define {}_HEIGHT {}'.format(fontName.upper(),root.attrib['height'])
    print

    yind = 0
    line = {}
    for item in pixels:
        line[yind] = []
        for xind in xrange(0,len(item),4):
            #line[yind].append(np.reshape(item, (128,4)))
            line[yind].append(dict(r=item[xind+0], g=item[xind+1], b=item[xind+2], a=item[xind+3]))
        yind += 1

    asciiPixel = [' ', '.', '*', '*',
                  '*', '*', '*', '*',
                  '*', '*', '*', '*',
                  '*', '*', '*', '*']
    count = 0
    for ch in sorted(glyphd.keys()):
        if ch == ' ':
            # skip space
            continue
        glyph = glyphd[ch]
        rect = [int(x) for x in glyph['rect'].split()]
        offset = [int(x) for x in glyph['offset'].split()]
        print 'const uint8_t {}_{:#x}[] __attribute__((__progmem__)) = {{'.format(fontName,ord(glyph['code'])),
        print "  /* '{0}' width: {1} */".format(glyph['code'],glyph['width'])
        x = 0
        for y in range(rect[1],rect[1]+rect[3]):
            patt = ''
            print '    ',
            lineWidth = 1
            pixels = 0
            pixCount = 0
            for x in range(rect[0],rect[0]+rect[2]-1):
                count += 1
                # map 255 shades to 4
                pix = line[y][x]['a']/64
                pixels = pixels << 2 | pix
                pixCount += 1
                if pixCount >= 4:
                    lineWidth += 1
                    print '{:#04x}, '.format(pixels),
                    pixels = 0
                    pixCount = 0

                patt += asciiPixel[pix]

            count += 1
            pix = line[y][x+1]['a']/64
            patt += asciiPixel[pix]
            pixels = pixels << 2 | pix
            pixCount += 1
            if pixCount < 4:
                pixels = pixels << (4-pixCount)*2
            print '{:#04x}, '.format(pixels),
            if lineWidth < (maxWidth+3)/4:
                for ind in range(lineWidth, (maxWidth+3)/4):
                    print '      ',
            print ' /* [{}] */'.format(patt)
        print '};\n'
    print

    print 'const glyph_t {}[] __attribute__((__progmem__)) = {{'.format(fontName)

    index = 0
    chMap = []
    for ch in range(ord(' '), ord('~')+2):
        if glyphd.has_key(chr(ch)):
            chMap.append(index)
            index += 1
            glyph = glyphd[chr(ch)]
            rect = [int(x) for x in glyph['rect'].split()]
            offset = [int(x) for x in glyph['offset'].split()]
            if ch == ord(' '):
                print "    {{ {:>2}, {:>2}, {:>2}, {:>2}, {:>2}, NULL }}, /* '{}' */ ".format(glyph['width'], 
                    rect[2], rect[3], offset[0], offset[1], glyph['code'])
            else:
                print "    {{ {:>2}, {:>2}, {:>2}, {:>2}, {:>2}, {}_{:#x} }}, /* '{}' */ ".format(glyph['width'], 
                    rect[2], rect[3], offset[0], offset[1], fontName, ord(glyph['code']), glyph['code'])
        else:
            chMap.append(None)
    print '};\n'

    print '/* Mapping from ASCII codes to font characters, from space (0x20) to del (0x7f) */'
    print 'const uint8_t {}_asciimap[] __attribute__((__progmem__)) = {{ '.format(fontName),
    index = 0
    for item in chMap:
        if index == 0:
            print '\n    ',
            index = 16
        if item != None:
            print '{:>3}, '.format(item),
        else:
            print '255, ',
        index -= 1
    print '};'

    return count

def main():
    generateHeader(options.name, options.png, options.xml)

if __name__ == "__main__":
    main()
