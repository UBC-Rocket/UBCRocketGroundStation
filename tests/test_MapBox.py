import os

import numpy
import pytest
from matplotlib import pyplot

import MapBox
from detail import LOCAL


@pytest.fixture()
def ubc_point_1():
    ubc_point_1 = MapBox.MapPoint(49.266904, -123.252976)  # 49.284162, -123.2766960
    return ubc_point_1


@pytest.fixture()
def ubc_point_2():
    ubc_point_2 = MapBox.MapPoint(49.265903, -123.251222)  # 49.239184, -123.210088
    return ubc_point_2


@pytest.fixture()
def hennings_tile():
    hennings_tile = MapBox.MapTile(41322, 89729, 18)
    return hennings_tile


class TestMapPoint:
    def test_get_pixel_x(self, ubc_point_1):
        x = ubc_point_1.getPixelX(18)

        assert x == 21156823

    def test_get_pixel_y(self, ubc_point_1):
        y = ubc_point_1.getPixelY(18)

        assert y == 45941250

    def test_get_tile_x(self, ubc_point_1):
        tx = ubc_point_1.getTileX(18)

        assert tx == 41321

    def test_get_tile_y(self, ubc_point_1):
        ty = ubc_point_1.getTileY(18)

        assert ty == 89729


class TestMapTile:
    def test_get_name(self, hennings_tile):
        name = hennings_tile.getName

        assert name == "41322_89729"

    def test_get_image_no_maps(self, hennings_tile, mocker):
        mocker.patch("MapBox.maps", None)
        mocked_isfile = mocker.patch("MapBox.os.path.isfile")

        mocked_isfile.return_value = False

        i = hennings_tile.getImage()

        numpy.testing.assert_array_equal(i, numpy.zeros((MapBox.TILE_SIZE, MapBox.TILE_SIZE, 3)))

    def test_get_image_fail(self, hennings_tile, mocker):
        mocked_isfile = mocker.patch("MapBox.os.path.isfile")

        mocked_isfile.return_value = False

        i = hennings_tile.getImage()

        numpy.testing.assert_array_equal(i, numpy.zeros((MapBox.TILE_SIZE, MapBox.TILE_SIZE, 3)))

    def test_get_image_exists(self, hennings_tile, mocker):
        hennings_image = pyplot.imread(os.path.join(LOCAL, "tests", "test_MapBox", "41322_89729.jpg"), "jpeg")
        mocked_tile = mocker.patch("MapBox.maps.tile")
        mocked_tile.return_value.status_code = 200
        mocked_tile.return_value.content = hennings_image

        i = hennings_tile.getImage()

        numpy.testing.assert_array_equal(i, hennings_image)

    @pytest.mark.parametrize("success", [True, False])
    def test_image_exists(self, hennings_tile, mocker, success):
        mocked_isfile = mocker.patch("MapBox.os.path.isfile")

        mocked_isfile.return_value = success

        ie = hennings_tile.imageExists

        mocked_isfile.assert_called_once()
        mocked_isfile.assert_called_with(os.path.join(LOCAL, "raw", "18", "41322_89729" + ".png"))
        assert ie is success


class TestTileGrid:
    @pytest.fixture()
    def ubc_tile_grid(self, ubc_point_1, ubc_point_2):
        ubc_tile_array = MapBox.TileGrid(ubc_point_1, ubc_point_2, 18)
        return ubc_tile_array

    def test_gen_tile_array(self, ubc_tile_grid):
        ta = [[MapBox.MapTile(41321, 89729, 18), MapBox.MapTile(41322, 89729, 18), MapBox.MapTile(41323, 89729, 18)],
              [MapBox.MapTile(41321, 89730, 18), MapBox.MapTile(41322, 89730, 18), MapBox.MapTile(41323, 89730, 18)]]

        ubc_tile_grid.genTileArray()

        numpy.testing.assert_array_equal(ta, ubc_tile_grid.ta)

    def test_download_array_images(self, ubc_tile_grid, mocker):
        mocked_image_exists = mocker.patch("MapBox.MapTile.imageExists")
        mocked_image_exists.return_value = False
        mocked_get_image = mocker.patch("MapBox.MapTile.getImage")

        ubc_tile_grid.downloadArrayImages()

        assert mocked_get_image.call_count == 3 * len(ubc_tile_grid.ta) * len(ubc_tile_grid.ta[0])

    def test_gen_stitched_map(self, ubc_tile_grid):
        hennings_image = pyplot.imread(
            os.path.join(
                LOCAL,
                "tests",
                "test_MapBox",
                "output_18_41321-41323_89729-89730.png",
            ),
            "jpeg",  # Needed to make sure MPL doesn't use Pillow and return decimals.
        )
        ubc_tile_grid.downloadArrayImages()
        stitched_map = ubc_tile_grid.genStitchedMap()

        numpy.testing.assert_array_equal(hennings_image, stitched_map)


def test_point_to_tile(ubc_point_1):
    t = MapBox.pointToTile(ubc_point_1, 18)

    assert t == MapBox.MapTile(41321, 89729, 18)
