# -*- coding: utf-8 -*-
"""Experience4.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uRP3xuc4YXLWKIl5hvTQZ2XX4mcrsMhM
"""

#!pip install bindsnet
import torch
import random
import matplotlib.pyplot as plt
from bindsnet.network import Network
from bindsnet.network.nodes import Input, LIFNodes
from bindsnet.network.topology import Connection, SparseConnection, LocalConnection,MeanFieldConnection
from bindsnet.network.monitors import Monitor
from bindsnet.analysis.plotting import plot_spikes, plot_voltages
from bindsnet.learning import PostPre, MSTDP

# Parametres
tauxConnectionEntree = 0.25
tauxConnectionRes = 0.1

nMedia = 100
nPersons = 1000


muPoidsEntree = 0.7
sigmaPoidsEntree = 0.05
muPoidsRes= 0.1
sigmaPoidsRes= 0.05

# Simulation time. (ms)
time = 1000
# Duree de la simulation exterieur (ms)
timeExSim=1
# Create the network.
network = Network()
# Create and add input, output layers.
source_layer = Input(n=nMedia,traces=True)
target_layer = LIFNodes(n=nPersons,traces=True)
#Creation de la matrice des poids aleatoire
def OnTime(spike):
  return ((spike * 1.0).sum(dim=0)>0)*1.0
def poids(x,y,tauxConnection,muPoids,sigmaPoids):
  return torch.mul(
      (torch.rand(x, y)<tauxConnection)*1.0,
      torch.randn(x, y)*sigmaPoids + muPoids
  )
#Ajout des couches au model
network.add_layer(
    layer=source_layer, name="A"
)
network.add_layer(
    layer=target_layer, name="B"
)

# Creation des connexions entre l'entree et le reservoir
#connMedia2Persons = (torch.rand(nMedia, nPersons)<tauxConnectionEntree)*1.0
#randomW = torch.randn(nMedia, nPersons)*sigmaPoidsEntree + muPoidsEntree
#wMedia2Persons = torch.mul(randomW,connMedia2Persons)

forward_connection = Connection(
    # Choix des couches a lier
    source=source_layer,
    target=target_layer,
    # Attribution des poids avec un tensor contenant les valeurs des poids de chaque connections (n=1000*1000)
    #w=connMedia2Persons
    w=poids(nMedia,nPersons,tauxConnectionEntree,muPoidsEntree,sigmaPoidsEntree)
)
# Ajout de la connexion au model
network.add_connection(
    connection=forward_connection, source="A", target="B"
)

# Creation des connexions entre les neurones du reservoir
recurrent_connection = Connection(
    # Choix des couches a lier
    source=target_layer,
    target=target_layer,
    # Attribution des poids avec un tensor contenant les valeurs des poids de chaque connections (n=1000*1000)
    w=poids(nPersons,nPersons,tauxConnectionRes,muPoidsRes,sigmaPoidsRes),
    # Choix de la regle d'apprentissage
    #update_rule=PostPre, nu=(1e-4, 1e-2)
)
# Ajout de la connexion au model
network.add_connection(
    connection=recurrent_connection, source="B", target="B"
)

# Create and add input and output layer monitors.
source_monitor = Monitor(
    obj=source_layer,
    state_vars=("s",),  # Record spikes.
    time=time,  # Length of simulation (if known ahead of time).
)
target_monitor = Monitor(
    obj=target_layer,
    state_vars=("s", "v"),  # Record spikes and voltages.
    time=time,  # Length of simulation (if known ahead of time).
)

network.add_monitor(monitor=source_monitor, name="A")
network.add_monitor(monitor=target_monitor, name="B")

# Create input spike data, where each spike is distributed according to Bernoulli(0.1).
input_data = torch.bernoulli(0.5 * (torch.cat((torch.ones(timeExSim, source_layer.n),torch.tensor((time-timeExSim)*[nMedia*[0.0]])),0)))
inputs = {"A": input_data}

# Simulate network on input data.
network.run(inputs=inputs, time=time)
print(OnTime(target_monitor.get("s")))

# Retrieve and plot simulation spike, voltage data from monitors.
spikes = {
    "A": source_monitor.get("s"), "B": target_monitor.get("s")
}
#print(poids(nMedia,nPersons,tauxConnectionEntree,muPoidsEntree,sigmaPoidsEntree)[0])
#print(poids(nPersons,nPersons,tauxConnectionRes,muPoidsRes,sigmaPoidsRes)[0])
voltages = {"B": target_monitor.get("v")}
plt.ioff()
plot_spikes(spikes)
plot_voltages(voltages, plot_type="line")
plt.show()

from torch import nn

somme = torch.sum(spikes["B"], dim=2)

kernel = torch.FloatTensor([[[0.006, 0.061, 0.242, 0.383, 0.242, 0.061, 0.006]]])
temp = somme.view(1,1,-1).float()

somme_smooth = nn.functional.conv1d(temp, kernel)

#plt.plot(somme_smooth.tolist()[0][0]) # size = [nrow, 1]
plt.plot(somme)
ax = plt.gca()
ax.set_xlim([0, 20])
ax.set_ylim([0, 52])
plt.show()