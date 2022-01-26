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

import curses
import cls
import pyaudio


class InfoWindow:
    def __init__(self, max_x, max_y):
        self.max_x, self.max_y = max_x, max_y
        self.display = curses.newwin(3, self.max_x-1, 1, 1)
        self.bpm = 0
        self.is_active = False
        self.beat = 0

    def update(self, clock):
        if clock.is_active:
            self.is_active = True
            self.beat = clock.beat
        if not clock or not clock.is_active:
            self.is_active = False

    def draw(self, midi_manager, audio_recorder):
        self.display.erase()
        self.display.clrtoeol()
        self.display.border(1)

        if not self.is_active:
            self.display.addstr(1, 3, "STOPPED")
            self.display.addstr(0, 0, "[ ]" * 4)
        elif self.is_active:
            self.display.addstr(1, 6, str(self.beat))
            self.display.addstr(0, 0, "[+]" * self.beat + "[ ]" * (4 - self.beat))
        self.display.addstr(1, 11, "|" + str(self.bpm) + " bpm.|")

        if midi_manager.midi_recorder.is_changing_active_state:
            self.display.addstr(1, 20, "MIDI_REC" + "|", curses.A_BLINK)
        elif midi_manager.midi_recorder.is_recording:
            self.display.addstr(1, 20, "MIDI_REC" + "|", curses.A_STANDOUT)

        if audio_recorder.is_changing_active_state:
            self.display.addstr(1, 29, "AUDIO_REC" + "|", curses.A_BLINK)
        elif audio_recorder.is_recording:
            self.display.addstr(1, 29, "AUDIO_REC" + "|", curses.A_STANDOUT)

        self.display.refresh()


class Slot:
    def __init__(self, x, y, midi_manager, audio_recorder):
        self.id_num = 0
        self.name = ""
        self.midi_manager = midi_manager
        self.audio_recorder = audio_recorder
        self.x, self.y = x, y
        self.display = curses.newwin(3, 12, y, x)
        self.display.addstr(0, 0, str(self.name[:13]))
        self.is_active = False
        self.is_changing_active_state = False
        self.type = ""

    def event(self, input_ch):
        if 48 <= int(input_ch) <= 57:
            if self.id_num == int(chr(input_ch)):
                for track in self.midi_manager.tracks:
                    if self.id_num == track.id_num:
                        if not self.midi_manager.is_active:
                            if track.is_active:
                                track.is_active = False
                            elif not track.is_active:
                                track.is_active = True
                            track.is_changing_active_state = False
                        else:
                            if not track.is_changing_active_state:
                                track.is_changing_active_state = True
                            elif track.is_changing_active_state:
                                track.is_changing_active_state = False

                for track in self.audio_recorder.tracks:
                    if self.id_num == track.id_num:
                        if not self.audio_recorder.is_active:
                            if track.is_active:
                                track.is_active = False
                            elif not track.is_active:
                                track.is_active = True
                            track.is_changing_active_state = False
                        else:
                            if not track.is_changing_active_state:
                                track.is_changing_active_state = True
                            elif track.is_changing_active_state:
                                track.is_changing_active_state = False

    def draw(self):
        self.display.erase()
        self.display.border(1)
        self.display.addstr(1, 0, str(self.type))
        self.display.addstr(2, 9, str(self.id_num))
        if self.is_active:
            self.display.addstr(0, 0, str(self.name[:13]), curses.A_STANDOUT)
        else:
            self.display.addstr(0, 0, str(self.name[:13]))
        if self.is_changing_active_state:
            self.display.addstr(0, 0, "->", curses.A_BLINK)
        self.display.refresh()


