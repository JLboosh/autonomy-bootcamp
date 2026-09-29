"""
TODO(bootcamper): write the tests for ``src/waypoint_utils.py`` in here.

The example below covers files that parse fine: with and without ``home``,
and files with comments and blank lines in them. The rest is yours:

- Bad data: a file whose top level isn't a mapping, waypoints missing
  ``lat``, ``lon``, or ``alt``, values that aren't numbers, YAML that
  doesn't parse, and a file that isn't there.
- Out of range: latitudes past +/-90 and longitudes past +/-180 get
  rejected.
- Nothing to work with: an empty file, an empty ``waypoints`` list, and
  ``sort_clockwise_sweep`` given a list of 0 or 1 waypoints.
- ``east_north_coordinate_offset_m``: offsets you worked out yourself,
  compared with ``pytest.approx``. Never use ``==`` on meters.
- Ordering: with no ``home``, ``sort_clockwise_sweep`` goes clockwise
  starting from north.
- With a ``home``: the order starts in home's direction instead, and goes
  back to starting at north if home is right on top of the centroid.
- Two waypoints in the same direction: the closer one comes first.
- Parsing gives you frozen ``Coordinate`` objects that can't be changed.

Graded by ``warg run utils grade-tests``: pass on the real code, 90% branch
coverage, and fail on every broken copy in ``grader/mutants/``.
"""

from dataclasses import FrozenInstanceError

import pytest

from src.types import Coordinate
from src.waypoint_utils import (
    east_north_coordinate_offset_m,
    parse_waypoints_file,
    sort_clockwise_sweep,
)

# The helper and the test below are given to you.


def write_to_tmp_waypoints_file(tmp_path, text):
    """Write ``text`` to a YAML file and hand back its path.

    ``tmp_path`` is a pytest fixture: a fresh empty directory per test.
    """
    path = tmp_path / "waypoints.yaml"
    path.write_text(text)
    return path


# One test, three files. ``parametrize`` runs the test body once per
# ``(text, expected)`` pair, and ``ids`` names each run so a failure tells you
# which file broke.
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            """
            home: {lat: 1, lon: 2, alt: 3}
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
        (
            """
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
              - {lat: 7, lon: 8, alt: 9}
            """,
            (None, [Coordinate(4, 5, 6), Coordinate(7, 8, 9)]),
        ),
        (
            """
            # a lap

            home: {lat: 1, lon: 2, alt: 3}

            waypoints:
              # first leg
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
    ],
    ids=["home-and-waypoints", "no-home", "comments-and-blank-lines"],
)
def test_parse_waypoints_file_success(tmp_path, text, expected):
    path = write_to_tmp_waypoints_file(tmp_path, text)
    assert parse_waypoints_file(path) == expected


def test_parse_waypoints_file_missing_file(tmp_path):
    path = tmp_path / "does_not_exist.yaml"

    with pytest.raises(OSError):
        parse_waypoints_file(path)




def test_parse_waypoints_file_top_level_not_mapping(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        - hello
        - world
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)



@pytest.mark.parametrize("missing_key", ["lat", "lon", "alt"])
def test_parse_waypoints_file_missing_coordinate_key(tmp_path, missing_key):
    values = {
        "lat": 43.0,
        "lon": -80.0,
        "alt": 15,
    }
    del values[missing_key]

    path = write_to_tmp_waypoints_file(
        tmp_path,
        f"""
        waypoints:
          - {values}
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


@pytest.mark.parametrize("bad_key", ["lat", "lon", "alt"])
def test_parse_waypoints_file_non_numeric_value(tmp_path, bad_key):
    values = {
        "lat": 43.0,
        "lon": -80.0,
        "alt": 15,
    }
    values[bad_key] = "not-a-number"

    path = write_to_tmp_waypoints_file(
        tmp_path,
        f"""
        waypoints:
          - {values}
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


def test_parse_waypoints_file_invalid_yaml(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - lat: 43.0
            lon: -80.0
            alt: 15
          this is invalid yaml
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (91, 0),
        (-91, 0),
        (0, 181),
        (0, -181),
    ],
)
def test_parse_waypoints_file_out_of_range_coordinate(tmp_path, lat, lon):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        f"""
        waypoints:
          - lat: {lat}
            lon: {lon}
            alt: 15
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


def test_parse_waypoints_file_empty_file(tmp_path):
    path = write_to_tmp_waypoints_file(tmp_path, "")

    assert parse_waypoints_file(path) == (None, [])


def test_parse_waypoints_file_empty_waypoints(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints: []
        """,
    )

    assert parse_waypoints_file(path) == (None, [])


