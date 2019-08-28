#
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
#

import numpy as np
import sonnet as snt
import tensorflow as tf

from kglib.kgcn_experimental.custom_nx import multidigraph_data_iterator


def graph_to_input_target(graph,
                          input_node_fields,
                          input_edge_fields,
                          target_node_fields,
                          target_edge_fields,
                          features_field):

    """Returns 2 graphs with input and target feature vectors for training.

    Args:
    graph: An `nx.MultiDiGraph` instance.

    Returns:
    The input `nx.MultiDiGraph` instance.
    The target `nx.MultiDiGraph` instance.

    Raises:
    ValueError: unknown node type
    """

    def create_feature(attr, fields):
        return np.hstack([np.array(attr[field], dtype=float) for field in fields])

    input_graph = graph.copy()
    target_graph = graph.copy()

    for node_index, node_data in graph.nodes(data=True):
        input_graph.nodes[node_index][features_field] = create_feature(node_data, input_node_fields)
        target_graph.nodes[node_index][features_field] = create_feature(node_data, target_node_fields)

    for receiver, sender, edge_data in graph.edges(data=True):
        input_graph.edges[receiver, sender, 0][features_field] = create_feature(edge_data, input_edge_fields)
        target_graph.edges[receiver, sender, 0][features_field] = create_feature(edge_data, target_edge_fields)

    input_graph.graph[features_field] = np.array([0.0]*5)
    target_graph.graph[features_field] = np.array([0.0]*5)

    return input_graph, target_graph


def encode_solutions(graph, solution_field="solution", encoded_solution_field="encoded_solution",
                     encodings=np.array([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])):
    """
    Determines the encoding to use for a solution category
    Args:
        graph: Graph to update
        solution_field: The property in the graph that holds the value of the solution
        encoded_solution_field: The property in the graph to use to hold the new solution value
        encodings: An array, a row from which will be picked as the new solution based on using the current solution
            as a row index

    Returns: Graph with updated `encoded_solution_field`

    """

    for data in multidigraph_data_iterator(graph):
        solution = data[solution_field]
        data[encoded_solution_field] = encodings[solution]

    return graph


def encode_type_categorically(graph_data_iterator, all_types, type_field, category_field):
    """
    Encodes the type found in graph data as an integer according to the index it is found in `all_types`
    Args:
        graph_data_iterator: An iterator of data in the graph (node data, edge data or combined node and edge data)
        all_types: The full list of types to be encoded in this order
        type_field: The data field containing the type
        category_field: The data field to use to store the encoding

    Returns:

    """
    for data in graph_data_iterator:
        data[category_field] = all_types.index(data[type_field])


def encode_types_one_hot(G, all_node_types, all_edge_types, attribute='one_hot_type', type_attribute='type'):
    """
    Creates a one-hot encoding for every element in the graph, based on the "type" attribute of each element.
    Adds this one-hot vector to each element as `attribute`
    :param G: The graph to encode
    :param all_node_types: The list of node types to encode from
    :param all_edge_types: The list of edge types to encode from
    :param attribute: The attribute to store the encodings on
    :param type_attribute: The pre-existing attribute that indicates the type of the element
    """

    # TODO Catch the case where all types haven't been given correctly
    for node_index, node_feature in G.nodes(data=True):
        one_hot = np.zeros(len(all_node_types), dtype=np.int)
        index_to_one_hot = all_node_types.index(node_feature[type_attribute])
        one_hot[index_to_one_hot] = 1
        G.nodes[node_index][attribute] = one_hot

    for sender, receiver, keys, edge_feature in G.edges(data=True, keys=True):
        one_hot = np.zeros(len(all_edge_types), dtype=np.int)
        index_to_one_hot = all_edge_types.index(edge_feature[type_attribute])
        one_hot[index_to_one_hot] = 1
        G.edges[sender, receiver, keys][attribute] = one_hot

    return G


def make_mlp_model(latent_size=16, num_layers=2):
    """Instantiates a new MLP, followed by LayerNorm.

    The parameters of each new MLP are not shared with others generated by
    this function.

    Returns:
      A Sonnet module which contains the MLP and LayerNorm.
    """
    return snt.Sequential([
        snt.nets.MLP([latent_size] * num_layers, activate_final=True),
        snt.LayerNorm()
    ])


class TypeEncoder(snt.AbstractModule):
    def __init__(self, num_types, type_indicator_index, op, name='type_encoder'):
        super(TypeEncoder, self).__init__(name=name)
        self._index_of_type = type_indicator_index
        self._num_types = num_types
        with self._enter_variable_scope():
            self._op = op

    def _build(self, features):
        index = tf.cast(features[:, self._index_of_type], dtype=tf.int64)
        one_hot = tf.one_hot(index, self._num_types, on_value=1.0, off_value=0.0, axis=-1, dtype=tf.float32)
        return self._op(one_hot)
