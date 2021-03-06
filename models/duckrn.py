import tflearn
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.conv import conv_2d
from tflearn.layers.normalization import local_response_normalization
from tflearn.layers.estimator import regression
from tflearn.optimizers import Momentum
from tflearn.initializations import truncated_normal
from tflearn.initializations import zeros
import math

stddev5 = math.sqrt(1.0 / (5 * 5 * 2))
stddev3 = math.sqrt(1.0 / (3 * 3 * 256))

def get_network():
    biases = zeros(shape=[9, 19, 1, 256])
    biases2 = zeros(shape=[19, 19, 1])
    network = input_data(shape=[None, 19, 19, 2], name='input')
    network = conv_2d(network, 256, 5, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev5), bias=False) + biases[0]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[1]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[2]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[3]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[4]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[5]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[6]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[7]
    network = local_response_normalization(network)
    network = conv_2d(network, 256, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases[8]
    network = local_response_normalization(network)
    network = conv_2d(network, 1, 3, activation='elu', regularizer="L2", weights_init=truncated_normal(stddev=stddev3), bias=False) + biases2
    network = fully_connected(network, 19*19, activation='softmax')
    momentum = Momentum(learning_rate=0.002)
    network = regression(network, optimizer=momentum, loss='categorical_crossentropy', name='target')
    return network
