#!/usr/bin/env python

from __future__ import division, print_function, absolute_import

__author__ = "Marek Rudnicki"

from numpy.testing import assert_equal
from pandas.util.testing import assert_frame_equal

import numpy as np
import pandas as pd

import thorns as th



def test_from_array():

    fs = 1e3
    a = np.array(
        [[0,0,0,1,0,0],
         [0,2,1,0,0,0]]
    ).T

    result = th.make_trains(a, fs=fs)


    expected = th.make_trains(
        [np.array([3])/fs,
         np.array([1,1,2])/fs],
        duration = 6/fs
    )


    assert_frame_equal(
        expected,
        result
    )




def test_from_arrays():

    arrays = [
        [1,2,3],
        [1,3,5,7],
        [0,8]
    ]


    expected = {
        'spikes': arrays,
        'duration': np.repeat(10., len(arrays))
    }
    expected = pd.DataFrame(expected)





    result = th.spikes._arrays_to_trains(
        arrays,
        duration=10.0
    )

    assert_frame_equal(
        result,
        expected
    )




    result = th.make_trains(
        arrays,
        duration=10.0
    )
    assert_frame_equal(
        expected,
        result
    )




def test_make_empty_trains():

    spikes = [[], []]

    trains = th.make_trains(
        spikes
    )

    expected = pd.DataFrame({
        'spikes': spikes,
        'duration': np.repeat(0., len(spikes))
    })

    assert_frame_equal(
        trains,
        expected
    )






    trains = th.make_trains(
        spikes,
        duration=10
    )

    expected = pd.DataFrame({
        'spikes': spikes,
        'duration': np.repeat(10., len(spikes))
    })

    assert_frame_equal(
        trains,
        expected
    )





def test_trains_to_array():


    trains = th.make_trains(
        [[1], [2,3]],
        duration=5
    )

    result = th.spikes.trains_to_array(
        trains,
        fs=1
    )


    assert_equal(
        result,
        [[0,0],
         [1,0],
         [0,1],
         [0,1],
         [0,0]]
    )






def test_accumulate_spike_trains():

    trains = th.make_trains(
        [[1], [2], [3], []],
        cfs=[2,1,2,3]
    )

    accumulated = th.accumulate_spikes(trains)

    expected = th.make_trains(
        [[2], [1,3], []],
        cfs=[1,2,3]
    )

    assert_frame_equal(accumulated, expected)




def test_select_trains():

    trains = th.make_trains(
        [[1], [2], [3], [4]],
        duration=4,
        cfs=[0,0,1,1],
        idx=[0,1,0,1]
    )



    selected = th.sel(
        trains,
        cfs=1,
        idx=1
    )

    expected = th.make_trains(
        [[4]],
        duration=4,
        cfs=[1],
        idx=[1]
    )
    expected.index = [3]

    assert_frame_equal(
        selected,
        expected,
    )




def test_trim():

    trains = th.make_trains(
        [[1,2,3,4],
         [3,4,5,6]],
        duration=8,
        type='hsr'
    )


    trimmed = th.trim(trains, 2, 4)


    expected = th.make_trains(
        [[0,1,2], [1,2]],
        duration=2,
        type='hsr'
    )


    assert_frame_equal(
        trimmed,
        expected
    )



def test_fold_trains():
    trains = th.make_trains(
        [[1.1, 2.1, 3.1], [2.1, 3.1, 5.1]],
        duration=6.5,
        cf=[1,2]
    )

    folded = th.fold_trains(trains, 1)


    expected = th.make_trains(
        [[  ], [.1], [.1], [.1], [  ], [  ], [  ],
         [  ], [  ], [.1], [.1], [  ], [.1], [  ]],
        duration=[1, 1, 1, 1, 1, 1, 0.5,
                  1, 1, 1, 1, 1, 1, 0.5],
        cf=[1, 1, 1, 1, 1, 1, 1,
            2, 2, 2, 2, 2, 2, 2]
    )

    assert_frame_equal(
        folded,
        expected,
    )