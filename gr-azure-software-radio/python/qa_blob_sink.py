# pylint: disable=missing-function-docstring, no-self-use, missing-class-docstring, no-member
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) Microsoft Corporation.
# Licensed under the GNU General Public License v3.0 or later.
# See License.txt in the project root for license information.
#


import numpy as np
from gnuradio import gr_unittest
from gnuradio import blocks
from azure_software_radio import BlobSink
import azure_software_radio


class qa_BlobSink(gr_unittest.TestCase):

    # pylint: disable=invalid-name
    def setUp(self):
        azure_software_radio.blob_setup(self)

    # pylint: disable=invalid-name
    def tearDown(self):
        azure_software_radio.blob_teardown(self)

    def test_instance(self):

        instance = BlobSink(authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name='test-instance',
                            block_len=500000,
                            queue_size=4)

        # really only checking that the init didn't throw an exception above, but adding the check
        # below to keep flake8 happy
        self.assertTrue(instance is not None)

    def test_round_trip_data_through_blob(self):
        """ Upload known data to a blob using the blob_source block.

        Read this data back using the azure blob API and confirm that the data wasn't corrupted.
        """

        blob_name = 'test-blob.npy'
        block_len = 500000

        # set up a vector source with known complex data
        src_data = np.arange(0, 2 * block_len, 1, dtype=np.complex64)
        src = blocks.vector_source_c(src_data)

        # set up a blob sink
        op = BlobSink(authentication_method="connection_string",
                      connection_str=self.blob_connection_string,
                      container_name=self.test_blob_container_name,
                      blob_name=blob_name,
                      block_len=block_len,
                      queue_size=4)

        self.tb.connect(src, op)
        # run the flowgraph
        self.tb.run()

        # connect to the test blob container and download the file
        # compare the file we downloaded against the samples in the vector source
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)

        result_data = np.frombuffer(
            blob_client.download_blob().readall(), dtype=np.complex64)

        # check data
        self.assertTrue((src_data == result_data).all())


if __name__ == '__main__':
    gr_unittest.run(qa_BlobSink)
