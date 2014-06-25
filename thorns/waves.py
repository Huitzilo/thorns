#!/usr/bin/env python

"""DSP related functions.

"""


from __future__ import division, print_function, absolute_import

__author__ = "Marek Rudnicki"

import numpy as np
import scipy.signal as dsp



def align(a, fs_a, b, fs_b):
    """Align two signals (a,b) so that they have the same sampling
    frequency (resample to lower fs) and length (trim longer signal).

    """
    assert a.ndim == 1
    assert b.ndim == 1

    if fs_a == fs_b:
        fs = fs_a
    elif fs_a > fs_b:
        fs = fs_b
        a = resample(a, fs_a, fs)
    elif fs_a < fs_b:
        fs = fs_a,
        b = resample(b, fs_b, fs)


    if len(a) > len(b):
        a = a[0:len(b)]
    elif len(a) < len(b):
        b = b[0:len(a)]

    return a, b, fs






def signal_to_noise_ratio_db(signal, noise):
    assert signal.shape == noise.shape

    snr_db = 20 * np.log10(
        rms(signal) / rms(noise)
    )

    return snr_db


snr_db = signal_to_noise_ratio_db
snr = signal_to_noise_ratio_db


def root_mean_square(signal):
    return np.sqrt( np.mean(signal**2) )

rms = root_mean_square



def fft_filter(signal, fs, band):

    lo, hi = band

    freqs = np.linspace(0, fs/2, len(signal)/2+1)


    signal_fft = np.fft.rfft(signal)
    signal_fft[ (freqs < lo) | (freqs > hi) ] = 0

    filtered = np.fft.irfft(signal_fft)

    return filtered




def set_dbspl(signal, dbspl):
    p0 = 20e-6
    rms = np.sqrt( np.sum(signal**2) / signal.size )

    scalled = signal * 10**(dbspl / 20.0) * p0 / rms

    return scalled


def resample(signal, fs, new_fs):
    new_signal = dsp.resample(signal, len(signal)*new_fs/fs)
    return new_signal



def trim(a,b):
    assert a.ndim == b.ndim == 1

    length = min([len(a), len(b)])
    aa = a[0:length]
    bb = b[0:length]

    return aa, bb




def ramped_tone(
        fs,
        freq,
        duration,
        pad=0,
        ramp=2.5e-3,
        dbspl=None
):
    """Generate ramped tone singal.

    Parameters
    ----------

    fs : float
        Sampling frequency in Hz.
    freq : float
        Frequency of the tone in Hz.
    duration : float
        Duration of the tone in seconds.
    pad : float, optional
        Duration of the pad in seconds (default is 0)
    ramp : float, optional
        Duration of the ramp in seconds (default is 2.5 ms)
    dbspl : float, optional
        Amplitude of the tone in dB SPL.  If None (default), no scaling.


    Returns
    -------

    array_like
        The output tone with optional padding.


    """
    assert ramp < duration/2

    t = np.arange(0, duration, 1/fs)
    s = np.sin(2 * np.pi * t * freq)
    if dbspl != None:
        s = set_dbspl(s, dbspl)

    if ramp != 0:
        ramp_signal = np.linspace(0, 1, np.ceil(ramp * fs))
        s[0:len(ramp_signal)] = s[0:len(ramp_signal)] * ramp_signal
        s[-len(ramp_signal):] = s[-len(ramp_signal):] * ramp_signal[::-1]


    pad_signal = np.zeros(pad * fs)
    sound = np.concatenate( (s, pad_signal) )

    return sound



def white_noise(
        fs,
        duration,
        band,
        seed,
        ramp=2.5e-3,
        pad=0,
        dbspl=None
):

    np.random.seed(seed)


    lo, hi = band

    n = int( np.round(duration * fs) )
    freqs_abs = np.abs( np.fft.fftfreq(n, 1/fs) )

    passband_mask = (freqs_abs > lo) & (freqs_abs < hi)

    angles = np.random.rand(n) * 2 * np.pi

    reals = np.cos(angles)
    imags = np.sin(angles)

    ss = reals + 1j*imags
    ss[ np.invert(passband_mask) ] = 0

    s = np.fft.ifft(ss).real

    s = set_dbspl(s, dbspl)


    ### Ramping
    ramp_signal = np.linspace(0, 1, np.round(ramp*fs))
    s[0:len(ramp_signal)] = s[0:len(ramp_signal)] * ramp_signal
    s[-len(ramp_signal):] = s[-len(ramp_signal):] * ramp_signal[::-1]


    ### Padding
    pad_signal = np.zeros(pad * fs)
    s = np.concatenate( (s, pad_signal) )


    return s





