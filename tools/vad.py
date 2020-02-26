#!/usr/bin/env python
# encoding: utf-8

"""
@author: zhanghe
@software: PyCharm
@file: vad.py
@time: 2020-02-24 14:29
@desc: VAD(Voice Activity Detection) 语音活动检测
"""

import collections
import contextlib
import json
import os
import sys
import wave

import webrtcvad

from tools.pcm import convert_wav

debug = False
wav_dir = 'apps/static/uploads/wav'
pcm_dir = 'apps/static/uploads/pcm'


def read_wave(path):
    """Reads a .wav file.
    Takes the path, and returns (PCM audio data, sample rate)."""
    # print(path)
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate."""
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Items(object):
    def __init__(self, s):
        self.s = s


class Frame(object):
    """Represents a "frame" of audio data."""

    def __init__(self, audio_bytes, timestamp, duration):
        self.bytes = audio_bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, pcm_audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration."""
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(pcm_audio):
        yield Frame(pcm_audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    """Filters out non-voiced audio frames.
    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.
    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.
    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.
    Arguments:
    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).
    Returns: A generator that yields PCM audio data."""
    vr = 0.99
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False
    voiced_frames = []
    a = []
    t = [0, 0]
    for frame in frames:
        debug and sys.stdout.write(
            '1' if vad.is_speech(frame.bytes, sample_rate) else '0')
        if not triggered:
            ring_buffer.append(frame)
            num_voiced = len([f for f in ring_buffer
                              if vad.is_speech(f.bytes, sample_rate)])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            # print('num_voiced: %d, vr * ring_buffer.maxlen: %d' % (num_voiced, vr * ring_buffer.maxlen))
            if num_voiced > vr * ring_buffer.maxlen:
                # sys.stdout.write('[%s - ' % (ring_buffer[0].timestamp,))
                t[0] = ring_buffer[0].timestamp
                triggered = True
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                voiced_frames.extend(ring_buffer)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append(frame)
            num_unvoiced = len([f for f in ring_buffer
                                if not vad.is_speech(f.bytes, sample_rate)])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            # print('num_unvoiced: %d, vr * ring_buffer.maxlen: %d' % (num_unvoiced, vr * ring_buffer.maxlen))
            if num_unvoiced > vr * ring_buffer.maxlen:
                # sys.stdout.write('%s]' % (frame.timestamp + frame.duration))
                t[1] = frame.timestamp + frame.duration
                a.append(t)
                t = [0, 0]
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
    if triggered:
        # sys.stdout.write('%s]' % (frame.timestamp + frame.duration))
        t[1] = frame.timestamp + frame.duration
        a.append(t)
    # sys.stdout.write('\n')
    yield Items(a)
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])


def run(wav_name, factor=0):
    wav_path = '%s/%s' % (wav_dir, wav_name)
    pcm_path = '%s/%s' % (pcm_dir, wav_name)
    # 判断wav文件是否存在
    if not os.path.isfile(wav_path):
        raise Exception('wav file [%s] is not exists!' % wav_path)
    if not os.path.isfile(pcm_path):
        convert_wav(wav_name)
    # 判断pcm文件是否存在
    if not os.path.isfile(pcm_path):
        raise Exception('pcm file [%s] is not converted!' % pcm_path)

    pcm_audio, sample_rate = read_wave(pcm_path)

    # 方案一（误差: 0、有噪点、段: 20）
    # frame_duration_ms = 10
    # padding_duration_ms = 210

    # 方案二（误差: 2、有噪点、段: 16）这里误差为噪点
    # frame_duration_ms = 30
    # padding_duration_ms = 300

    # 方案三（误差: 1、有噪点、段: 12）推荐，这里误差为噪点
    frame_duration_ms = 30
    padding_duration_ms = 450

    # 方案四（误差: 2、有噪点、段: 9）这里误差实际为1
    # frame_duration_ms = 30
    # padding_duration_ms = 600

    vad = webrtcvad.Vad(int(factor))
    frames = frame_generator(frame_duration_ms, pcm_audio, sample_rate)
    frames = list(frames)
    segments = vad_collector(sample_rate, frame_duration_ms, padding_duration_ms, vad, frames)
    r = []
    for i, segment in enumerate(segments):
        # 切割小段音频
        # path = 'chunk-%002d.wav' % (i,)
        # write_wave(path, segment, sample_rate)
        if isinstance(segment, Items):
            r = segment.s
    return r


def main(args):
    try:
        if len(args) < 1:
            sys.stderr.write(
                'Usage: tools/vad.py <wav file name>\n')
            sys.exit(1)
        r = run(*args)
        print(json.dumps(r, indent=4))
    except Exception as e:
        print(e.message)


if __name__ == '__main__':
    # python tools/vad.py test.wav

    # 第一个参数为wav文件存放路径，目前仅支持单通道，8K，16K，32K的采样率。
    # 第二个参数为敏感系数，取值0-3，越大表示越敏感，越激进，对细微的声音频段都可以识别出来；

    # 其中可调试的参数有：Channels、sample_with、sample_rate、vadmode、frame_duration(10, 20, 30)、 padding_duration_ms
    # 示例wav文件下载：73.wav 链接：https://pan.baidu.com/s/19YJB9u0zvCFGBLDRisK1KQ 密码：fgkf
    main(sys.argv[1:])
