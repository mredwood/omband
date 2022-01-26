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

import gui
import time
import pygame
import cls




def main():

    conf_init = cls.ConfInit()
    conf_init.run()

    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.mixer.init()

    application = gui.Application()
    while application.is_running_app:
        application.event()
        application.update()
        application.draw()
        # ATTENTION: a high sleeping time breaks this program, but it's necessary to have a sleep time if we don't want our CPU on fire.
        time.sleep(0.001)



if __name__ == "__main__":
    main()