class TrackGrid:
    def __init__(self, max_x, max_y, midi_manager, audio_recorder):
        self.midi_manager = midi_manager
        self.audio_recorder = audio_recorder

        self.slots = []
        self.max_x, self.max_y = max_x, max_y
        self.create_slots()

    def create_slots(self):
        self.slots = []
        x, y = 1, 4
        id_num = 1

        for track in self.midi_manager.tracks:
            slot = Slot(x, y, self.midi_manager, self.audio_recorder)
            slot.name = track.name
            slot.type = track.type
            slot.id_num = id_num
            track.id_num = slot.id_num
            self.slots.append(slot)
            if y + 4 >= self.max_y:
                y = 1
                x += 14
            y += 3
            id_num += 1

        for track in self.audio_recorder.tracks:
            slot = Slot(x, y, self.audio_recorder, self.audio_recorder)
            slot.name = track.name
            slot.type = track.type
            slot.id_num = id_num
            track.id_num = slot.id_num
            self.slots.append(slot)
            if y + 4 >= self.max_y:
                y = 1
                x += 14
            y += 3
            id_num += 1

    def refresh(self):
        for slot in self.slots:
            del slot
        self.create_slots()

    def event(self, input_ch):
        for slot in self.slots:
            slot.event(input_ch)

    def update(self, midi_manager, audio_recorder):
        if midi_manager.clock.just_ticked and midi_manager.clock.relative_tick == 1:
            self.refresh()

        for slot in self.slots:
            for track in midi_manager.tracks:
                if slot.id_num == track.id_num:
                    if track.is_active:
                        slot.is_active = True
                    else:
                        slot.is_active = False

                    if track.is_changing_active_state:
                        slot.is_changing_active_state = True
                    else:
                        slot.is_changing_active_state = False

            for track in audio_recorder.tracks:
                if slot.id_num == track.id_num:
                    if track.is_active:
                        slot.is_active = True
                    else:
                        slot.is_active = False

                    if track.is_changing_active_state:
                        slot.is_changing_active_state = True
                    else:
                        slot.is_changing_active_state = False


class Application:
    def __init__(self):
        self.screen = curses.initscr()
        self.screen.nodelay(1)
        self.max_y, self.max_x = self.screen.getmaxyx()

        curses.curs_set(0)
        curses.cbreak()
        curses.noecho()

        self.midi_manager = cls.MidiManager()
        self.audio_recorder = cls.AudioRecorder()

        self.info_window = InfoWindow(self.max_x, self.max_y)
        self.info_window.bpm = self.midi_manager.bpm

        self.track_grid = TrackGrid(self.max_x, self.max_y, self.midi_manager, self.audio_recorder)

        self.is_running_app = True

    def event(self):
        input_ch = self.screen.getch()
        if input_ch == ord("q"):
            self.on_exit()
            self.is_running_app = False

        if input_ch == ord("g"):
            self.midi_manager.save_midi_tracks_to_file()

        if input_ch == ord("p"):
            if not self.midi_manager.is_active:
                self.midi_manager.activate()
                for track in self.audio_recorder.tracks:
                    track.reset()
                    track.is_playing = True

            elif self.midi_manager.is_active:
                self.midi_manager.stop()
                for track in self.audio_recorder.tracks:
                    track.is_playing = False
                    track.stop_playing()

        if input_ch == ord("d"):
            if len(self.audio_recorder.tracks) > 0:
                self.audio_recorder.tracks[-1].is_active = False
                self.audio_recorder.tracks[-1].wave_file.stop()
                self.audio_recorder.tracks.pop()
                self.screen.clear()
                self.track_grid.refresh()

        if input_ch == ord("r"):
            if not self.midi_manager.midi_recorder.is_changing_active_state:
                self.midi_manager.midi_recorder.is_changing_active_state = True
            elif self.midi_manager.midi_recorder.is_changing_active_state:
                self.midi_manager.midi_recorder.is_changing_active_state = False

        if input_ch == ord("a"):
            if not self.audio_recorder.is_changing_active_state:
                self.audio_recorder.is_changing_active_state = True
            elif self.audio_recorder.is_changing_active_state:
                self.audio_recorder.is_changing_active_state = False

        self.track_grid.event(input_ch)

    def update(self):
        self.info_window.update(self.midi_manager.clock)
        self.midi_manager.update()
        self.audio_recorder.update(self.midi_manager.clock)
        self.track_grid.update(self.midi_manager, self.audio_recorder)

    def draw(self):
        self.info_window.draw(self.midi_manager, self.audio_recorder)
        for slot in self.track_grid.slots:
            slot.draw()

        self.screen.refresh()

    def on_exit(self):
        self.midi_manager.on_exit()
        curses.endwin()
