# Node Matching Algorithm
from heapq import heappush, heappop
from collections import defaultdict

def heapsort(iterable):
  h = []
  for value in iterable:
    newValue = -value[0]
    value = (newValue, value[1])
    heappush(h, value)

  return h

# Performs node matching algorithm
# Computational Nodes will look like  (power, id)
# Data Nodes will look like (power, id)
def node_matching(computational_nodes, data_nodes):
  # Sort computational nodes and data nodes by powers 
  sortedComputationalNodes = heapsort(computational_nodes)
  priorityDataNodes = heapsort(data_nodes)

  dataNodeMapping = defaultdict(list)
  while sortedComputationalNodes:
    power, nodeId = heappop(sortedComputationalNodes)
    power = -int(power)

    try:
      largestDataNode = heappop(priorityDataNodes)
      dataNodePower = -int(largestDataNode[0])
      dataNodeId = largestDataNode[1]
    except IndexError as error:
      return dataNodeMapping

    dataNodeMapping[dataNodeId].append(nodeId)
    if(dataNodePower > power):
      newDataNode = (power - dataNodePower, dataNodeId)
      heappush(priorityDataNodes, newDataNode)
    else:
      newComputationalNode = (dataNodePower - power, nodeId)
      heappush(sortedComputationalNodes, newComputationalNode)

  return dataNodeMapping

if __name__ == "__main__":
  sampleComputationalNodes = [(5, "a"), (3, "b"), (2, "c"), (7, "d"), (3, "e")]
  sampleDataNodes = [(10, "1"), (4, "2"), (5, "3"), (1, "4")]

  nodeMatchingDict = node_matching(sampleComputationalNodes, sampleDataNodes)
  for key, value in nodeMatchingDict.items():
    print("Data Node: {} with Computational Nodes: {}".format(key, value))

