"""Radiation conventions of the weather models (paper 01, Lemma 1)."""

import numpy as np

from ewf.weather.models import deaccumulate, deaverage


def test_deaccumulate_ecmwf_accumulations():
    # constant 300 W/m2 for 3 h, then 600 W/m2 for 3 h, then 0
    steps = [0, 3, 6, 9]
    acc = np.array([[0.0], [300 * 3 * 3600], [300 * 3 * 3600 + 600 * 3 * 3600], [2700 * 3600]])
    ghi, interval = deaccumulate(steps, acc)
    assert np.isnan(ghi[0, 0])
    np.testing.assert_allclose(ghi[1:, 0], [300, 600, 0])
    np.testing.assert_allclose(interval[1:], [3, 3, 3])


def test_deaccumulate_irregular_steps_and_noise():
    steps = [0, 3, 6, 12]
    acc = np.array([[0.0], [3600.0 * 3 * 100], [3600.0 * 3 * 100 - 1.0], [3600.0 * 3 * 100 + 6 * 3600 * 50]])
    ghi, interval = deaccumulate(steps, acc)
    assert ghi[2, 0] == 0          # tiny negative difference is clipped
    np.testing.assert_allclose(ghi[3, 0], 50, rtol=1e-6)
    assert interval[3] == 6


def test_deaverage_gfs_windows_reset_every_six_hours():
    # true hourly means
    true = np.array([0, 100, 200, 300, 400, 500, 600, 50, 60])   # for hours 1..8 (index = end hour)
    steps = list(range(0, 9))
    windows, avg = [None], [np.nan]
    for b in range(1, 9):
        a = 0 if b <= 6 else 6
        windows.append((a, b))
        avg.append(true[a + 1:b + 1].mean())
    ghi, interval = deaverage(steps, windows, np.array(avg)[:, None])
    np.testing.assert_allclose(ghi[1:, 0], true[1:], atol=1e-9)
    np.testing.assert_allclose(interval[1:], 1)


def test_deaverage_three_hourly_after_120h():
    steps = [120, 123, 126]
    windows = [(114, 120), (120, 123), (120, 126)]
    avg = np.array([[0.0], [90.0], [(90 * 3 + 30 * 3) / 6]])
    ghi, interval = deaverage(steps, windows, avg)
    np.testing.assert_allclose(ghi[1:, 0], [90, 30])
    np.testing.assert_allclose(interval[1:], [3, 3])
