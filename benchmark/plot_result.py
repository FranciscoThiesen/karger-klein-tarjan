from matplotlib import pyplot
import numpy as np

def plot_results():
    X = [1250000, 2500000, 5000000, 10000000, 20000000]
    for val in X:
        val = val + 10000
    
    Y_boruvka = [107026667, 335252500, 385897500, 1065545000, 2205997000]
    Y_kkt = [2349635000, 5402627000, 11672843000, 22823183000, 45423793000]
    Y_kruskal = [145902800, 305691000, 621930000, 1364027000, 2878812000]
    Y_prim = [170785750, 284413000, 541855000, 1117153000, 2813013000]

    pyplot.plot(X, Y_boruvka,'ro')
    pyplot.plot(X, Y_kkt, 'bo')
    pyplot.plot(X, Y_kruskal, 'go')
    pyplot.plot(X, Y_prim, 'yo')

    pyplot.show()

plot_results()
