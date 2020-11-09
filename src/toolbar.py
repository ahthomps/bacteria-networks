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
        self.MplWidget = MplWidget
        super().__init__(self.MplWidget.canvas, parent)
        self.message_display = self.actions()[-1]
        for _ in range(5):
            self.removeAction(self.actions()[-1])
        self.addAction(self.message_display)

        self.building_edge_data = None

        # self.canvas.mpl_connect('pick_event', self.object_clicked)

    def add_network_tools(self):
        self.removeAction(self.actions()[-1])
        self.addSeparator()
        self.addAction(QIcon("ui/standard_node.svg"), "Add Cell", self.cell).setToolTip("Add a cell")
        self.addAction(QIcon("ui/standard_edge.svg"), "Add Edge", self.edge).setToolTip("Add an edge")
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
        graph = self.main_window.program_manager.graph
        id = max(graph.nodes) + 1
        graph.add_node(id,x=event.xdata,y=event.ydata)
        self.main_window.program_manager.cell_data.append([id,event.xdata,event.ydata])
        self.main_window.program_manager.refreshKDtree()
        self.main_window.cellCounter.setText('Cell Count: ' + str(self.main_window.program_manager.get_cell_count()))
        self.canvas.axes.plot(event.xdata, event.ydata, color="red", marker="o", gid="cell_center")
        self.canvas.draw()

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
        self.building_edge_data = {}
        self.building_edge_data['node_begin'] = self.main_window.program_manager.get_closest_node(event.xdata,event.ydata)
        self.building_edge_data['edge_line'] = None
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.drag_edge)

    def drag_edge(self, event):
        node_begin = self.building_edge_data['node_begin']
        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
        self.building_edge_data['edge_line'] = self.MplWidget.draw_line((node_begin[1], node_begin[2]), (event.xdata, event.ydata))

    def release_edge(self, event):
        print("edge finished")
        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
        node_end = self.main_window.program_manager.get_closest_node(event.xdata,event.ydata)
        node_begin = self.building_edge_data['node_begin']
        if not node_begin[0] == node_end[0]:
            center1 = [node_begin[1], node_begin[2]]
            center2 = [node_end[1], node_end[2]]
            print('adding edge from', center1, 'to', center2)
            self.MplWidget.draw_line(center1, center2)
            # self.canvas.axes.plot([node_begin[1],node_end[1]], [node_begin[2],node_end[2]], color="green", linestyle="dashed", marker="o", gid="edge")
            # self.canvas.draw()
            self.main_window.program_manager.graph.add_edge(node_begin[0],node_end[0])
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.building_edge_data = None
