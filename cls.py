import time
import copy
import pyaudio
import wave
import mido
import pygame


def ms_per_beat_to_bpm(ms_per_beat):
    bpm = 60000 / ms_per_beat
    return bpm


def extract_tempo_from_track(midi_file):
    for track in midi_file.tracks:
        for msg in track:
            if msg.is_meta and msg.type == "set_tempo":
                bpm = mido.tempo2bpm(msg.tempo)
                return bpm
    return 0


def extract_msgs_from_midi_track(midi_track):
    msgs = []
    for msg in midi_track:
        msgs.append(msg)
    return msgs


def extract_absolute_msgs_from_midi_track(midi_track, ticks_per_beat, new_ticks_per_beat):
    msgs = []
    absolute_time = 0
    for msg in midi_track:
        absolute_time = absolute_time + msg.time
        temp_msg = copy.copy(msg)
        temp_msg.time = absolute_time/(ticks_per_beat/new_ticks_per_beat)
        msgs.append(temp_msg)
    return msgs


def absolute_msgs_to_midi_track(midi_track):
    msgs = []
    for i in range(len(midi_track.msgs)):
        new_msg = copy.copy(midi_track.msgs[i])
        if i > 0:
            new_msg.time = (midi_track.msgs[i].time - midi_track.msgs[i-1].time)
        msgs.append(new_msg)
    return msgs


def bpm_to_ms_per_beat(bpm):
    ms_per_beat = 60000 / bpm
    return ms_per_beat


class MidiRecorder:
    def __init__(self, tracks):
        self.input_device = None
        self.tracks = tracks

        self.temp_midi_track = None
        self.temp_track = None

        self.relative_tick = 0
        self.is_active = False
        self.is_recording = False
        self.is_changing_active_state = False

    def record(self, clock):
        if self.is_active and self.is_recording:
            if clock.just_ticked:
                self.relative_tick += 1

            for msg in self.input_device.iter_pending():
                if not msg.type == "clock":
                    msg.time = self.relative_tick
                    self.temp_midi_track.append(msg)

    def update(self, clock):
        self.change_state_check(clock)
        self.record(clock)

    def stop_recording(self):
        self.temp_midi_track.name = "NewMidiRec"
        self.temp_track = TrackMidi(midi_track=self.temp_midi_track)
        self.temp_track.final_tick = self.relative_tick
        msg = mido.MetaMessage("end_of_track", time=self.relative_tick)
        self.temp_track.msgs.append(msg)

        self.temp_track.is_active = True
        self.tracks.append(self.temp_track)

        self.temp_track = None
        self.temp_midi_track = None

        self.relative_tick = 0
        self.is_active = False
        self.is_recording = False
        self.input_device.close()

    def change_active_state(self):
        if self.is_recording:
            self.stop_recording()
        elif not self.is_recording:
            self.temp_midi_track = mido.MidiTrack()
            self.is_active = True
            self.is_recording = True
            self.input_device = mido.open_input("minilogue:minilogue MIDI 2 24:1")

    def change_state_check(self, clock):
        if clock.relative_tick == 1 and clock.beat == 1 and self.is_changing_active_state:
            self.is_changing_active_state = False
            self.change_active_state()


class Track:
    def __init__(self):
        self.type = ""


class TrackMidi(Track):
    def __init__(self, midi_track=None, ticks_per_beat=192):
        self.ticks_per_beat = ticks_per_beat
        self.new_ticks_per_beat = ticks_per_beat  # This would change the resolution. If changed, it's necessary to change it as well in the Clock class

        self.relative_tick = 0
        self.final_tick = 0

        if midi_track is not None and midi_track.name != "NewMidiRec":
            self.msgs = extract_absolute_msgs_from_midi_track(midi_track, self.ticks_per_beat, self.new_ticks_per_beat)
            self.name = midi_track.name
        elif midi_track is not None and midi_track.name == "NewMidiRec":
            self.msgs = extract_msgs_from_midi_track(midi_track)
            self.name = midi_track.name
        
        self.type = "MIDI"
        self.id_num = 0
        self.final_tick = self.calculate_final_tick()
        self.bar_length = self.final_tick / self.ticks_per_beat

        self.is_active = True
        self.is_changing_active_state = False

    def calculate_final_tick(self):
        final_tick = self.ticks_per_beat * 8
        for msg in self.msgs:
            if msg.type == "end_of_track":
                final_tick = msg.time
        return final_tick


    def update(self, clock, output_device):
        if clock.just_ticked:
            self.relative_tick += 1
            if self.relative_tick > self.final_tick:
                self.relative_tick = 1

            if self.is_active:
                for msg in self.msgs:
                    if msg.time == self.relative_tick and not msg.is_meta:
                        output_device.send(msg)

        if self.relative_tick == self.final_tick and self.is_changing_active_state:
            self.change_active_state()
            self.is_changing_active_state = False

    def reset(self):
        self.relative_tick = 0

    def change_active_state(self):
        if self.is_active:
            self.is_active = False
        elif not self.is_active:
            self.is_active = True


