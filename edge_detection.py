import numpy as np
from skimage import morphology, filters, exposure, segmentation, restoration, color, util, measure

def cell_overlaps_from_contour(contours):
    # create adjacency list for the networks
    adjacency_list =[[] for _ in range(len(contours))]

    # brute force overlap detection
    for i in range(len(contours)):
        contour1 = contours[i]
        for j in range(i + 1, len(contours)):
            contour2 = contours[j]

            # if the intersections of the np arrays has 1s then they overlap
            if np.logical_and(contour1, contour2, dtype=np.int8).any():
                print("overlap:", i, j)
                adjacency_list[i].append(j)
                adjacency_list[j].append(i)

            # if not dialate each contour and try again?
            else:
                dialated_contour1 = morphology.dilation(contour1)
                if np.logical_and(dialated_contour1, contour2, dtype=np.int8).any():
                    print("overlap:", i, j)
                    adjacency_list[i].append(j)
                    adjacency_list[j].append(i)
    return

def cell_overlaps(cells):
    for i in range(len(cells) - 1):
        contour1 = cells[i]._contour
        for j in range(i + 1, len(cells)):
            contour2 = cells[j]._contour
            # if the intersections of the np arrays has 1s then they overlap
            if np.logical_and(contour1, contour2, dtype=np.int8).any():
                print("overlap:", i, j)
                cells[i]._adj_list.append(j)
                cells[j]._adj_list.append(i)

            # if not dialate each contour and try again?
            else:
                dialated_contour1 = morphology.dilation(contour1)
                if np.logical_and(dialated_contour1, contour2, dtype=np.int8).any():
                    print("overlap:", i, j)
                    cells[i]._adj_list.append(j)
                    cells[j]._adj_list.append(i)
    return
