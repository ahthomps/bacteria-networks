from PyQt5.QtGui import QIcon
from enum import Enum
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.lines import Line2D

class _Mode(str, Enum):
    NONE = ""
    PAN = "pan/zoom"
    ZOOM = "zoom rect"
    CELL = "add cell"
    EDGE = "add edge"

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

        # self.canvas.mpl_connect('pick_event', self.object_clicked)

    def set_post_processor(self, post_processor):
        self.post_processor = post_processor

    def add_network_tools(self):
        self.removeAction(self.actions()[-1])
        self.addSeparator()
        self.addAction(QIcon("ui/standard_node.svg"), "Add Cell", self.cell).setToolTip("Add a cell")
        self.addAction(QIcon("ui/standard_edge.svg"), "Add Cell Contact Edge", self.edge).setToolTip("Add cell to cell contact edge")
        self.addAction(self.message_display)

    def mouse_move(self, event):
        pass

    def object_clicked(self, event):
        print("you clicked an object!")

    def _zoom_pan_handler(self, event):
        super()._zoom_pan_handler(event)
        if self.mode == _Mode.CELL:
            if event.name == "button_release_event":
                self.release_cell(event)
        elif self.mode == _Mode.EDGE:
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

    def edge(self):
        if self.mode == _Mode.EDGE:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.EDGE
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
        self.building_edge_data['edge_line'] = self.MplWidget.draw_line((node_data['x'], node_data['y']), (event.xdata, event.ydata))

    def release_edge(self, event):
        print("edge finished")
        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
        node1_id, node1_data = self.post_processor.get_closest_node(event.xdata,event.ydata)
        node2_id, node2_data = self.building_edge_data['node_begin']
        if node1_id == node2_id:
            return
        print('adding edge from', [node1_data['x'], node1_data['y']], 'to', [node2_data['x'], node2_data['y']])
        key = self.post_processor.graph.new_edge_key(node1_id, node2_id)
        self.post_processor.graph.add_edge(node1_id, node2_id, key=key, type="cell_to_cell")
        self.MplWidget.draw_edge(node1_id, node2_id, node1_data, node2_data, key, self.post_processor.graph[node1_id][node2_id][key])
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.building_edge_data = None
