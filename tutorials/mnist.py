import ipdb
import numpy as np

from cle.cle.cost import NllMulInd
from cle.cle.data import Iterator
from cle.cle.models import Model
from cle.cle.layers import InitCell
from cle.cle.layers.feedforward import FullyConnectedLayer
from cle.cle.train import Training
from cle.cle.train.ext import (
    EpochCount,
    GradientClipping,
    Monitoring,
    Picklize,
    EarlyStopping
)
from cle.cle.train.opt import RMSProp
from cle.cle.utils import error, flatten, predict, OrderedDict
from cle.datasets.mnist import MNIST

# Set your dataset
data_path = '/home/junyoung/data/mnist/mnist.pkl'
save_path = '/home/junyoung/src/cle/saved/'

batch_size = 128
debug = 0

model = Model()
train_data = MNIST(name='train',
                   path=data_path)

valid_data = MNIST(name='valid',
                   path=data_path)

# Choose the random initialization method
init_W = InitCell('randn')
init_b = InitCell('zeros')

# Define nodes: objects
x, y = train_data.theano_vars()
# You must use THEANO_FLAGS="compute_test_value=raise" python -m ipdb
if debug:
    x.tag.test_value = np.zeros((batch_size, 784), dtype=np.float32)
    y.tag.test_value = np.zeros((batch_size, 1), dtype=np.float32)

h1 = FullyConnectedLayer(name='h1',
                         parent=['x'],
                         parent_dim=[784],
                         nout=1000,
                         unit='relu',
                         init_W=init_W,
                         init_b=init_b)

output = FullyConnectedLayer(name='output',
                             parent=['h1'],
                             parent_dim=[1000],
                             nout=10,
                             unit='softmax',
                             init_W=init_W,
                             init_b=init_b)

# You will fill in a list of nodes
nodes = [h1, output]

# Initalize the nodes
for node in nodes:
    node.initialize()

params = flatten([node.get_params().values() for node in nodes])

# Build the Theano computational graph
h1_out = h1.fprop([x])
y_hat = output.fprop([h1_out])

# Compute the cost
cost = NllMulInd(y, y_hat).mean()
err = error(predict(y_hat), y)
cost.name = 'cross_entropy'
err.name = 'error_rate'

model.inputs = [x, y]
model._params = params
model.nodes = nodes

# Define your optimizer: Momentum (Nesterov), RMSProp, Adam
optimizer = RMSProp(
    lr=0.001
)

extension = [
    GradientClipping(),
    EpochCount(40),
    Monitoring(freq=100,
               ddout=[cost, err],
               data=[Iterator(train_data, batch_size),
                     Iterator(valid_data, batch_size)]),
    Picklize(freq=200,
             path=save_path)
]

mainloop = Training(
    name='toy_mnist',
    data=Iterator(train_data, batch_size),
    model=model,
    optimizer=optimizer,
    cost=cost,
    outputs=[cost, err],
    extension=extension
)
mainloop.run()
