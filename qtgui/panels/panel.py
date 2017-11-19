import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QComboBox
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QSplitter

from qtgui.widgets import QActivationView
from qtgui.widgets import QInputSelector, QInputInfoBox, QImageView
from qtgui.widgets import QNetworkView, QNetworkInfoBox

class Panel(QWidget):
    '''Base class for different visualisation panels. In the future, the type of
    visualisation should be a component in the panel, not a separate panel
    class.

    Attributes
    ----------
    network :   network.network.Network
                Network to run occlusion on
    data    :   np.ndarray
                Input dataset
    layer   :   str
                Identifier of the currently selected layer
    '''

    def __init__(self, parent=None):
        '''Initialization of the ActivationsView.

        Parameters
        ----------
        parent  :   QWidget
                    The parent argument is sent to the QWidget constructor.
        '''
        super().__init__(parent)

        self.initUI()

        self._network = None

        # FIXME[question]: int (index) or str (label)?
        self._layer = None

        self._data = None

    def on_input_selected(self, callback):
        '''Connect a callback to the input selector.

        Parameters
        ----------
        callback    :   function
                        Function to call when input selector receives selected
                        event
        '''
        self._input_selector.selected.connect(callback)

    def initUI(self):
        '''Initialise all UI elements. These are

            * The ``QImageView`` showing the current input image
            * A ``QInputSelector`` to show input controls
            * A ``QNetworkView``, a widget to select a layer in a network
            * A ``QInputInfoBox`` to display information about the input

        '''
        ########################################################################
        #                              User input                              #
        ########################################################################
        self._input_view = QImageView(self)
        # FIXME[layout]
        # keep image view square (TODO: does this make sense for every input?)
        self._input_view.heightForWidth = lambda w: w
        self._input_view.hasHeightForWidth = lambda: True

        # QNetworkInfoBox: a widget to select the input to the network
        # (data array, image directory, webcam, ...)
        # the 'next' button: used to load the next image
        self._input_selector = QInputSelector()

        self._input_info = QInputInfoBox()
        # FIXME[layout]
        self._input_info.setMinimumWidth(300)

        input_layout = QVBoxLayout()
        # FIXME[layout]
        input_layout.setSpacing(0)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(self._input_view)
        input_layout.addWidget(self._input_info)
        input_layout.addWidget(self._input_selector)

        input_box = QGroupBox('Input')
        input_box.setLayout(input_layout)
        self._input_box = input_box

        ########################################################################
        #                            Network                                   #
        ########################################################################
        # networkview: a widget to select a layer in a network
        self._network_view = QNetworkView()
        self._network_view.selected.connect(self.setLayer)

        self._network_selector = QComboBox()
        self._networks = {}
        self._network_selector.addItems(self._networks.keys())
        self._network_selector.activated.connect(
            lambda index: self.setNetwork(
                self._networks[self._network_selector.currentText()]))

        # layerinfo: display input and layer info
        self._network_info = QNetworkInfoBox()
        # FIXME[layout]
        self._network_info.setMinimumWidth(300)

        network_layout = QVBoxLayout()
        network_layout.addWidget(self._network_selector)
        network_layout.addWidget(self._network_view)
        network_layout.addWidget(self._network_info)

        network_box = QGroupBox('Network')
        network_box.setLayout(network_layout)

        self._network_box = network_box

    def addNetwork(self, network):
        '''Add a model to visualise. This will add the network to the list of
        choices and make it the currently selcted one

        Parameters
        ----------
        network     :   network.network.Network
                        A network  (should be of the same class as currently
                        selected ones)
        '''
        name = 'Network ' + str(self._network_selector.count())
        self._networks[name] = network
        self._network_selector.addItem(name)
        self.setNetwork(network)

    def getNetworkName(self, network):
        '''Get the name of the currently selected network. Note: This runs in
        O(n).

        Parameters
        ----------
        network     :   network.network.Network
                        The network to visualise.
        '''
        name = None
        for n, net in self._networks.items():
            if net == network:
                name = n
        return name

    def setNetwork(self, network=None):
        '''Set the current network. This will deselect all layers.

        Parameters
        ----------
        network     :   network.network.Network
                        Network instance to display
        '''
        if self._network != network:
            # aovid recomputing everything if no change
            self._network = network
            # change the network selector to reflect the network
            name = self.getNetworkName(network)
            index = self._network_selector.findText(name)
            self._network_selector.setCurrentIndex(index)

            self._network_view.setNetwork(network)
            self._network_info.setNetwork(network)
            self.setLayer(None)

    def setLayer(self, layer=None):
        '''Set the current layer to choose units from.

        Parameters
        ----------
        layer       :   network.layers.layers.Layer
                        Layer instance to display

        '''
        if self._layer != layer:
            self._layer = layer
            self._network_info.setLayer(layer)

    def setInputDataArray(self, data: np.ndarray=None):
        '''Set the input data to be used.

        Parameters
        ----------
        data    :   np.ndarray
                    The input data (for valid shapes see DeepVisMainWindow)

        '''
        self._input_selector.setDataArray(data)

    def setInputDataFile(self, filename: str):
        '''Set the input data to be used via file name.

        Parameters
        ----------
        filename    :   str
                    The input data in serialised numpy (for valid shapes see
                    DeepVisMainWindow)

        '''
        self._input_selector.setDataFile(filename)

    def setInputDataDirectory(self, dirname: str):
        '''Set the input data to be used via dir name.

        Parameters
        ----------
        dirname    :   str
                    The input data directory containing serialised numpy (for
                    valid shapes see DeepVisMainWindow)

        '''
        self._input_selector.setDataDirectory(dirname)

    def setInputDataSet(self, name: str):
        '''Set the input data to be used via name

        Parameters
        ----------
        name    :   str
                    Name of the input data set (must be known to the
                    application)

        '''
        self._input_selector.setDataSet(name)

    def setInputData(self, raw: np.ndarray=None, fitted: np.ndarray=None,
                     description: str=None):
        '''Set the current input stimulus for the network.
        The input stimulus should be taken from the internal data collection.
        This method will display the input data in the ImageView, set the
        current input data to the fitted version and update the activation.

        Parameters
        ----------
        raw     :   np.ndarray
                    The raw input data, as provided by the data source.
        fitted  :   np.ndarray
                    The input data transformed to fit the network.
        description :   str
                        A textual description of the input data
        '''
        self._input_view.setImage(raw)
        self._input_info.showInfo(raw, description)

        self._data = fitted
