"""Tests for util.config_util"""

import unittest

from ample.util.config_util import AMPLEConfigOptions
from ample.util import argparse_util
from ample.util import options_processor
from ample.util.mrbump_util import REBUILD_MAX_PERMITTED_RESOLUTION
from ample.util.mrbump_util import SHELXE_MAX_PERMITTED_RESOLUTION
from ample.util.mrbump_util import SHELXE_MAX_PERMITTED_RESOLUTION_CC

__author__ = "Jens Thomas"


class Test(unittest.TestCase):

    def test_options_shelxe_resolution_max(self):
        """Make sure we turn off shelxe if resolution is outside limit
        """
        options = AMPLEConfigOptions()
        argso = argparse_util.process_command_line(args=['-mtz', 'foo',
                                                         '-fasta', 'bar'])
        options.populate(argso)

        self.assertTrue(options.d['use_shelxe'])  # default so should be true
        options.d['shelxe_rebuild'] = True

        # Set resolution below limit
        options.d['mtz_min_resolution'] = SHELXE_MAX_PERMITTED_RESOLUTION + 1
        options_processor.process_mr_options(options.d)

        self.assertFalse(options.d['use_shelxe'])
        self.assertFalse(options.d['shelxe_rebuild'])


    def test_options_shelxe_resolution_ok(self):
        """Check we don't accidently turn it off if above limit
        """
        options = AMPLEConfigOptions()
        argso = argparse_util.process_command_line(args=['-mtz', 'foo',
                                                         '-fasta', 'bar'])
        options.populate(argso)

        self.assertTrue(options.d['use_shelxe'])  # default so should be true
        options.d['shelxe_rebuild'] = True
        options.d['mtz_min_resolution'] = SHELXE_MAX_PERMITTED_RESOLUTION - 1
        options_processor.process_mr_options(options.d)
        
        self.assertTrue(options.d['use_shelxe'])
        self.assertTrue(options.d['shelxe_rebuild'])


    def test_options_shelxe_resolution_cc(self):
        """Check limit with coiled-coil mode turned on
        """
        options = AMPLEConfigOptions()
        argso = argparse_util.process_command_line(args=['-mtz', 'foo',
                                                         '-fasta', 'bar',
                                                         '-coiled_coil', 'True'])
        options.populate(argso)

        options.d['shelxe_rebuild'] = True
        limit = SHELXE_MAX_PERMITTED_RESOLUTION + ((SHELXE_MAX_PERMITTED_RESOLUTION_CC - SHELXE_MAX_PERMITTED_RESOLUTION) / 2)
        options.d['mtz_min_resolution'] = limit
        options_processor.process_mr_options(options.d)
        
        self.assertTrue(options.d['use_shelxe'])
        self.assertTrue(options.d['shelxe_rebuild'])
        
        
    def test_options_shelxe_resolution_cmd(self):
        """Check limit with coiled-coil mode turned on
        """
        extra = (REBUILD_MAX_PERMITTED_RESOLUTION - SHELXE_MAX_PERMITTED_RESOLUTION_CC) / 2
        limit = REBUILD_MAX_PERMITTED_RESOLUTION - extra
        options = AMPLEConfigOptions()
        argso = argparse_util.process_command_line(args=['-mtz', 'foo',
                                                         '-fasta', 'bar',
                                                         '-coiled_coil', 'True',
                                                         '-shelxe_max_resolution', str(limit)])
        options.populate(argso)
        
        options.d['use_shelxe'] = True
        options.d['shelxe_rebuild'] = True
        options.d['mtz_min_resolution'] = SHELXE_MAX_PERMITTED_RESOLUTION_CC + (extra / 2)
        options_processor.process_mr_options(options.d)
        
        self.assertTrue(options.d['use_shelxe'])
        self.assertTrue(options.d['shelxe_rebuild'])


if __name__ == "__main__":
    unittest.main()
