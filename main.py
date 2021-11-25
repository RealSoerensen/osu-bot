import cv2 as cv
import numpy as np
import mss
from win32con import MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
from win32api import SetCursorPos, mouse_event
from multiprocessing import Process, Pipe


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
        grey = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        circles = cv.HoughCircles(grey, cv.HOUGH_GRADIENT, dp=1, minDist=0.1, param1=1, param2=100, minRadius=5,
                                  maxRadius=70)
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.uint16(np.around(circles))
            # loop over the (x, y) coordinates and radius of the circles
            for index, (x, y, r) in enumerate(circles[0, :]):
                # draw the circle in the output image
                cv.circle(image, (x, y), r, (0, 255, 0), 4)
                # loop over the (x, y) coordinates and radius of the circles again
                for x2, y2, r2 in circles[0, :][index + 1:]:
                    # Check if first circle matches second circle
                    if x - 10 <= x2 <= x + 10 and y - 10 <= y2 <= y + 10 and r - 2 <= r2 <= r + 2:
                        while x - 5 <= x2 <= x + 5 and y - 5 <= y2 <= y + 5:
                            # Move cursor to the provided x, y coordinates
                            SetCursorPos((x, y))
                            # Press mouse1
                            mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0)
                        # Release mouse1
                        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0)
        # Send the image with circles to showImage
        p_input2.send(image)


def showImage(p_output2):
    while True:
        image = p_output2.recv()
        # Show image with detection
        cv.imshow("Detection window", image)
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
