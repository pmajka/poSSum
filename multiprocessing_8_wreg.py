import multiprocessing
import logging
import sys
import os
import subprocess as sub

import networkx as nx
import json

def listToChain(listToSplit):
    if len(listToSplit) == 1:
        return [(listToSplit[0], listToSplit[0])]
    else:
        return zip(listToSplit[:-1], listToSplit[1:])

class copier():
    COMMAND_ANTS_LINEAR_REG = \
            """ANTS 2 \
                -m MI[%(fixed)04d.png,%(moving)04d.png,1,32] \
                -o f%(fixed)04d_m%(moving)04d_ \
                -i 0 \
                --number-of-affine-iterations 10x0x0x0x0"""
    
    def __init__(self):
        pass
    
    def __call__(self, (fi,mi)):
        command = self.COMMAND_ANTS_LINEAR_REG % {'fixed' : fi, 'moving': mi}
        p = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = p.communicate()
        print  output, errors

class metric():
    COMMAND_C2D_METRIC = """c2d %(fixed)04d.png %(moving)04d.png -background 255 -reslice-itk  %(fixed)04d_%(moving)04d_Affine.txt %(fixed)04d.png -ncor """
    def __init__(self):
        pass
    
    def __call__(self, (fi,mi)):
        command = self.COMMAND_C2D_METRIC% {'fixed' : fi, 'moving': mi}
        p = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = p.communicate()
        print  output, errors
        return fi, mi, float(output.strip().split('=')[1].strip())

class chainTransform():
    FN_TPL_PARTIAL_TRANSFORM = """%(fixed)04d_%(moving)04d_Affine.txt"""
    FN_TPL_COMPOSED_TRANSFORM= """ct_f%(fixed)04d_m%(moving)04d_Affine.txt"""
    COMMAND_COMPOSE_MULTI_TRANSFORM="""ComposeMultiTransform 2 %(outputTransformFilename)s %(inputTransformsFilenamesList)s"""
    
    def __init__(self):
        pass
    
    def prepareTransformationChain(self, chain):
        sys.stdout.flush()
        listOfTransforms = []
        
        for fi, mi in listToChain(chain):
            listOfTransforms.append(\
                    self.FN_TPL_PARTIAL_TRANSFORM % {'fixed' : fi, 'moving': mi})
        #print listOfTransforms
        sys.stdout.flush()
        return " ".join(listOfTransforms)
    
    def __call__(self, (fi, mi, chain)):
        
        outputFilename = self.FN_TPL_COMPOSED_TRANSFORM % {'fixed' : fi, 'moving': mi}
        #print (fi, mi, chain)
        cmdDict = {}
        cmdDict['outputTransformFilename'] = outputFilename
        cmdDict['inputTransformsFilenamesList'] = \
                self.prepareTransformationChain(chain)
         
        command = self.COMMAND_COMPOSE_MULTI_TRANSFORM % cmdDict
        p = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = p.communicate()
        #print command
        return fi, mi, output

class reslice():
    FN_TPL_COMPOSED_TRANSFORM= """ct_f%(fixed)04d_m%(moving)04d_Affine.txt"""
    FN_TPL_MOVING_IMAGE = """%(movingFileIndex)04d.png"""
    FN_TPL_OUTPUT_IMAGE = """%(movingFileIndex)04d.nii.gz"""
    COMMAND_COMPOSE_WARP_IMAGE= \
            """c2d %(inputFilename)s %(inputFilename)s \
               -reslice-itk %(transformFilename)s \
               -type uchar -o %(outputFilename)s"""
    
    def __init__(self):
        pass
    
    def __call__(self, (fi, mi)):
        transform = self.FN_TPL_COMPOSED_TRANSFORM % {'fixed' : fi, 'moving': mi}
        outputFilename = self.FN_TPL_OUTPUT_IMAGE  % {'movingFileIndex': mi}
        inputImage = self.FN_TPL_MOVING_IMAGE  % {'movingFileIndex': mi}
         
        cmdDict = {}
        cmdDict['transformFilename'] = transform
        cmdDict['outputFilename']    = outputFilename
        cmdDict['inputFilename']     = inputImage
         
        command = self.COMMAND_COMPOSE_WARP_IMAGE % cmdDict
        p = sub.Popen(command.split(), stdout=sub.PIPE, stderr=sub.PIPE)
        output, errors = p.communicate()
        #print command
        return fi, mi, output, errors
        

class manager():
    def __init__(self, pool):
        self.start = 100
        self.end   = 130
        self.ref   = 115
        self.k     = 2
        self.eps   = 1
        
        self.pool = multiprocessing.Pool(processes=4)
    
    def transform(self):
        ii = copier()
        span = self._generateSpan()
        self.pool.map(ii, span)
    
    def buildGraph(self):
        ii = metric()
        span = self._generateSpan()
        self.metrics = self.pool.map(ii, span)
        #self.metrics = map(ii, span)
    
    def buildNetwork(self):
        graphWeights = map(lambda x: self.getGraphWeight(x), self.metrics)
        json.dump(graphWeights, open('weights.json', 'wb'))
        #graphWeights = json.load(open('weights.json'))
        G = nx.DiGraph()
        G.add_weighted_edges_from(graphWeights)
        self.pathPairs = nx.all_pairs_dijkstra_path(G)
    
    def composeTransformations(self):
        chains = []
        ii = chainTransform()
        for target in sorted(self.pathPairs[self.ref].keys()):
            chains.append((self.ref, target, self.pathPairs[self.ref][target]))
        self.pool.map(ii, chains)
        #map(ii, chains)
    
    def applyTransforms(self):
        chains = []
        ii = reslice()
        for target in sorted(self.pathPairs[self.ref].keys()):
            chains.append((self.ref, target))
        self.pool.map(ii, chains)
    
    def getGraphWeight(self, (fi, mi, metric)):
        w = (1 + metric) * abs(fi-mi) * (1+self.eps)**(abs(fi-mi))
        return (fi, mi, w)
    
    def _generateSpan(self):
        span = []
        for i in range(self.start, self.end + 1):
            for j in range(i-self.k, i+self.k):
                if j>=self.start and j<=self.end: #and i!=j:
                    span.append((i,j))
        return span
    
    def execute(self):
        #ii.transform()
        ii.buildGraph()   
        ii.buildNetwork()
        ii.composeTransformations()
        ii.applyTransforms()

if __name__ == '__main__':
    #multiprocessing.log_to_stderr(logging.DEBUG)
    pool = multiprocessing.Pool(processes=4)
    ii = manager(pool)
    ii.execute()
#    multiprocessing.log_to_stderr(logging.DEBUG)
    pool.close()
    pool.join()
