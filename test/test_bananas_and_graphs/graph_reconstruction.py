#!/usr/bin/python

import csv
from sys import argv
import networkx as nx
import numpy as np
from numpy import ones, concatenate
from math import ceil, sqrt
import matplotlib.pyplot as plt

def weightFunction(mdx, fdx, similarity_measure, l):
    return (1.0 + similarity_measure) * abs(mdx - fdx) * (1.0 + l) ** (abs(mdx - fdx))

def weightFunctionWrapper(row_from_similarity_table, l):
    return weightFunction(row_from_similarity_table[0],
                          row_from_similarity_table[1],
                          row_from_similarity_table[2], l)

def createGraph(numberOfSlices, epsilon, similarityData = None):
    if not similarityData:
        similarityData = createSimilarityData(numberOfSlices, epsilon)
    graphWeights = createWeightsFromData(similarityData)
    G = nx.DiGraph()
    G.add_weighted_edges_from(graphWeights)
    return G



def getShortestPath(node1, node2, Graph, shortest_paths = None ):
    if not shortest_paths:
        shortest_paths = nx.all_pairs_dijkstra_path(G)

def convertDataFromStrings(row):
    return int(row[0]), int(row[1]), float(row[2])

def createGraphFromFile(file_name):
    weights = []
    f = open(file_name, 'rb')
    csvreader = csv.reader(f, delimiter=' ')
    for row in csvreader:
        weights.append(row)
        weights.append([row[1], row[0], row[2]])
    weights = map(convertDataFromStrings,weights)
    G = nx.DiGraph()
    G.add_weighted_edges_from(weights)
    return G

def createGraphsFromSimilarities(similarities_data, lambdas):
    """l lambda"""
    similarities = []
    f = open(similarities_data, 'rb')
    csvreader = csv.reader(f, delimiter=' ')
    for row in csvreader:
        similarities.append(row)
        similarities.append([row[1], row[0], row[2]])
    similarities = map(convertDataFromStrings, similarities)
    graphs = []
    for l in lambdas:
        weights = []
        for row in similarities:
            weights.append([row[0], row[1], weightFunctionWrapper(row,l)])
        G = nx.DiGraph()
        G.add_weighted_edges_from(weights)
        graphs.append(G)
    return graphs

def nodesOmitted(Graph, referenceNode):
    shortest_paths = nx.all_pairs_dijkstra_path(Graph)
    front_path = shortest_paths[referenceNode][0]
    back_path = shortest_paths[referenceNode][len(Graph.nodes()) - 1]
    path = concatenate([front_path, back_path])
    omitted = ones(len(Graph.nodes()))
    for node in path:
        omitted[node] = 0
    return omitted
    G = nx.DiGraph()
    G.add_weighted_edges_from(weights)
    return G

def plotOmittedFromGraph(graph, reference_slice, l = "not specified"):



    omitted = nodesOmitted(graph, reference_slice)
    omitted[reference_slice] = -1
    reshape_parameter = int(ceil(sqrt(len(omitted))))
    magic_number = reshape_parameter / 2.
    padding = ones(reshape_parameter ** 2 - len(omitted)) * .5
    to_plot = concatenate([omitted, padding]).reshape((reshape_parameter,
                                                reshape_parameter)) * -1

    ##setting variables for text annotations
    x = np.linspace(8./reshape_parameter,
                reshape_parameter - 8./reshape_parameter, reshape_parameter)

    y = np.linspace(10./reshape_parameter,
                reshape_parameter - 8./reshape_parameter, reshape_parameter)

    plt.figure()
    plt.title(str(l))
    ax = plt.gca()
    ax.invert_yaxis()
    plt.pcolor(to_plot,cmap='PiYG')
    for i in range(reshape_parameter):
        for j in range(reshape_parameter):
            plt.text(x[i], y[j], str(i+j*reshape_parameter), color="white",
                                    horizontalalignment='center')
    plt.colorbar()

##czary

def setLambdaForWrapper(el):
    def WrapperWithLambda(row):
        return weightFunctionWrapper(row, el)
    return WrapperWithLambda


if __name__ == "__main__":
    """usage python graph_reconstruction file_name reference_slice lambda1 lambda2 ... lambdaN"""
    file_name = argv[1]
    reference_slice = int(argv[2])
    lambdas = map(float, argv[3:])
    graphs = createGraphsFromSimilarities(file_name, lambdas)
    for i, graph in enumerate(graphs):
        plotOmittedFromGraph(graph, reference_slice, lambdas[i])
    plt.show()
