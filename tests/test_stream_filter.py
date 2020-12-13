from connections.sim.stream_filter import ReadFilter, WriteFilter, A
from io import BytesIO

def test_passthrough():
    test_data = [x for x in range(0, 255)]
    test_stream = BytesIO()

    # Write test data to stream
    write_filter = WriteFilter(test_stream)
    for b in test_data:
        write_filter.write(bytes([b]))

    # Check all were written
    num = test_stream.tell()
    assert num == len(test_data) * 2

    # Check all are within correct range
    test_stream.seek(0)
    encoded = test_stream.read(num)
    for b in encoded:
        assert A <= b < (A + 16)

    # Check reverse filter
    test_stream.seek(0)
    read_filter = ReadFilter(test_stream, 0)
    for b in test_data:
        assert b == read_filter.read(1)[0]



