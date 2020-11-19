import numpy as np
from skimage import morphology
from bio_object import compute_contour, compute_cell_center

CELL_CONTACT_EDGE = "cell_contact"
CELL_TO_CELL_EDGE = "cell_to_cell"
CELL_TO_SURFACE_EDGE = "cell_to_surface"

class NetworkEdge:
    def __init__(self, tail, head, nanowire=None):
        self.tail = tail
        self.head = head
        self.type = ""
        self.nanowire = nanowire

    def set_type_as_cell_contact(self):
        self.type = CELL_CONTACT_EDGE

    def set_type_as_cell_to_cell(self):
        self.type = CELL_TO_CELL_EDGE

    def set_type_as_cell_to_surface(self):
        self.type = CELL_TO_SURFACE_EDGE

    def type_is_cell_contact(self):
        return self.type == CELL_CONTACT_EDGE

    def type_is_cell_to_cell(self):
        return self.type == CELL_TO_CELL_EDGE

    def type_is_cell_to_surface(self):
        return self.type == CELL_TO_SURFACE_EDGE

    def __str__(self):
        return f"{self.type}: {self.tail.id} {self.head.id}"

def add_edge(obj1, obj2, nanowire=None):
    obj1.adj_list.append(obj2)
    obj1.edge_list.append(NetworkEdge(obj1, obj2, nanowire))

    obj2.adj_list.append(obj1)
    obj2.edge_list.append(NetworkEdge(obj2, obj1, nanowire))


def compute_cell_contact(bio_objects, image, update_progress_bar):
    """ Computes all cell-to-cell contacts and adds to adj_list attribute of the cell objects"""

    # filter out non-cells and cells that don't have contours (no possible cell contact)

    cells = []
    for obj in bio_objects:
        if obj.is_cell() and obj.overlapping_bboxes != []:
            cells.append(obj)
            compute_contour(obj, image)

    for i, cell1 in enumerate(cells):
        if update_progress_bar is not None:
            update_progress_bar(int(i / len(bio_objects) * 100))
        for cell2 in cell1.overlapping_bboxes:
            if cell2.id > cell1.id:
                continue
            cell1_contour_dilated = morphology.dilation(cell1.contour)
            # if the intersections of the np arrays has 1s then they overlap
            if (np.logical_and(cell1.contour, cell2.contour, dtype=np.int8).any() or
                    np.logical_and(cell1_contour_dilated, cell2.contour, dtype=np.int8).any()):
                add_edge(cell1, cell2)
                cell1.edge_list[-1].set_type_as_cell_contact()
                cell2.edge_list[-1].set_type_as_cell_contact()

def add_edge_based_on_intersection_set(surface, nanowire, intersection_set):
    if len(intersection_set) == 1:
        cell1 = intersection_set[0]
        add_edge(cell1, surface, nanowire)
        cell1.edge_list[-1].set_type_as_cell_to_surface()
        surface.edge_list[-1].set_type_as_cell_to_surface()
    elif len(intersection_set) == 2:
        cell1, cell2 = intersection_set
        add_edge(cell1, cell2, nanowire)
        cell1.edge_list[-1].set_type_as_cell_to_cell()
        cell2.edge_list[-1].set_type_as_cell_to_cell()
    elif len(intersection_set) != 0:
        return False
    return True

def compute_nanowire_edges(bio_objects, image, update_progress_bar):
    surface = bio_objects[0]
    num_cells = sum(bio_obj.is_cell() for bio_obj in bio_objects)
    nanowires = filter(lambda b: b.is_nanowire(), bio_objects)

    for i, nanowire in enumerate(nanowires):
        if update_progress_bar is not None:
            update_progress_bar(int((num_cells + i) / len(bio_objects) * 100))

        found_edge = add_edge_based_on_intersection_set(surface, nanowire, nanowire.overlapping_bboxes)
        if not found_edge:
            compute_contour(nanowire, image)

            intersections = []
            for cell in nanowire.overlapping_bboxes:
                if cell.contour is None:
                    compute_contour(cell, image)
                if np.logical_and(cell.contour, nanowire.contour, dtype=np.uint8).any():
                    intersections.append(cell)

            add_edge_based_on_intersection_set(surface, nanowire, intersections)
