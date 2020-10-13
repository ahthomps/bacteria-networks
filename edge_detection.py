import numpy as np
from skimage import morphology, filters, exposure, segmentation, restoration, color, util, measure

def compute_cell_contact(cells):
    for i in range(len(cells) - 1):
        cell1 = cells[i]
        for j in range(i + 1, len(cells)):
            cell2 = cells[j]
            # if the intersections of the np arrays has 1s then they overlap
            if np.logical_and(cell1._contour, cell2._contour, dtype=np.int8).any():
                cell1._adj_list.append(cell2)
                cell2._adj_list.append(cell1)

            # if not dilate each contour and try again?
            else:
                dilated_contour1 = morphology.dilation(cell1._contour)
                if np.logical_and(dilated_contour1, cell2._contour, dtype=np.int8).any():
                    cell1._adj_list.append(cell2)
                    cell2._adj_list.append(cell1)
