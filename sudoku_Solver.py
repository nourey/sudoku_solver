import time
import cv2
import pytesseract      
import numpy as np


def euclidian_distance(point1, point2):
    distance = np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
    return distance


def order_corner_points(corners):
    sort_corners = [(corner[0][0], corner[0][1]) for corner in corners]
    sort_corners = [list(ele) for ele in sort_corners]
    x, y = [], []

    for i in range(len(sort_corners[:])):
        x.append(sort_corners[i][0])
        y.append(sort_corners[i][1])

    centroid = [sum(x) / len(x), sum(y) / len(y)]

    for _, item in enumerate(sort_corners):
        if item[0] < centroid[0]:
            if item[1] < centroid[1]:
                top_left = item
            else:
                bottom_left = item
        elif item[0] > centroid[0]:
            if item[1] < centroid[1]:
                top_right = item
            else:
                bottom_right = item

    ordered_corners = [top_left, top_right, bottom_right, bottom_left]

    return np.array(ordered_corners, dtype="float32")

def image_preprocessing(image, corners):
    ordered_corners = order_corner_points(corners)
    top_left, top_right, bottom_right, bottom_left = ordered_corners


    width1 = euclidian_distance(bottom_right, bottom_left)
    width2 = euclidian_distance(top_right, top_left)

    height1 = euclidian_distance(top_right, bottom_right)
    height2 = euclidian_distance(top_left, bottom_right)

    width = max(int(width1), int(width2))
    height = max(int(height1), int(height2))

    dimensions = np.array([[0, 0], [width, 0], [width, width],
                           [0, width]], dtype="float32")

    matrix = cv2.getPerspectiveTransform(ordered_corners, dimensions)

    transformed_image = cv2.warpPerspective(image, matrix, (width, width))

    transformed_image = cv2.resize(transformed_image, (600, 600), interpolation=cv2.INTER_AREA)

    return transformed_image


def get_square_box_from_image(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 3)
    adaptive_threshold = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 3)
    corners = cv2.findContours(adaptive_threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    corners = corners[0] if len(corners) == 2 else corners[1]
    corners = sorted(corners, key=cv2.contourArea, reverse=True)
    for corner in corners:
        length = cv2.arcLength(corner, True)
        approx = cv2.approxPolyDP(corner, 0.015 * length, True)

        puzzle_image = image_preprocessing(image, approx)
        break
    return puzzle_image

def findNextCellToFill(sudoku):
    for x in range(9):
        for y in range(9):
            if sudoku[x][y] == 0:
                return x, y
    return -1, -1
    
def isValid(sudoku, i, j, e):
    rowOk = all([e != sudoku[i][x] for x in range(9)])
    if rowOk:
        columnOk = all([e != sudoku[x][j] for x in range(9)])
        if columnOk:
            secTopX, secTopY = 3*(i//3), 3*(j//3)
            for x in range(secTopX, secTopX+3):
                for y in range(secTopY, secTopY+3):
                    if sudoku[x][y] == e:
                        return False
            return True
    return False
    
def solveSudoku(sudoku, i=0, j=0):
    i, j = findNextCellToFill(sudoku)
    if i == -1:
        return True
    for e in range(1, 10):
        if isValid(sudoku, i, j, e):
            sudoku[i][j] = e
            if solveSudoku(sudoku, i, j):
                return True
            sudoku[i][j] = 0
    return False

def sudokuVisualisor(sudoku):
    print("------------------------")
    for i in range(len(sudoku)):
        line = "|"
        if i == 3 or i == 6:
            print("------------------------")
        for j in range(len(sudoku[i])):
            if j == 3 or j == 6:
                line += "| "
            if sudoku[i][j] == 0:
                line += "  "
            else:
                line += str(sudoku[i][j])+" "
        print(line+"|")
    print("------------------------")
def get_final_frame(image):
    src = get_square_box_from_image(cv2.imread(image))

    src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    src = cv2.adaptiveThreshold(src, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 85, 17)
    return src

def get_digits(image):
    custom_config = r'--psm 10 --oem 1 --tessdata-dir /home/tesseract-4.1.1/tessdata/ -c tessedit_char_whitelist=0123456789'

    number_list = ["1","2","3","4","5","6","7","8","9"]

    n = 0
    sudoku = []
    src = get_final_frame(image)
    for y in range(0,9):
        raw = []
        for x in range(0,9):

            crop_img = src[(y*65)+13:65*(y+1), (x*65)+13:65*(x+1)]
            value = pytesseract.image_to_string(crop_img,config=custom_config, lang="digits")
            if (value[0] in number_list):
                raw.append(int(value[0]))
            else:
                raw.append(0)
            n=n+1
        sudoku.append(raw)
    return sudoku

def finalize_sudoku(image):
    
    start = time.time()
    sudoku = get_digits(image)

    print("\n Here is the Sudoku to solve: \n")
    sudokuVisualisor(sudoku)
    print("____________________________________")
    print("\n      ### Solving Puzzle ###")
    print("____________________________________")
    solveSudoku(sudoku)
    print("\n Here is the solution: \n")
    sudokuVisualisor(sudoku)


    end = time.time()

    print("Elapsed Time: " + str(end-start))

image=input('Path of the image? ')


finalize_sudoku(image)