def test_parse_waypoints_file_waypoints_not_list(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          lat: 43.0
          lon: -80.0
          alt: 15
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)


def test_east_north_coordinate_offset_north():
    east, north = east_north_coordinate_offset_m(
        43.0, -80.0,
        43.001, -80.0,
    )

    assert east == pytest.approx(0.0, abs=0.01)
    assert north == pytest.approx(111.2, abs=0.1)


def test_east_north_coordinate_offset_east():
    east, north = east_north_coordinate_offset_m(
        43.0, -80.0,
        43.0, -79.999,
    )

    assert east == pytest.approx(81.32, abs=0.01)
    assert north == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize(
    ("from_lat", "from_lon", "to_lat", "to_lon", "expected_east_sign", "expected_north_sign"),
    [
        (43.0, -80.0, 42.999, -80.0, 0, -1),
        (43.0, -80.0, 43.0, -80.001, -1, 0),
    ],
)
def test_east_north_coordinate_offset_directions(
    from_lat,
    from_lon,
    to_lat,
    to_lon,
    expected_east_sign,
    expected_north_sign,
):
    east, north = east_north_coordinate_offset_m(
        from_lat, from_lon, to_lat, to_lon
    )

    if expected_east_sign < 0:
        assert east < 0
    else:
        assert east == pytest.approx(0.0, abs=0.01)

    if expected_north_sign < 0:
        assert north < 0
    else:
        assert north == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize(
    "waypoints",
    [
        [],
        [Coordinate(43.0, -80.0, 15.0)],
    ],
)
def test_sort_clockwise_sweep_zero_or_one_waypoint(waypoints):
    assert sort_clockwise_sweep(waypoints) == waypoints


def test_sort_clockwise_sweep_starts_north_and_goes_clockwise():
    north = Coordinate(43.001, -80.0, 15.0)
    east = Coordinate(43.0, -79.999, 15.0)
    south = Coordinate(42.999, -80.0, 15.0)
    west = Coordinate(43.0, -80.001, 15.0)

    waypoints = [south, west, east, north]

    result = sort_clockwise_sweep(waypoints)

    assert result == [north, east, south, west]


def test_sort_clockwise_sweep_starts_from_home():
    north = Coordinate(43.001, -80.0, 15.0)
    east = Coordinate(43.0, -79.999, 15.0)
    south = Coordinate(42.999, -80.0, 15.0)
    west = Coordinate(43.0, -80.001, 15.0)

    home = Coordinate(43.0, -79.9995, 15.0)

    waypoints = [south, west, north, east]

    result = sort_clockwise_sweep(waypoints, home)

    assert result == [east, south, west, north]

def test_sort_clockwise_sweep_home_at_centroid_starts_north():
    north = Coordinate(43.001, -80.0, 15.0)
    east = Coordinate(43.0, -79.999, 15.0)
    south = Coordinate(42.999, -80.0, 15.0)
    west = Coordinate(43.0, -80.001, 15.0)

    home = Coordinate(43.0, -80.0, 15.0)

    waypoints = [south, west, east, north]

    result = sort_clockwise_sweep(waypoints, home)

    assert result == [north, east, south, west]


def test_sort_clockwise_sweep_same_angle_closer_first():
    close_north = Coordinate(43.001, -80.0, 15.0)
    far_north = Coordinate(43.002, -80.0, 15.0)
    east = Coordinate(43.0, -79.999, 15.0)
    south = Coordinate(42.999, -80.0, 15.0)
    west = Coordinate(43.0, -80.001, 15.0)

    waypoints = [far_north, west, south, east, close_north]

    result = sort_clockwise_sweep(waypoints)

    assert result[0] == close_north
    assert result[1] == far_north


def test_parse_waypoints_file_coordinates_are_frozen(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        home: {lat: 43.0, lon: -80.0, alt: 15}
        waypoints:
          - {lat: 43.001, lon: -80.001, alt: 20}
        """,
    )

    home, waypoints = parse_waypoints_file(path)

    assert home is not None

    with pytest.raises(FrozenInstanceError):
        home.lat = 44.0

    with pytest.raises(FrozenInstanceError):
        waypoints[0].lon = -81.0

def test_parse_waypoints_file_coordinate_entry_not_mapping(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - hello
        """,
    )

    with pytest.raises(ValueError):
        parse_waypoints_file(path)
