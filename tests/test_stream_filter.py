from connections.sim.stream_filter import StreamFilter, sys # We will be mocking stream_filter's sys (not our own)
from io import BufferedReader, BytesIO

class TestStreamFilter:

    SYS_PLATFORM_CACHE = None

    def setup_method(self):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        TestStreamFilter.SYS_PLATFORM_CACHE = sys.platform

    def teardown_method(self):
        """ teardown any state that was previously setup with a setup_method
        call.
        """
        sys.platform = TestStreamFilter.SYS_PLATFORM_CACHE # Needs to be reset otherwise other tests will fail
        # (found out the hard way)

    def test_passthrough(self):
        test_data = [x for x in range(0, 255)]

        stream = BufferedReader(BytesIO(bytes(test_data)))

        filter = StreamFilter(stream, 0)

        for b in test_data:
            assert b == filter.read(1)[0]

    def test_windows_filter(self):
        sys.platform = 'win32'

        test_data = b'bye\x0d\x0abye'

        stream = BufferedReader(BytesIO(bytes(test_data)))

        filter = StreamFilter(stream, 0)

        expected = b'bye\x0abye'

        for b in expected:
            assert b == filter.read(1)[0]

    def test_linux_no_filter(self):
        sys.platform = 'linux'

        test_data = b'hi\x0d\x0ahi'

        stream = BufferedReader(BytesIO(bytes(test_data)))

        filter = StreamFilter(stream, 0)

        expected = test_data

        for b in expected:
            assert b == filter.read(1)[0]
