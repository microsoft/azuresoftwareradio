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
from azure_software_radio import BlobSource
import azure_software_radio


class qa_BlobSource(gr_unittest.TestCase):

    # pylint: disable=invalid-name
    def setUp(self):
        azure_software_radio.blob_setup(self)

    # pylint: disable=invalid-name
    def tearDown(self):
        azure_software_radio.blob_teardown(self)

    def test_round_trip_data_through_blob(self):
        """ Upload known data to a blob using the azure blob API.

        Read this data back into a GNU Radio vector sink using the BlobSource
        block and confirm that the data wasn't corrupted.
        """

        blob_name = 'test-blob.npy'
        num_samples = 1000000

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)
        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)
        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')
        # set up a blob sink
        source = BlobSource(authentication_method="connection_string",
                            connection_str=self.blob_connection_string,
                            container_name=self.test_blob_container_name,
                            blob_name=blob_name,
                            queue_size=4)
        dst = blocks.vector_sink_c()

        self.tb.connect(source, dst)
        # set up fg
        self.tb.run()
        # check data

        result_data = dst.data()

        # check data
        self.assertTrue((src_data == result_data).all())

    def test_chunk_residue(self):
        '''
        Test that we don't crash if we get back a non-integer number of samples from a blob chunk
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)

        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        # set up a blob sink
        op = BlobSource(authentication_method="connection_string",
                        connection_str=self.blob_connection_string,
                        container_name=self.test_blob_container_name,
                        blob_name=blob_name,
                        queue_size=4)

        src_data_bytes = src_data.tobytes()
        # don't send the last 2 bytes of the last sample
        chunk = src_data_bytes[:-2]
        data, chunk_residue = op.chunk_to_array(chunk=chunk, chunk_residue=b'')

        # check data - it should include all samples except the last one
        self.assertTrue((data == src_data[:-1]).all())
        # the chunk residue should be the first 6 bytes of the last sample
        self.assertTrue((chunk_residue == src_data_bytes[-8:-2]))

        op.stop()

    def test_chunk_residue_merge(self):
        '''
        Test that we can glue samples back together if we get them in separate chunks
        '''

        blob_name = 'test-blob.npy'
        num_samples = 500

        # set up a vector source with known complex data
        src_data = np.arange(0, num_samples, 1, dtype=np.complex64)

        # connect to the test blob container and upload our test data
        blob_client = self.blob_service_client.get_blob_client(
            container=self.test_blob_container_name,
            blob=blob_name)

        blob_client.upload_blob(data=src_data.tobytes(), blob_type='BlockBlob')

        # set up a blob sink
        op = BlobSource(authentication_method="connection_string",
                        connection_str=self.blob_connection_string,
                        container_name=self.test_blob_container_name,
                        blob_name=blob_name,
                        queue_size=4)

        src_data_bytes = src_data.tobytes()
        # don't send the first 2 bytes of the first sample
        chunk_residue_in = src_data_bytes[:2]
        chunk = src_data_bytes[2:]

        data, chunk_residue = op.chunk_to_array(
            chunk=chunk, chunk_residue=chunk_residue_in)

        # check data - it should include all samples
        self.assertTrue((data == src_data).all())
        # the chunk residue should be the first 6 bytes of the last sample
        self.assertTrue(len(chunk_residue) == 0)

        op.stop()


if __name__ == '__main__':
    gr_unittest.run(qa_BlobSource)
