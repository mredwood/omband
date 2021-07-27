import gui
import time
import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()


application = gui.Application()


def main():
    while application.is_running_app:
        application.event()
        application.update()
        application.draw()
        # ATTENTION: a high sleeping time breaks this program, but it's necessary to have a sleep time if we don't want our CPU on fire.
        time.sleep(0.001)


if __name__ == "__main__":
    main()
