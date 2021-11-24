import cv2 as cv
import numpy as np
import mss
from win32con import MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
from win32api import SetCursorPos, mouse_event
from multiprocessing import Process, Pipe
from keyboard import is_pressed
from time import sleep


def click(x, y):
    # Move cursor to the provided x, y coordinates
    SetCursorPos((x, y))
    # Press mouse1
    mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0)
    mouse_event(MOUSEEVENTF_LEFTUP, 0, 0)


def grabImage(p_input):
    window = {"top": 0, "left": 0, "width": 720, "height": 1080}
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
        circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, dp=1.2, minDist=1, param2=130, minRadius=0, maxRadius=150)
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.uint16(np.around(circles))
            # loop over the (x, y) coordinates and radius of the circles
            for index, (x, y, r) in enumerate(circles[0, :]):
                # loop over the (x, y) coordinates and radius of the circles again
                for x2, y2, r2 in circles[0, :][index+1:]:
                    # Check if first cicle matches second cicle
                    if x-10 <= x2 <= x+10 and y-10 <= y2 <= y+10 and r-2 <= r2 <= r+2:
                        # Click on cicle
                        click(x, y)
                # draw the circle in the output image
                cv.circle(image, (x, y), r, (0, 255, 0), 4)
        # Send the image with circles to showImage
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
