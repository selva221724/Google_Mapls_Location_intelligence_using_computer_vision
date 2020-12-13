import os
import cv2
import math
import numpy as np
from copy import copy
from skimage.io import imread
from matplotlib import pyplot as plt
from shapely.geometry import Polygon, Point


def slice_class(img_input, color):
    """Slicing images based on given color space
    Parameters:
     input image: RGBImage
     color range: HSV color range
    Return:
     contours list """
    img1 = img_input.copy()
    R1, G1, B1, R2, G2, B2 = color[0][0], color[0][1], color[0][2], color[1][0], color[1][1], color[1][2]
    hsv_conv = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_conv, (R1, G1, B1), (R2, G2, B2))
    imask = mask > 0
    zeros = np.zeros_like(img1, np.uint8)
    zeros[imask] = img1[imask]
    gray_conv = cv2.cvtColor(zeros, cv2.COLOR_BGR2GRAY)
    ret, threshold = cv2.threshold(gray_conv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    temp_contours = []
    for cnt in contours:
        if cv2.contourArea(cnt) > 100:
            temp_contours.append(cnt.tolist())
    return temp_contours


img_path = './Images'
image_folder = [os.path.join(img_path, image) for image in os.listdir(img_path)]
image_folder = sorted(image_folder)

for image in image_folder:
    img = cv2.imread(image)
    color_classes = {'building': [(13, 3, 244), (255, 18, 255)],
                     'veg': [(0, 0, 0), (73, 255, 235)],
                     'road': [(0, 0, 0), (0, 255, 255)]
                     }
    w, h = img.shape[1], img.shape[0]
    midX, midY = int(w / 2), int(h / 2)
    mid_point = Point(midX, midY)

    entrance = None
    Target_class = None
    shop = None
    for i, j in color_classes.items():
        conts = slice_class(img, j)
        for cnt in conts:
            coords = [list(i[0]) for i in cnt]
            coords_poly = Polygon(coords)
            if coords_poly.contains(mid_point):
                if i == 'road':
                    entrance = [midX, midY]
                    Target_class = ['building']

                elif i == 'building':
                    poly_coords = list(coords_poly.exterior.coords)
                    poly_coords = [[int(k[0]), int(k[1])] for k in poly_coords]
                    dists = []
                    for pt in poly_coords:
                        x2, y2 = pt[0], pt[1]
                        x1, y1 = midX, midY
                        dist = math.hypot(x2 - x1, y2 - y1)
                        dists.append([dist, [x2, y2]])
                        entrance = min(dists, key=lambda x: x[0])[1]
                    Target_class = ['road', 'building']
                    shop = cnt

    if Target_class is None:
        entrance = [midX, midY]
        Target_class = ['road', 'building']

    distance_classes = {}

    for target in Target_class:
        Target_contours = slice_class(img, color_classes[target])
        try:
            Target_contours.remove(shop)
        except:
            pass
        temp = []
        for cnt in Target_contours:
            coords = [list(i[0]) for i in cnt]
            dists = []
            for pt in coords:
                x2, y2 = pt[0], pt[1]
                x1, y1 = entrance[0], entrance[1]
                dist = math.hypot(x2 - x1, y2 - y1)
                dists.append([dist, [x2, y2]])
                distance, end_coord = min(dists, key=lambda x: x[0])
            temp.append([distance, end_coord])

        distance_classes.update({target: min(temp, key=lambda x: x[0])})

    res = min(distance_classes.items(), key=lambda x: x[1][0])
    cv2.circle(img, (midX, midY), radius=5, color=(255, 0, 0), thickness=2)
    cv2.circle(img, (entrance[0], entrance[1]), radius=5, color=(255, 255, 0), thickness=4)
    cv2.circle(img, (res[1][1][0], res[1][1][1]), radius=5, color=(255, 0, 255), thickness=2)
    fig = plt.figure()
    plt.imshow(img)
    plt.savefig('./result_imgs/' + image.split('/')[-1])
    plt.close()
    print('{}   {:.3f}  {}'.format(image.split('/')[-1], res[1][0], res[0]))
