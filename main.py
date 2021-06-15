import gui
import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()


application = gui.Application()


def main():
    while application.is_running_app:
        application.event()
        application.update()
        application.draw()


if __name__ == "__main__":
    main()
