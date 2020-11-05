import numpy as np
from skimage import morphology, filters, exposure, segmentation, restoration, color, util, measure
from bio_object import compute_contour, compute_cell_center
import matplotlib.pyplot as plt

class NetworkEdge:
    def __init__(self, tail, head, nanowire=None):
        self.tail = tail
        self.head = head
        self.type = ""
        self.nanowire = nanowire

    def set_type_as_cell_contact(self):
        self.type = "cell_contact"

    def set_type_as_cell_to_cell(self):
        self.type = "cell_to_cell"

    def set_type_as_cell_to_surface(self):
        self.type = "cell_to_surface"

    def type_is_cell_contact(self):
        return self.type == "cell_contact"

    def type_is_cell_to_cell(self):
        return self.type == "cell_to_cell"

    def type_is_cell_to_surface(self):
        return self.type == "cell_to_surface"

    def __str__(self):
        return f"{self.type}: {self.tail.id} {self.head.id}"

def add_edge(obj1, obj2, nanowire=None):
    obj1.adj_list.append(obj2)
    obj1.edge_list.append(NetworkEdge(obj1, obj2, nanowire))

    obj2.adj_list.append(obj1)
    obj2.edge_list.append(NetworkEdge(obj2, obj1, nanowire))


def compute_cell_contact(bio_objects, image):
    """ Computes all cell-to-cell contacts and adds to adj_list attribute of the cell objects"""

    # filter out non-cells and cells that don't have contours (no possible cell contact)

    cells = []
    for obj in bio_objects:
        if obj.is_cell() and obj.overlapping_bboxes != []:
            cells.append(obj)
            compute_contour(obj, image)

    for i in range(len(cells) - 1):
        cell1 = cells[i]
        for j in range(i + 1, len(cells)):
            cell2 = cells[j]
            cell1_contour_dilated = morphology.dilation(cell1.contour)
            # if the intersections of the np arrays has 1s then they overlap
            if (np.logical_and(cell1.contour, cell2.contour, dtype=np.int8).any() or
                    np.logical_and(cell1_contour_dilated, cell2.contour, dtype=np.int8).any()):
                add_edge(cell1, cell2)
                cell1.edge_list[-1].set_type_as_cell_contact()
                cell2.edge_list[-1].set_type_as_cell_contact()


def compute_nanowire_edges(bio_objects, canvas, image):

    nanowires = []
    for obj in bio_objects:
        if obj.is_nanowire():
            nanowires.append(obj)

    surface = bio_objects[0]

    for nanowire in nanowires:
        if len(nanowire.overlapping_bboxes) == 0:
            continue
        elif len(nanowire.overlapping_bboxes) == 2:
            cell1, cell2 = nanowire.overlapping_bboxes
            add_edge(cell1, cell2, nanowire)
            cell1.edge_list[-1].set_type_as_cell_to_cell()
            cell2.edge_list[-1].set_type_as_cell_to_cell()

        elif len(nanowire.overlapping_bboxes) == 1:
            cell1 = nanowire.overlapping_bboxes[0]
            add_edge(cell1, surface, nanowire)
            cell1.edge_list[-1].set_type_as_cell_to_surface()
            surface.edge_list[-1].set_type_as_cell_to_surface()
        else:
            # # find subimage containing the nanowire
            # subimage = np.asarray(image[nanowire.y1:nanowire.y2 + 1, nanowire.x1:nanowire.x2 + 1])
            # image_plot = plt.imshow(subimage, cmap='gray')
            # plt.show()
            # # use li thresholding to compute a binary image of the subimage (from original image)
            # threshold = filters.threshold_li(subimage)
            # subimage = subimage > threshold
            # image_binary_plot = plt.imshow(subimage, cmap='gray')
            # plt.show()
            # # find different regions in the subimage
            # labels_mask = measure.label(subimage, connectivity=2)
            # image_labels_plt = plt.imshow(labels_mask, cmap='gray')
            # plt.show()
            # # find properties of the different regions
            # regions = measure.regionprops(labels_mask)
            # # since this subimage corresponds to the bounding box of the nanowire,
            # # we can assume that the region with the largest bounding box is the nanowire
            # regions.sort(key=lambda x: x.bbox_area, reverse=True)
            # nanowire_image = regions[0].image
            # nanowire_image_plt = plt.imshow(nanowire_image, cmap='gray')
            # plt.show()
            # nanowire_contour = np.zeros(image.shape, dtype=np.uint8)
            # nanowire_contour[nanowire.y1:nanowire.y1 + len(nanowire_image), nanowire.x1:nanowire.x1 + len(nanowire_image[0])] = nanowire_image
            # nanowire_contour = morphology.dilation(nanowire_contour)
            compute_contour(nanowire, image)

            intersections = []
            for cell in nanowire.overlapping_bboxes:
                if cell.contour is None:
                    compute_contour(cell, image)
                if np.logical_and(cell.contour, nanowire.contour, dtype=np.uint8).any():
                    intersections.append(cell)

            print("intersections length: ", len(intersections))
            if len(intersections) == 2:
                cell1, cell2 = intersections
                add_edge(cell1, cell2, nanowire)
                cell1.edge_list[-1].set_type_as_cell_to_cell()
                cell2.edge_list[-1].set_type_as_cell_to_cell()
            elif len(intersections) == 1:
                cell1 = intersections[0]
                add_edge(cell1, surface, nanowire)
                cell1.edge_list[-1].set_type_as_cell_to_surface()
