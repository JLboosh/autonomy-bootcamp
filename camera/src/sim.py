"""SimCamera: YOUR Part 2 assignment.

A camera that makes up its own frames. Read ``src/fixed.py`` and its tests
first, then make ``tests/test_sim_camera.py`` pass:

    warg run camera test

``SimCamera(width=64, height=48)`` hands back a ``(height, width, 3)``
``uint8`` frame every time you ask, for as long as it's on, with ``index``
counting up from 0. Same rules as every camera
(``src/abstract_camera.py``), plus one:

A frame's pixels depend only on its index. Frame 2 always looks the same,
here or in any SimCamera built with the same size, and frames with different
indexes look different. Fill values, gradients, and
``numpy.random.default_rng(index)`` all work.
"""

import time

import numpy as np

from .abstract_camera import AbstractCamera
from .frame import CameraFrame


class SimCamera(AbstractCamera):

    """Fake camera that makes up its own frames."""

    def __init__(self, width: int = 64, height: int = 48) -> None:
        """Save the camera settings and set up its state."""

        self._width = width
        self._height = height
        self._initialized = False
        self._captures = 0
        self._last_timestamp = float("-inf")

    def initialize_camera(self) -> bool:
        """Turn the fake camera on and start counting from index 0."""

        self._initialized = True
        self._captures = 0
        return True

    def capture_frame(self) -> CameraFrame:
        """Make up the next frame."""

        if not self._initialized:
            raise RuntimeError(
                "capture_frame() called on a camera that is not initialized"
            )

        rng = np.random.default_rng(self._captures)

        rgb = rng.integers(
            0,
            256,
            size=(self._height, self._width, 3),
            dtype=np.uint8,
        )

        frame = CameraFrame(
            rgb=rgb.copy(),
            timestamp=self._next_timestamp(),
            index=self._captures,
        )

        self._captures += 1

        return frame

    def stop(self) -> None:
        """Turn the fake camera off. Safe to call more than once."""

        self._initialized = False

    def _next_timestamp(self) -> float:
        """Return a timestamp that is strictly greater than the previous."""

        timestamp = time.monotonic()

        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1e-6

        self._last_timestamp = timestamp

        return timestamp


        




