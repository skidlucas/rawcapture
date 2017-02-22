#!/usr/bin/env python2

if __name__ == '__main__':
    import os
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import wxgui
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from gnuradio.wxgui import fftsink2
from gnuradio.wxgui import forms
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import osmosdr
import time
import wx
import sys
import getopt
import re


class rawcapture(grc_wxgui.top_block_gui):

    def __init__(self):
        grc_wxgui.top_block_gui.__init__(self, title="RawCapture")
        _icon_path = "/usr/share/icons/hicolor/32x32/apps/gnuradio-grc.png"
        self.SetIcon(wx.Icon(_icon_path, wx.BITMAP_TYPE_ANY))

        # create outputs folder if it doesn't exist
        output_path = "outputs/"

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        ##################################################
        # Variables
        ##################################################
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'f:s:o:h', ['freq=', 'samp_rate=', 'output=', 'help'])
        except getopt.GetoptError:
            usage()

        output_file_name = "raw"

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage()
            elif opt in ('-f', '--freq'):
                #get int and dec part of the argument
                if "." not in str(arg): 
                    freq_has_dec = False
                    freq_int_part = str(arg)
                else:
                    freq_has_dec = True
                    freq_int_part, freq_dec_part = str(arg).split('.')

                self.freq = freq = float(arg) * 1e6 #101.9
            elif opt in ('-s', '--samp_rate'):
                #get int and dec part of the argument
                if "." not in str(arg): 
                    sample_rate_has_dec = False
                    sample_rate_int_part = str(arg)
                else:
                    sample_rate_has_dec = True
                    sample_rate_int_part, sample_rate_dec_part = str(arg).split('.')
                
                self.sample_rate = sample_rate = float(arg) * 1e6 #0.5
            elif opt in ('-o', '--output'):
                output_file_name = str(arg)
                
            else:
                usage()

        # check if there is a freq and a sample_rate
        try:
            freq
        except NameError:
            print "You didn't enter the center frequency\n"
            usage()

        try:
            sample_rate
        except NameError:
            print "You didn't enter a sample rate\n"
            usage()
        
        # correctly name the output_file
        full_path = os.path.realpath(__file__)
        if freq_has_dec is True:
            freq_str = freq_int_part + "p" + freq_dec_part + "M"
        else:
            freq_str = freq_int_part + "M"

        if sample_rate_has_dec is True:
            sample_rate_str = sample_rate_int_part + "p" + sample_rate_dec_part + "M"
        else:
            sample_rate_str = sample_rate_int_part + "M"

        output_file_name += "_c" + freq_str + "_s" + sample_rate_str + ".iq"
        print "creating file /outputs/" + output_file_name + "\n\n"
        self.output_file = output_file = os.path.dirname(full_path) + "/outputs/" + output_file_name

        ##################################################
        # Blocks
        ##################################################
        self.wxgui_fftsink2_0 = fftsink2.fft_sink_c(
            self.GetWin(),
            baseband_freq=freq,
            y_per_div=10,
            y_divs=10,
            ref_level=0,
            ref_scale=2.0,
            sample_rate=sample_rate,
            fft_size=1024,
            fft_rate=15,
            average=True,
            avg_alpha=None,
            title="FFT Plot",
            peak_hold=False,
        )
        self.Add(self.wxgui_fftsink2_0.win)
    
        self.osmosdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.osmosdr_source_0.set_sample_rate(sample_rate)
        self.osmosdr_source_0.set_center_freq(freq, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(10, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna("", 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)

        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, output_file, False)
        self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################   
        self.connect((self.osmosdr_source_0, 0), (self.wxgui_fftsink2_0, 0))    
        self.connect((self.osmosdr_source_0, 0), (self.blocks_file_sink_0, 0))


def main(top_block_cls=rawcapture, options=None):

    tb = top_block_cls()
    tb.Start(True)
    tb.Wait()

def usage():
    print "How to use:\npython rawcapture.py -f freq (Mhz) -s samp_rate (Mhz) [-o output_file]"
    print "If you don't use the -o option, the name will be raw_c[freq]_s[samp_rate].iq"
    sys.exit(2)


if __name__ == '__main__':
    main()
