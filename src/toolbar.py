from PyQt5.QtGui import QIcon
from enum import Enum
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.lines import Line2D
from edge_detection import CELL_CONTACT_EDGE, CELL_TO_CELL_EDGE, CELL_TO_SURFACE_EDGE

class _Mode(str, Enum):
    NONE = ""
    PAN = "pan/zoom"
    ZOOM = "zoom rect"
    CELL = "add cell"
    CELLCONTACTEDGE = "add cell contact edge"
    CELLTOSURFACEEDGE = "add cell to surface edge"
    CELLTOCELLEDGE = "add cell to cell edge"
    ERASER = "erase node/edge"

    def __str__(self):
        return self.value

    @property
    def _navigate_mode(self):
        return self.name if self is not _Mode.NONE else None

class CustomToolbar(NavigationToolbar2QT):
    def __init__(self, MplWidget, parent):
        self.main_window = parent
        self.post_processor = None
        self.MplWidget = MplWidget
        super().__init__(self.MplWidget.canvas, parent)
        self.message_display = self.actions()[-1]
        for _ in range(5):
            self.removeAction(self.actions()[-1])
        self.addAction(self.message_display)

        self.building_edge_data = None


    def set_post_processor(self, post_processor):
        self.post_processor = post_processor

    def add_network_tools(self):
        self.removeAction(self.actions()[-1])
        self.addSeparator()
        self.addAction(QIcon("ui/standard_node.svg"), "Add Cell", self.cell).setToolTip("Add a cell")
        self.addAction(QIcon("ui/standard_edge.svg"), "Add Cell to Cell Edge", lambda: self.edge(_Mode.CELLTOCELLEDGE)).setToolTip("Add cell to cell  edge")
        self.addAction(QIcon("ui/celltosurface_edge.svg"), "Add Cell to Surface Edge", lambda: self.edge(_Mode.CELLTOSURFACEEDGE)).setToolTip("Add cell to surface edge")
        self.addAction(QIcon("ui/standard_edge.svg"), "Add Cell Contact Edge", lambda: self.edge(_Mode.CELLCONTACTEDGE)).setToolTip("Add cell contact edge")
        self.addAction(QIcon("ui/eraser.svg"), "Erase Network Object", self.eraser).setToolTip("Erase node or edge")
        self.addAction(self.message_display)

    def mouse_move(self, event):
        pass

    def _zoom_pan_handler(self, event):
        super()._zoom_pan_handler(event)
        if self.mode == _Mode.CELL:
            if event.name == "button_release_event":
                self.release_cell(event)
        elif self.mode == _Mode.CELLCONTACTEDGE or self.mode == _Mode.CELLTOSURFACEEDGE or self.mode == _Mode.CELLTOCELLEDGE:
            if  event.name == "button_press_event":
                self.press_edge(event)
            elif event.name == "button_release_event":
                self.release_edge(event)

    def cell(self):
        if self.mode == _Mode.CELL:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.CELL
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)

    def release_cell(self, event):
        id = max(self.post_processor.graph.nodes) + 1
        self.post_processor.graph.add_node(id,x=event.xdata,y=event.ydata)
        self.MplWidget.draw_node(id, self.post_processor.graph.nodes[id])
        self.post_processor.build_KDTree()
        self.main_window.update_cell_counter()

    def cell_contact_edge(self):
        if self.mode == _Mode.CELLCONTACTEDGE:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.CELLCONTACTEDGE
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)

    def edge(self, mode):
        if self.mode == mode:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = mode
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)

    def press_edge(self, event):
        assert(self.building_edge_data is None)
        self.building_edge_data = {'node_begin': None, 'edge_line': None}
        self.building_edge_data['node_begin'] = self.post_processor.get_closest_node(event.xdata,event.ydata)
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.drag_edge)

    def drag_edge(self, event):
        _, node_data = self.building_edge_data['node_begin']
        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
            self.building_edge_data['edge_line'] = None
        type = CELL_CONTACT_EDGE if self.mode == _Mode.CELLCONTACTEDGE else \
               CELL_TO_SURFACE_EDGE if self.mode == _Mode.CELLTOSURFACEEDGE else \
               CELL_TO_CELL_EDGE
        self.building_edge_data['edge_line'] = self.MplWidget.draw_line((node_data['x'], node_data['y']), (event.xdata, event.ydata), type)

    def release_edge(self, event):
        print("edge finished")
        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
            self.building_edge_data['edge_line'] = None
        if _Mode.CELLTOSURFACEEDGE == self.mode:
            node1_id = 0
            node1_data = {'x': event.xdata, 'y': event.ydata}
        else:
            node1_id, node1_data = self.post_processor.get_closest_node(event.xdata,event.ydata)
        node2_id, node2_data = self.building_edge_data['node_begin']
        if node1_id == node2_id:
            return
        print('adding edge from', [node1_data['x'], node1_data['y']], 'to', [node2_data['x'], node2_data['y']])
        key = self.post_processor.graph.new_edge_key(node1_id, node2_id)
        type = CELL_CONTACT_EDGE if self.mode == _Mode.CELLCONTACTEDGE else \
               CELL_TO_SURFACE_EDGE if self.mode == _Mode.CELLTOSURFACEEDGE else \
               CELL_TO_CELL_EDGE
        if _Mode.CELLTOSURFACEEDGE == self.mode:
            self.post_processor.graph.add_edge(node1_id, node2_id, key=key, type=type, surface_point=node1_data)
        else:
            self.post_processor.graph.add_edge(node1_id, node2_id, key=key, type=type)
        self.MplWidget.draw_edge(node1_id, node2_id, node1_data, node2_data, key, self.post_processor.graph[node1_id][node2_id][key])
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.building_edge_data = None

    def eraser(self):
        if self.mode == _Mode.ERASER:
            self.mode = _Mode.NONE
        else:
            self.mode = _Mode.ERASER
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.canvas.widgetlock.release(self)
        self.set_message(self.mode)
        self.canvas.mpl_connect('pick_event', self.erase_network_object)

    def erase_network_object(self, event):
        print(self.MplWidget.artist_data[event.artist._gid])
        print("you clicked an object!", event)
        graph = self.post_processor.graph
        object_data = self.MplWidget.artist_data[event.artist._gid]
        if object_data["network_type"] == "node":
            graph.remove_node(object_data["node_id"])
            self.main_window.update_cell_counter()
        elif object_data["network_type"] == "edge" and graph.has_edge(object_data["edge_head"], object_data["edge_tail"], key=object_data["edge_key"]):
            graph.remove_edge(object_data["edge_head"], object_data["edge_tail"], key=object_data["edge_key"])

        del self.MplWidget.artist_data[event.artist._gid]
        event.artist.remove()
        self.canvas.draw()
