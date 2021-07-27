# Dependencies

- curses (it should be included in Linux, maybe not in Windows)
- mido
- python-rtmidi
- pyaudio
- pygame

# What is it?

Have you ever seen some person playing a guitar with a looper pedal on the street? That's what this program is for, but with two fundamental differences:
1. Although it can be used with any source of audio, this is intended for using a synthesizer.
2. It has midi integrated, as well as audio, so it can be used as both an audio looper and a midi looper, all at once. Yoy can "bounce" your midi tracks as audio recording a new track as audio.

So, we could say this software is a WIP CLI midi and audio looper. You can record and play midi and audio, all in sync, so with a hardware synthesizer and a line input in your audio interface you are able to record many tracks which will loop. It is possible, as well, to mute/deactivate tracks and activate them again without stopping. They will activate or deactivate when a new bar starts, not immediately.

# What isn't working or needs improvement?

THIS HAS BEEN TESTED ON LINUX ONLY.

- Right now, my synthesizer is hardcoded.
- Curses in python crashes when shrinking too much the console window. I'm not sure how to fix it, and if it's possible at all.
- It needs a midi file in order to load, but I don't want that. It will load any midi file named metronome.midi that is in the same directory as the program.
- BPM is hardcoded.
- Controls have to improve. Vim-like commands, maybe?
- Documentation.
- Refactorization.

# How to use?

## Play/Stop

If you press "p" on your keyboard, it will start playing or stop playing.

## Audio recording

If you press "a" on your keyboard, it will arm a new track to record audio. If it's stopped, it will start recording as soon as you press "p" to play. If it's playing, it will start recording as soon as a new bar is started.

## Midi recording

If you press "r" on your keyboard, it will arm a new track to record midi. If it's stopped, it will start recording as soon as you press "p" to play. If it's playing, it will start recording as soon as a new bar is started.

## Delete last audio track

You can delete the last audio track pressing "d". It will not delete midi tracks, though.

## Deactivate midi track

If you press the same number as the index of the midi track, it will start/stop playing as soon as a new bar is started. For example, if you want to deactivate midi track number 3, you just press "3" on your keyboard.

## Save midi file

Your audio tracks will be overwritten by a new program, but you could save new versions of your midi tracks when pressing "g" at any moment. It will not have any feedback, but a directory will be created alongside the program with a new midi file whose name will be the current date and time. It will not overwrite previous versions.
The midi file will be a type 1 midi file. That means "multitrack" midi file, so you could open it with other programs, like Sequencer64, and it will work.

 