def electrical_pulse(
        fs,
        amplitudes,
        durations,
        gap=0,
        pad=0,
        charge=None
):

    assert len(amplitudes) == len(durations)

    gap_signal = np.zeros(gap * fs)
    pad_signal = np.zeros(pad * fs)

    signals = []
    for amp,dur in zip(amplitudes, durations):
        signals.append( amp * np.ones(dur * fs) )
        signals.append( gap_signal )

    # Remove the last gap
    signals.pop(-1)


    signals.append( pad_signal )

    signal = np.concatenate( signals )


    if charge is not None:
        c = np.sum(np.abs(signal))/fs
        signal /= c


    return signal



def generate_electrical_amplitudes(
        durations,
        polarity,
        ratio=None,
):

    assert (ratio is None) or (ratio >= 0)


    ### Normalize polarity
    if polarity in ('c', 'cathodic', -1):
        polarity = -1
    elif polarity in ('a', 'anodic', 1):
        polarity = 1
    else:
        raise RuntimeError("Unknown polarity")


    ### Monophasic pulse
    if len(durations) == 1:
        amplitude = polarity / durations[0]
        amplitudes = (amplitude,)


    ### Biphasic pulse
    elif len(durations) == 2:
        assert (ratio is None) or (ratio == 1)
        amplitudes = (
            +1*polarity * (0.5 / durations[0]),
            -1*polarity * (0.5 / durations[1])
        )


    ### Triphasic pulse
    elif len(durations) == 3:
        amplitudes = (
            +1*polarity * (0.5 * ratio / durations[0]),
            -1*polarity * (0.5 / durations[1]),
            +1*polarity * (0.5 * (1-ratio) / durations[2])
        )

    else:
        raise RuntimeError("Unknown pulse shape")

    return amplitudes



def t(signal, fs):
    """
    Return time vector for the signal.

    signal: signal
    fs: sampling frequency in Hz

    """
    tmax = (len(signal)-1) / fs
    return np.linspace(0, tmax, len(signal))



def amplitude_modulated_tone(
        fs,
        fm,
        fc,
        m,
        duration,
        pad=0,
        ramp=2.5e-3,
        dbspl=None
):
    """Generate amplitude modulated tone.

    fs : float
        Sampling frequency in Hz.
    fm : float
        Modulation frequency in Hz.
    fc : float
        Carrier frequency in Hz.
    m : float
        Modulation depth <0-1>.
    duration : float
        Tone duration in seconds.
    pad : float, optional
        Duration of the pad in seconds (default is 0)
    ramp : float, optional
        Duration of the ramp in seconds (default is 2.5 ms)
    dbspl : float, optional
        Amplitude of the tone in dB SPL.  If None (default), no scaling.

    """
    assert ramp < duration/2
    assert 0 <= m <= 1
    assert fs/2 >= fc > fm

    t = np.arange(0, duration, 1/fs)
    s = (1 + m*np.sin(2*np.pi*fm*t)) * np.sin(2*np.pi*fc*t)

    if dbspl != None:
        s = set_dbspl(s, dbspl)

    if ramp != 0:
        ramp_signal = np.linspace(0, 1, np.ceil(ramp * fs))
        s[0:len(ramp_signal)] = s[0:len(ramp_signal)] * ramp_signal
        s[-len(ramp_signal):] = s[-len(ramp_signal):] * ramp_signal[::-1]


    pad_signal = np.zeros(pad * fs)
    sound = np.concatenate( (s, pad_signal) )

    return sound


am_tone = amplitude_modulated_tone