class MidiManager:
    def __init__(self):
        self.output_device = mido.open_output("minilogue:minilogue MIDI 2 24:1")

        self.bpm = 97
        self.ms_per_beat = bpm_to_ms_per_beat(self.bpm)
        self.ticks_per_beat = 192

        self.midi_file = mido.MidiFile("metronome.midi")
        self.tracks = self.load_tracks()
        self.original_tracks = []

        for track in self.tracks:
            self.original_tracks.append(track)

        self.clock = Clock(self.ms_per_beat, self.ticks_per_beat)
        self.clock.is_active = False
        self.midi_recorder = MidiRecorder(self.tracks)

        self.is_active = False

    def save_midi_tracks_to_file(self):
        for track in self.tracks:
            if track not in self.original_tracks:
                msgs = []
                new_track = mido.MidiTrack()
                new_track.name = "MidiRecord"
                msgs = absolute_msgs_to_midi_track(track)
                for msg in msgs:
                    new_track.append(msg)
                self.midi_file.tracks.append(new_track)
        self.midi_file.save("midi/" + str(time.ctime()).replace(" ", "_") + ".midi")


    def activate(self):
        self.clock = Clock(self.ms_per_beat, self.ticks_per_beat)
        self.clock.is_active = True
        self.is_active = True

    def stop(self):
        self.output_device.reset()
        self.clock.is_active = False
        for track in self.tracks:
            track.relative_tick = 0
        self.is_active = False

    def load_tracks(self):
        tracks = []
        n = 0
        while n < len(self.midi_file.tracks):
            track_midi = TrackMidi(midi_track=self.midi_file.tracks[n], ticks_per_beat=self.ticks_per_beat)
            tracks.append(track_midi)
            n += 1
        return tracks

    def update(self):
        if self.is_active:
            self.clock.update()
            self.midi_recorder.update(self.clock)
            for track in self.tracks:
                track.update(self.clock, self.output_device)

    def on_exit(self):
        self.output_device.panic()


class AudioRecorder:
    def __init__(self):
        self.tracks = []

        self.relative_tick = 0

        self.is_active = False
        self.is_recording = False
        self.is_changing_active_state = False

        self.frames_per_buffer = 512
        self.rate = 44100
        self.channels = 1
        self.format = pyaudio.paInt16

        self.total_frames = []
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.wave_file = None

        self.index = 1

    def start_recording(self):
        self.is_active = True
        self.is_recording = True

        self.wave_file = wave.open("output" + str(self.index) + ".wav", 'wb')
        self.wave_file.setnchannels(self.channels)
        self.wave_file.setsampwidth(self.p.get_sample_size(self.format))
        self.wave_file.setframerate(self.rate)
        self.wave_file.writeframes(b''.join(self.total_frames))

        self.stream = self.p.open(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.frames_per_buffer, stream_callback=self.get_callback())
        self.stream.start_stream()

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wave_file.writeframes(in_data)
            return in_data, pyaudio.paContinue
        return callback

    def update(self, clock):
        self.change_state_check(clock)
        if clock.just_ticked:
            for track in self.tracks:
                track.update(clock)

            if self.is_active and self.is_recording:
                self.relative_tick += 1

    def stop_recording(self):
        self.stream.stop_stream()
        self.wave_file.close()
        self.stream.close()

        temp_track = TrackAudio(self.index)
        temp_track.name = "NewRec" + str(temp_track.index)
        temp_track.final_tick = self.relative_tick
        temp_track.is_active = True

        self.tracks.append(temp_track)

        self.relative_tick = 0

        self.index += 1
        self.is_recording = False

    def change_state_check(self, clock):
        if clock.relative_tick == 1 and clock.beat == 1 and self.is_changing_active_state:
            if not self.is_recording:
                self.start_recording()
            elif self.is_recording:
                self.stop_recording()
            self.is_changing_active_state = False


class TrackAudio(Track):
    def __init__(self, index):
        self.index = index
        self.id_num = 0

        self.type = "AUDIO"
        self.name = ""

        self.relative_tick = 0
        self.final_tick = 0

        self.volume_fade = 1.0

        self.is_active = True
        self.is_playing = True
        self.is_changing_active_state = False
        self.wave_file = pygame.mixer.Sound("output" + str(self.index) + ".wav")

    def stop_playing(self):
        self.wave_file.stop()

    def update(self, clock):
        if clock.just_ticked:
            self.relative_tick += 1
            if self.relative_tick > self.final_tick:
                self.relative_tick = 1

            if self.relative_tick == 1 and self.is_playing:
                self.wave_file.play()

        elif self.relative_tick == 1 and not self.is_playing:
            self.stop_playing()

        if self.relative_tick == self.final_tick and self.is_changing_active_state:
            self.change_active_state()
            self.is_changing_active_state = False

    def reset(self):
        self.relative_tick = 0

    def change_active_state(self):
        if self.is_active:
            self.is_active = False
        elif not self.is_active:
            self.is_active = True


class Clock:
    def __init__(self, ms_per_beat, ticks_per_beat):
        self.ticks_per_beat = ticks_per_beat
        self.seconds_to_next_tick = (ms_per_beat/self.ticks_per_beat) / 1000

        self.start_time = time.time()
        self.current_time = self.start_time
        self.final_time = self.start_time + self.seconds_to_next_tick

        self.relative_tick = 0
        self.absolute_tick = 0
        self.final_tick = self.ticks_per_beat * 4

        self.beat = 1

        self.just_ticked = False
        self.is_active = False

    def update(self):
        if self.is_active:
            self.current_time = time.time()
            self.just_ticked = False

            if self.current_time >= self.final_time:
                self.tick()

    def tick(self):
        self.just_ticked = True

        self.relative_tick += 1
        if self.relative_tick > self.final_tick:
            self.relative_tick = 1

        self.absolute_tick += 1
        self.final_time = self.start_time + (self.seconds_to_next_tick * self.absolute_tick) # self.start_time doesn't change in order to avoid time drifting over time

        if self.relative_tick % self.ticks_per_beat == 0:
            self.beat += 1
            if self.beat > 4:
                self.beat = 1

    def reset(self):
        self.start_time = time.time()
        self.current_time = self.start_time
        self.final_time = self.start_time + self.seconds_to_next_tick

        self.just_ticked = False

        self.relative_tick = 0
        self.absolute_tick = 0

        self.final_tick = self.ticks_per_beat * 4
