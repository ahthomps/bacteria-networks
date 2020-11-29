from PyQt5.QtGui import QIcon
from enum import Enum
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.lines import Line2D
from edge_detection import CELL_CONTACT_EDGE, CELL_TO_CELL_EDGE, CELL_TO_SURFACE_EDGE
from post_processing import NORMAL, SPHEROPLAST, CURVED, FILAMENT

class _Mode(str, Enum):
    """ Adapted from matplotlib's backend_bases.py. Contains information on
        the possible modes of the toolbar. """
    NONE = ""
    PAN = "pan/zoom"
    ZOOM = "zoom rect"
    CELL = "add cell"
    CELLCONTACTEDGE = "add cell contact edge"
    CELLTOSURFACEEDGE = "add cell to surface edge"
    CELLTOCELLEDGE = "add cell to cell edge"
    EDITOR = "edit cell classification"
    ERASER = "erase node/edge"

    def __str__(self):
        return self.value

    @property
    def _navigate_mode(self):
        return self.name if self is not _Mode.NONE else None

class CustomToolbar(NavigationToolbar2QT):
    """ Extends matplotlib's navigation toolbar. Added functionality includes
        adding nodes to network, adding three types of edges (cell contact,
        cell-to-cell nanowire, cell-to-surface nanowire) to the network, erase
        network objects, edit cell classifications, and buttons to navigate in
        an image directory. """
    def __init__(self, MplWidget, parent):
        self.main_window = parent
        # post_processor intialized as None because the post processor object
        # does not get instantiated until network graph can be created
        self.post_processor = None
        self.MplWidget = MplWidget

        super().__init__(self.MplWidget.canvas, parent)

        # remove unused buttons from the original toolbar
        self.message_display = self.actions()[-1]
        for _ in range(5):
            self.removeAction(self.actions()[-1])
        self.addAction(self.message_display)

        self.building_edge_data = None
        self.cell_classifications = [NORMAL, CURVED, FILAMENT, SPHEROPLAST]

    def add_toolbar_items(self, items):
        """ Expects a collection of collections in (icon, name, function,
            tooltip, checkable) format. Adds the program's custom toolbar actions
            to the interface. """

        for icon, name, function, tooltip, checkable in items:
            action = self.addAction(icon, name, function)
            action.setToolTip(tooltip)
            action.setCheckable(checkable)

    def add_file_navigation_buttons(self):
        """ Adds back and forward buttons for navigating through images that
            were just processed in a batch. """

        NAV_ITEMS = ((QIcon("ui/icons/prev.png"), "prev", lambda: self.main_window.load_batch_image(self.main_window.batch_index - 1), "Previous Image", False),
                     (QIcon("ui/icons/next.png"), "next", lambda: self.main_window.load_batch_image(self.main_window.batch_index + 1), "Next Image", False))
        self.add_toolbar_items(NAV_ITEMS)

    def set_post_processor(self, post_processor):
        self.post_processor = post_processor

    def add_network_tools(self):
        """ Adds custom network editing tools to the toolbar. """

        self.removeAction(self.actions()[-1])
        self.addSeparator()

        # This should be a global constant but it needs to use methods from this object
        NETWORK_ITEMS = ((QIcon("ui/icons/standard_node.svg"), "add_cell", self.add_cell_button_press, "Add a cell", True),
                         (QIcon("ui/icons/cell_to_cell.svg"), "add_cell_to_cell_edge", lambda: self.add_edge_button_press(_Mode.CELLTOCELLEDGE), "Add cell to cell  edge", True),
                         (QIcon("ui/icons/cell_to_surface.svg"), "add_cell_to_surface_edge", lambda: self.add_edge_button_press(_Mode.CELLTOSURFACEEDGE), "Add cell to surface edge", True),
                         (QIcon("ui/icons/cell_contact.svg"), "add_cell_contact_edge", lambda: self.add_edge_button_press(_Mode.CELLCONTACTEDGE), "Add cell contact edge", True),
                         (QIcon("ui/icons/editor.svg"), "edit_cell_classification", self.editor_button_press, "Edit cell classification", True),
                         (QIcon("ui/icons/eraser.svg"), "erase", self.eraser_button_press, "Erase node or edge", True))
        self.add_toolbar_items(NETWORK_ITEMS)

        self.addAction(self.message_display)
        self.addSeparator()

    def mouse_move(self, event):
        return

    def _update_buttons_checked(self):
        # sync button checkstates to match active mode
        self.uncheck_buttons()
        super()._update_buttons_checked()
        for action in self.actions():
            if action.text() == 'add_cell':
                action.setChecked(self.mode == _Mode.CELL)
            if action.text() == "add_cell_to_cell_edge":
                action.setChecked(self.mode == _Mode.CELLTOCELLEDGE)
            if action.text() == "add_cell_to_surface_edge":
                action.setChecked(self.mode == _Mode.CELLTOSURFACEEDGE)
            if action.text() == "add_cell_contact_edge":
                action.setChecked(self.mode == _Mode.CELLCONTACTEDGE)
            if action.text() == "edit_cell_classification":
                action.setChecked(self.mode == _Mode.EDITOR)
            if action.text() == "erase":
                action.setChecked(self.mode == _Mode.ERASER)


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

    def uncheck_buttons(self):
        for action in self.actions():
            if action.isChecked():
                action.setChecked(False)

    def add_cell_button_press(self):
        if self.mode == _Mode.ERASER or self.mode == _Mode.EDITOR:
            self.canvas.mpl_disconnect(self._id_pick)
        if self.mode == _Mode.CELL:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = _Mode.CELL
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)

        self._update_buttons_checked()

    def release_cell(self, event):
        if event.xdata is None or event.ydata is None:
            return

        node_id = max([int(node) for node in self.post_processor.graph.nodes]) + 1
        self.post_processor.graph.add_node(node_id, x=int(event.xdata), y=int(event.ydata), node_type=NORMAL)
        self.MplWidget.draw_node(node_id, self.post_processor.graph.nodes[node_id])
        self.MplWidget.canvas.draw()
        self.post_processor.build_KDTree()
        self.main_window.update_cell_counters()

    def add_edge_button_press(self, mode):
        if self.mode == _Mode.ERASER or self.mode == _Mode.EDITOR:
            self.canvas.mpl_disconnect(self._id_pick)
        if self.mode == mode:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        else:
            self.mode = mode
            self.canvas.widgetlock(self)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.set_message(self.mode)

        self._update_buttons_checked()

    def press_edge(self, event):
        assert self.building_edge_data is None
        node_begin = self.post_processor.get_closest_node(event.xdata, event.ydata)
        if node_begin is None:
            return

        self.building_edge_data = {'edge_line': None}
        self.building_edge_data['node_begin'] = node_begin
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.drag_edge)

    def drag_edge(self, event):
        _, node_data = self.building_edge_data['node_begin']
        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
            self.building_edge_data['edge_line'] = None
        edge_type = CELL_CONTACT_EDGE if self.mode == _Mode.CELLCONTACTEDGE else \
                    CELL_TO_SURFACE_EDGE if self.mode == _Mode.CELLTOSURFACEEDGE else \
                    CELL_TO_CELL_EDGE
        if self.building_edge_data['edge_line'] is None:
            self.building_edge_data['edge_line'] = self.MplWidget.draw_line((node_data['x'], node_data['y']), (event.xdata, event.ydata), edge_type)

    def exit_from_edge_creation(self):
        self.building_edge_data = None
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)

    def release_edge(self, event):
        if self.building_edge_data is None:
            return

        if event.xdata is None or event.ydata is None:
            self.exit_from_edge_creation()
            return

        if self.building_edge_data['edge_line'] is not None:
            self.building_edge_data['edge_line'].remove()
            self.building_edge_data['edge_line'] = None
            self.canvas.draw()
        if self.mode == _Mode.CELLTOSURFACEEDGE:
            node1_id = 0
            node1_data = {'x': int(event.xdata), 'y': int(event.ydata)}
        else:
            node1 = self.post_processor.get_closest_node(event.xdata,event.ydata)
            if node1 is None:
                self.exit_from_edge_creation()
                return
            node1_id, node1_data = node1

        node2_id, node2_data = self.building_edge_data['node_begin']

        if node1_id == node2_id:
            self.exit_from_edge_creation()
            return

        key = self.post_processor.graph.new_edge_key(node1_id, node2_id)
        edge_type = CELL_CONTACT_EDGE if self.mode == _Mode.CELLCONTACTEDGE else \
                    CELL_TO_SURFACE_EDGE if self.mode == _Mode.CELLTOSURFACEEDGE else \
                    CELL_TO_CELL_EDGE
        if _Mode.CELLTOSURFACEEDGE == self.mode:
            self.post_processor.graph.add_edge(node1_id, node2_id, key=key, edge_type=edge_type, surface_point=node1_data)
        else:
            self.post_processor.graph.add_edge(node1_id, node2_id, key=key, edge_type=edge_type)
        self.MplWidget.draw_edge(node1_id, node2_id, node1_data, node2_data, key, self.post_processor.graph[node1_id][node2_id][key])
        self.MplWidget.canvas.draw()
        self.building_edge_data = None
        self.canvas.mpl_disconnect(self._id_drag)
        self._id_drag = self.canvas.mpl_connect('motion_notify_event', self.mouse_move)

    def editor_button_press(self):
        if self.mode == _Mode.ERASER:
            self.canvas.mpl_disconnect(self._id_pick)
        if self.mode == _Mode.EDITOR:
            self.mode = _Mode.NONE
            self.canvas.mpl_disconnect(self._id_pick)
        else:
            self.mode = _Mode.EDITOR
            self._id_pick = self.canvas.mpl_connect('pick_event', self.edit_cell_classification)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.canvas.widgetlock.release(self)
        self.set_message(self.mode)

        self._update_buttons_checked()

    def edit_cell_classification(self, event):
        object_data = self.MplWidget.return_artist_data(event.artist._gid)
        if object_data["network_type"] == "edge":
            return

        current_node_type = self.post_processor.graph.nodes[object_data["node_id"]]['node_type']
        next_node_type = self.cell_classifications[(self.cell_classifications.index(current_node_type) + 1) % len(self.cell_classifications)]
        self.post_processor.graph.nodes[object_data["node_id"]]['node_type'] = next_node_type
        self.MplWidget.update_node_color(event.artist, next_node_type)
        self.main_window.update_cell_counters()

    def eraser_button_press(self):
        if self.mode == _Mode.EDITOR:
            self.canvas.mpl_disconnect(self._id_pick)
        if self.mode == _Mode.ERASER:
            self.mode = _Mode.NONE
            self.canvas.mpl_disconnect(self._id_pick)
        else:
            self.mode = _Mode.ERASER
            self._id_pick = self.canvas.mpl_connect('pick_event', self.erase_network_object)
        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self.mode._navigate_mode)
        self.canvas.widgetlock.release(self)
        self.set_message(self.mode)

        self._update_buttons_checked()

    def erase_network_object(self, event):
        graph = self.post_processor.graph
        object_data = self.MplWidget.artist_data[event.artist._gid]
        if object_data["network_type"] == "node":
            self.post_processor.graph.remove_node(object_data["node_id"])
            self.main_window.update_cell_counters()
            self.post_processor.build_KDTree()
        elif object_data["network_type"] == "edge" and graph.has_edge(object_data["edge_head"], object_data["edge_tail"], key=object_data["edge_key"]):
            graph.remove_edge(object_data["edge_head"], object_data["edge_tail"], key=object_data["edge_key"])

        del self.MplWidget.artist_data[event.artist._gid]
        event.artist.remove()
        self.canvas.draw()
