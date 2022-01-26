''' omband, midi and audio looper
Copyright (C) 2021,2022  Marcos Redwood (marcos.rc91@gmail.com)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
'''

import time
import configparser
import copy
import wave
import os

import pyaudio
import mido
import pygame


# These are some functions that will be used later.

# This one transforms ms_per_beat to bpm
def ms_per_beat_to_bpm(ms_per_beat):
    bpm = 60000 / ms_per_beat
    return bpm

# This one extracts tempo from the midi file. It returns the bpm
def extract_tempo_from_track(midi_file):
    for track in midi_file.tracks:
        for msg in track:
            if msg.is_meta and msg.type == "set_tempo":
                bpm = mido.tempo2bpm(msg.tempo)
                return bpm
    return 0

# This one extracts a list of all the messages in a midi_track
def extract_msgs_from_midi_track(midi_track):
    msgs = []
    for msg in midi_track:
        msgs.append(msg)
    return msgs

# This one extracts the absolute time from a midi_track (according to the tempo)
def extract_absolute_msgs_from_midi_track(midi_track, ticks_per_beat, new_ticks_per_beat):
    msgs = []
    absolute_time = 0
    for msg in midi_track:
        absolute_time = absolute_time + msg.time
        temp_msg = copy.copy(msg)
        temp_msg.time = absolute_time/(ticks_per_beat/new_ticks_per_beat)
        if temp_msg.time == 0 and not temp_msg.is_meta:
            temp_msg.time = 1 # This changes de 0 time of the first note_on message in order to avoid skipping the first note.
        msgs.append(temp_msg)
    return msgs

# This one returns the midi messages with the corrected time (relative time between messages)
def absolute_msgs_to_midi_track(midi_track):
    msgs = []
    for i in range(len(midi_track.msgs)):
        new_msg = copy.copy(midi_track.msgs[i])
        if i > 0:
            new_msg.time = (midi_track.msgs[i].time - midi_track.msgs[i-1].time)
        msgs.append(new_msg)
    return msgs

# This one transforms the bpm to ms_per_beat
def bpm_to_ms_per_beat(bpm):
    ms_per_beat = 60000 / bpm
    return ms_per_beat

# This function returns a value from the config file
def string_to_config_parser(content_to_parse):
    config = configparser.ConfigParser()
    config.read("omband.conf")
    return config[content_to_parse[0]][content_to_parse[1]]



# This class is the initial configuration screen
class ConfInit:
    def __init__(self):
        self.config_file_path = "omband.conf"
        self.bpm = 120
        self.ticks_per_beat = 0

        self.input_device_string = ""
        self.output_device_string = ""

        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)

    def show_config_file(self):
        print("There's an omband.conf file. We found the next configuration:\n")
        print("Ports:")
        print(" Input_device = " + self.config["Ports"]["input_device"])
        print(" Output_device = " + self.config["Ports"]["output_device"])
        print("Midi:")
        print(" bpm = " + self.config["Midi"]["bpm"])
        print(" Ticks per beat (192 by default) = " + self.config["Midi"]["ticks_per_beat"])
        print(" File to load ('metronome.midi' by default) = " + self.config["Midi"]["file_to_load"])

        command_is_valid = False
        while not command_is_valid:
            command = input("\nProceed with this configuration? (Y/n) ")
            if command.lower() == "y" or command == "":
                print("OK")
                command_is_valid = True
            elif command.lower() == "n":
                print("OK, no")
                command_is_valid = True
                self.ask_for_parameters()



    def ask_for_parameters(self):
        print("asking")

    def run(self):
        os.system('clear')
        self.show_config_file()


# This class will be the one in charge to record a new midi track
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

    # This method appends the midi messages from the input device to self.temp_midi_track
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

    # This method stops the recording. It gives a name to the new midi track, it puts a final_tick to it and it adds a final meta message, "end of track". After that, it resets some variables.
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
            self.input_device = mido.open_input(string_to_config_parser(["Ports", "input_device"]))

    # This method checks, at the beginning of each beat number1 whether it's necessary to change the state to active/inactive
    def change_state_check(self, clock):
        if clock.relative_tick == 1 and clock.beat == 1 and self.is_changing_active_state:
            self.is_changing_active_state = False
            self.change_active_state()


# This class is only a parent to other two classes: TrackMidi and TrackAudio
class Track:
    def __init__(self):
        self.type = ""


# This is a TrackMidi. Its main purpose is to send the messages it has to the output device
class TrackMidi(Track):
    def __init__(self, midi_track=None, ticks_per_beat=int(string_to_config_parser(["Midi", "ticks_per_beat"]))):
        self.ticks_per_beat = ticks_per_beat
        self.new_ticks_per_beat = ticks_per_beat

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


# This class saves midi files and activates the update method of the midi tracks
class MidiManager:
    def __init__(self):
        self.output_device = mido.open_output(string_to_config_parser(["Ports", "output_device"]))

        self.bpm = int(string_to_config_parser(["Midi", "bpm"]))
        self.ms_per_beat = bpm_to_ms_per_beat(self.bpm)
        self.ticks_per_beat = int(string_to_config_parser(["Midi", "ticks_per_beat"]))

        self.midi_file = mido.MidiFile(string_to_config_parser(["Midi", "file_to_load"]))
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
        if not os.path.exists('midi'):
            os.makedirs('midi')
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

# This class records the audio
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

    # This method starts recording. It creates a stream of audio
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

    # This one stops recording and creates a new trackAudio object
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


# This is the class TrackAudio. All audio tracks are of this kind
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


# This class is the one that keeps ticking. It's the "master clock"
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
