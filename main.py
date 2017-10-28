#!/usr/bin/env python

import sys
import argparse
import os

from PyQt5.QtWidgets import QApplication

from qtgui.main import DeepVisMainWindow

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Neural network analysis.')
    parser.add_argument("--model", help='filename of model to use',
                        default='models/example_keras_mnist_model.h5')
    parser.add_argument("--data", help='filename of dataset to visualize')
    parser.add_argument("--datadir", help='directory containing input images')
    parser.add_argument("--dataset", help='name of a dataset',
                        choices=['mnist'],
                        default='mnist')
    parser.add_argument("--framework", help='the framework to use.',
                        choices=['keras-tensorflow', 'keras-theano', 'torch'],
                        default='keras-tensorflow')
    args = parser.parse_args()

    if args.framework.startswith('keras'):
        # the only way to configure the keras backend appears to be via env vars
        # we thus inject one for this process. Keras must be laoded after this
        # is done
        if args.framework == 'keras-tensorflow':
            os.environ['KERAS_BACKEND'] = 'tensorflow'
        if args.framework == 'keras-theano':
            os.environ['KERAS_BACKEND'] = 'theano'
        # network = KerasNetwork(args.model)
        if not args.model:
            args.model = 'models/example_keras_mnist_model.h5'
        from network.keras_tensorflow import Network as KerasTensorFlowNetwork
        network = KerasTensorFlowNetwork(model_file=args.model)
    elif args.framework == 'torch':
        from network.torch import Network as TorchNetwork
        # FIXME[hack]: provide these parameter on the command line ...
        net_file = "models/example_torch_mnist_net.py"
        net_class = "Net"
        parameter_file = "models/example_torch_mnist_model.pth"
        input_shape = (28, 28)
        network = TorchNetwork(net_file, parameter_file,
                               net_class=net_class,
                               input_shape=input_shape)

    app = QApplication(sys.argv)
    mainWindow = DeepVisMainWindow()
    mainWindow.setNetwork(network)
    if args.data:
        mainWindow.setInputDataFile(args.data)
    elif args.dataset:
        mainWindow.setInputDataSet(args.dataset)
    if args.datadir:
        mainWindow.setInputDataDirectory(args.datadir)

    mainWindow.show()

    rc = app.exec_()
    print("Good bye ({})".format(rc))
    sys.exit(rc)
