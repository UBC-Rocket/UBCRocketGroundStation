import os

import numpy
import pytest
from matplotlib import pyplot

from util.detail import LOCAL
from main_window.competition.mapping import mapbox_utils


@pytest.fixture()
def ubc_point_1():
    ubc_point_1 = mapbox_utils.MapPoint(
        49.266904, -123.252976
    )  # 49.284162, -123.2766960
    return ubc_point_1


@pytest.fixture()
def ubc_point_2():
    ubc_point_2 = mapbox_utils.MapPoint(
        49.265903, -123.251222
    )  # 49.239184, -123.210088
    return ubc_point_2


@pytest.fixture()
def hennings_tile():
    hennings_tile = mapbox_utils.MapTile(41322, 89729, 18)
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

    def test_get_image_no_maps(self, hennings_tile, mocker):
        mocker.patch("main_window.competition.mapping.mapbox_utils.maps", None)
        mocked_isfile = mocker.patch("main_window.competition.mapping.mapbox_utils.os.path.isfile")

        mocked_isfile.return_value = False

        i = hennings_tile.getImage()

        numpy.testing.assert_array_equal(
            i, numpy.zeros((mapbox_utils.TILE_SIZE, mapbox_utils.TILE_SIZE, 3))
        )

    def test_get_image_fail(self, hennings_tile, mocker):
        mocked_isfile = mocker.patch("main_window.competition.mapping.mapbox_utils.os.path.isfile")

        mocked_isfile.return_value = False

        i = hennings_tile.getImage()

        numpy.testing.assert_array_equal(
            i, numpy.zeros((mapbox_utils.TILE_SIZE, mapbox_utils.TILE_SIZE, 3))
        )

    def test_get_image_exists(self, hennings_tile, mocker):
        hennings_image = pyplot.imread(
            os.path.join(LOCAL, "tests", "test_mapbox_utils", "41322_89729.jpg"), "jpeg"
        )
        mocked_tile = mocker.patch("main_window.competition.mapping.mapbox_utils.maps.tile")
        mocked_tile.return_value.status_code = 200
        mocked_tile.return_value.content = hennings_image

        i = hennings_tile.getImage()

        numpy.testing.assert_array_equal(i, hennings_image)

    @pytest.mark.parametrize("success", [True, False])
    def test_image_exists(self, hennings_tile, mocker, success):
        mocked_isfile = mocker.patch("main_window.competition.mapping.mapbox_utils.os.path.isfile")

        mocked_isfile.return_value = success

        ie = hennings_tile.imageExists()

        mocked_isfile.assert_called_once()
        mocked_isfile.assert_called_with(
            os.path.join(mapbox_utils.MAPBOX_CACHE, "raw", "18", "41322_89729" + ".png")
        )
        assert ie is success


class TestTileGrid:
    @pytest.fixture()
    def ubc_tile_grid(self, ubc_point_1, ubc_point_2):
        ubc_tile_array = mapbox_utils.TileGrid(ubc_point_1, ubc_point_2, 18)
        return ubc_tile_array

    def test_gen_tile_array(self, ubc_tile_grid):
        ta = [
            [
                mapbox_utils.MapTile(41321, 89729, 18),
                mapbox_utils.MapTile(41322, 89729, 18),
                mapbox_utils.MapTile(41323, 89729, 18),
            ],
            [
                mapbox_utils.MapTile(41321, 89730, 18),
                mapbox_utils.MapTile(41322, 89730, 18),
                mapbox_utils.MapTile(41323, 89730, 18),
            ],
        ]

        ubc_tile_grid.genTileArray()

        numpy.testing.assert_array_equal(ta, ubc_tile_grid.ta)

    def test_download_array_images(self, ubc_tile_grid, mocker):
        mocked_image_exists = mocker.patch("main_window.competition.mapping.mapbox_utils.MapTile.imageExists")
        mocked_image_exists.return_value = False
        mocked_get_image = mocker.patch("main_window.competition.mapping.mapbox_utils.MapTile.getImage")

        ubc_tile_grid.downloadArrayImages()

        assert mocked_get_image.call_count == 3 * len(ubc_tile_grid.ta) * len(
            ubc_tile_grid.ta[0]
        )

    def test_gen_stitched_map(self, ubc_tile_grid):
        hennings_image = pyplot.imread(
            os.path.join(
                LOCAL,
                "tests",
                "test_mapbox_utils",
                "output_18_41321-41323_89729-89730.png",
            ),
            "jpeg",  # Needed to make sure MPL doesn't use Pillow and return decimals.
        )
        
        ubc_tile_grid.downloadArrayImages()
        stitched_map = ubc_tile_grid.genStitchedMap()

        # assert_allclose because linux vs. windows can decode the images slightly differently
        # https://github.com/python-pillow/Pillow/issues/3833
        # https://github.com/python-pillow/Pillow/issues/4686
        numpy.testing.assert_allclose(hennings_image[:,:,:3], stitched_map[:,:,:3], rtol=0, atol=20) # Some systems return alpha channels for one and not the other, needs to be removed before comparison


def test_point_to_tile(ubc_point_1):
    t = mapbox_utils.pointToTile(ubc_point_1, 18)

    assert t == mapbox_utils.MapTile(41321, 89729, 18)
