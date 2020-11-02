import numpy as np
from skimage import morphology, filters, exposure, segmentation, restoration, color, util, measure
from classes import NetworkEdge

def compute_cell_contact(bio_objects):
    """ Computes all cell-to-cell contacts and adds to adj_list attribute of the cell objects"""

    # filter out non-cells and cells that don't have contours (no possible cell contact)
    cells = []
    for obj in bio_objects:
        if obj.is_cell() and obj.has_contour():
            cells.append(obj)

    for i in range(len(cells) - 1):
        cell1 = cells[i]
        for j in range(i + 1, len(cells)):
            cell2 = cells[j]
            # if the intersections of the np arrays has 1s then they overlap
            if np.logical_and(cell1.contour, cell2.contour, dtype=np.int8).any():
                # cell1.adj_list.append(cell2)
                cell1.edge_list.append(NetworkEdge(cell1, cell2))
                cell1.edge_list[-1].set_type_as_cell_contact()

                # cell2.adj_list.append(cell1)
                cell2.edge_list.append(NetworkEdge(cell2, cell1))
                cell2.edge_list[-1].set_type_as_cell_contact()

            # if not dilate each contour and try again?
            else:
                dilated_contour1 = morphology.dilation(cell1.contour)
                if np.logical_and(dilated_contour1, cell2.contour, dtype=np.int8).any():
                    # cell1.adj_list.append(cell2)
                    cell1.edge_list.append(NetworkEdge(cell1, cell2))
                    cell1.edge_list[-1].set_type_as_cell_contact()

                    # cell2.adj_list.append(cell1)
                    cell2.edge_list.append(NetworkEdge(cell2, cell1))
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
                nanowire_center = ((nanowire.x1 + nanowire.x2 )// 2, (nanowire.y1 + nanowire.y2) // 2)
                canvas.axes.plot([nanowire_center[0], cell.cell_center[0]], [nanowire_center[1], cell.cell_center[1]], color="violet", marker='o', gid='edge')
    canvas.draw()


def compute_nanowire_edges(bio_objects, canvas):

    nanowires = []
    for obj in bio_objects:
        if obj.is_nanowire():
            nanowires.append(obj)

    compute_nanowire_to_cell_bbox_overlaps(nanowires, bio_objects, canvas)
    surface = bio_objects[0]

    for nanowire in nanowires:
        if len(nanowire.overlapping_bboxes) == 2:
            cell1, cell2 = nanowire.overlapping_bboxes
            cell1.adj_list.append(cell2)
            cell1.edge_list.append(NetworkEdge(cell1, cell2, nanowire))
            cell1.edge_list[-1].set_type_as_cell_to_cell()

            cell2.adj_list.append(cell1)
            cell2.edge_list.append(NetworkEdge(cell2, cell1, nanowire))
            cell2.edge_list[-1].set_type_as_cell_to_cell()

        elif len(nanowire.overlapping_bboxes) == 1:
            cell1 = nanowire.overlapping_bboxes[0]
            cell1.adj_list.append(surface)
            cell1.edge_list.append(NetworkEdge(cell1, surface, nanowire))
            cell1.edge_list[-1].set_type_as_cell_to_surface()

            surface.adj_list.append(cell1)
            surface.edge_list.append(NetworkEdge(surface, cell1, nanowire))
            surface.edge_list[-1].set_type_as_cell_to_surface()
