import cv2 as cv
import numpy as np
import mss
from win32con import MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
from win32api import SetCursorPos, mouse_event
from multiprocessing import Process, Pipe
from keyboard import is_pressed
from time import sleep


def ar_calculation(ar_input):
    try:
        ar_input = ar_input.split(".")
        ar_input.remove(".")
    except Exception:
        pass
    ar_input[0] = int(ar_input[0])
    ar_input[1] = int(ar_input[1])

    if ar_input[0] <= 4:
        try:
            return ((1800 - ar_input[1] * 120) - (120 / 10 * ar_input[1])) / 100
        finally:
            return 1800 / 100
    elif ar_input[0] >= 5:
        return ((1200 - ar_input[1] * 150) - (150 / 10 * ar_input[1])) / 100


def click(x, y):
    SetCursorPos((x, y))
    sleep(ar_calculation(ar))
    mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0)
    mouse_event(MOUSEEVENTF_LEFTUP, 0, 0)


def grabImage(p_input):
    window = {"top": 0, "left": 0, "width": 1920, "height": 1080}
    sct = mss.mss()
    while True:
        # Grab screen image
        image = np.asarray(sct.grab(window))
        # Resize image to 60% of original size. Lower % = worse detection
        image = cv.resize(image, None, fx=0.4, fy=0.4)
        # Put image from pipe
        p_input.send(image)


def detecting(p_output, p_input2):
    while True:
        image = p_output.recv()
        # Convert to grayscale
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, minDist=1, dp=1.2, param1=150, param2=110, minRadius=30,
                                  maxRadius=100)
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.uint16(np.around(circles))
            # loop over the (x, y) coordinates and radius of the circles
            for (x, y, r) in circles[0, :]:
                # draw the circle in the output image, then draw a rectangle
                # corresponding to the center of the circle
                cv.circle(image, (x, y), r, (0, 255, 0), 4)
                if is_pressed("v"):
                    click(round(x * 2.5), round(y * 2.5))
        p_input2.send(image)


def showImage(p_output2):
    while True:
        image_np = p_output2.recv()
        # Show image with detection
        cv.imshow("Detection window", image_np)
        # Press "q" to quit
        if cv.waitKey(25) & 0xFF == ord("q"):
            cv.destroyAllWindows()
            break


if __name__ == "__main__":
    # Pipes
    p_output, p_input = Pipe()
    p_output2, p_input2 = Pipe()

    # Creating processes
    p1 = Process(target=grabImage, args=(p_input,))
    p2 = Process(target=detecting, args=(p_output, p_input2,))
    p3 = Process(target=showImage, args=(p_output2,))

    # Starting processes
    p1.start()
    p2.start()
    p3.start()
    ar = input("Enter the AR for the map: ")
