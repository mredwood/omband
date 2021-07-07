# Dependencies

- curses (it should be included in Linux, maybe not in Windows)
- mido
- python-rtmidi
- pyaudio
- pygame

# What is it?

This software is a WIP midi and audio looper for CLI. You can record and play midi, synced with audio, so with a hardware synthesizer and a line input in your audio interface you are able to record many tracks which will loop. It is possible, as well, to mute/deactivate tracks and activate them again without stopping. They will activate or deactivate when a new bar starts, not immediately.

# What isn't working or needs improvement?

- Right now, my synthesizer and audio interface are hardcoded.
- It will EAT your CPU, as it is really intensive. *Fixing this is the number one priority*.
- Curses in python crashes when shrinking too much the console window. I'm not sure how to fix it, and if it's possible at all.
- Controls have to improve. Vim-like commands, maybe?
- Documentation.

# How to use?

TODO
