import numpy as np
from skimage import morphology, filters, exposure, segmentation, restoration, color, util, measure
from classes import NetworkEdge
from bio_object import compute_contour, compute_cell_center
import matplotlib.pyplot as plt

def add_edge(obj1, obj2, nanowire=None):
    obj1.adj_list.append(obj2)
    obj1.edge_list.append(NetworkEdge(obj1, obj2, nanowire))

    obj2.adj_list.append(obj1)
    obj2.edge_list.append(NetworkEdge(obj2, obj1, nanowire))

def compute_all_cell_bbox_overlaps(bio_objects):
    """ Computes the overlaps of the bounding boxes containing cells. """
    for i in range(len(bio_objects) - 1):
        cell1 = bio_objects[i]
        if not cell1.is_cell():
            continue

        for j in range(i + 1, len(bio_objects)):
            cell2 = bio_objects[j]
            if not cell2.is_cell():
                continue

            if cell1.bbox_overlaps_with_other_bbox(cell2)[0]:
                cell1.overlapping_bboxes.append(cell2)
            if cell2.bbox_overlaps_with_other_bbox(cell1)[0]:
                cell2.overlapping_bboxes.append(cell1)

def compute_cell_contact(bio_objects, image):
    """ Computes all cell-to-cell contacts and adds to adj_list attribute of the cell objects"""

    # filter out non-cells and cells that don't have contours (no possible cell contact)

    compute_all_cell_bbox_overlaps(bio_objects)

    cells = []
    for obj in bio_objects:
        if obj.is_cell():
            compute_cell_center(obj, image)
            if obj.overlapping_bboxes != []:
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


def compute_nanowire_to_cell_bbox_overlaps(nanowires, bio_objects, canvas):
    """ Computes the overlaps between nanowires and cells. Stores the overlaps in the nanowire
        objects only. """
    for nanowire in nanowires:
        for cell in bio_objects:
            # only looking at nanowire to cell overlaps, skip nanowires
            if not cell.is_cell():
                continue

            # want overlaps where nanowire and cell partially overlap or cell completely overlaps nanowire
            partially_overlaps, nanowire_is_contained_in_cell = nanowire.bbox_overlaps_with_other_bbox(cell)
            if partially_overlaps or nanowire_is_contained_in_cell:
                nanowire.overlapping_bboxes.append(cell)

                # for testing purposes:
                # nanowire_center = ((nanowire.x1 + nanowire.x2 )// 2, (nanowire.y1 + nanowire.y2) // 2)
                # canvas.axes.plot([nanowire_center[0], cell.cell_center[0]], [nanowire_center[1], cell.cell_center[1]], color="violet", marker='o', gid='edge')
    # canvas.draw()


def compute_nanowire_edges(bio_objects, canvas, image, binary_image):

    nanowires = []
    for obj in bio_objects:
        if obj.is_nanowire():
            nanowires.append(obj)

    compute_nanowire_to_cell_bbox_overlaps(nanowires, bio_objects, canvas)
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
                    cell.compute_cell_contour(image)
                if np.logical_and(cell.contour, nanowire.contour, dtype=np.int8).any():
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













# end
