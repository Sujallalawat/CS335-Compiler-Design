#!/usr/bin/python3.8

import networkx as nx
from ChironAST.ChironAST import PhiCommand  # Import PhiCommand to handle φ-functions

class BasicBlock:
    def __init__(self, bbname):
        self.name = bbname
        self.instrlist = []
        if bbname == "START" or bbname == "END":
            self.irID = bbname
        else:
            self.irID = int(bbname) - 1

    def __str__(self):
        return self.name

    def append(self, instruction):
        self.instrlist.append(instruction)

    def extend(self, instructions):
        self.instrlist.extend(instructions)

    def label(self):
        if len(self.instrlist):
            return '\n'.join(str(instr[0])+'; L'+ str(instr[1]) for instr in self.instrlist)
        else:
            return self.name
    
    def insert_phi(self, variable, predecessors):
        """ Inserts a φ-function for a given variable at the correct position, dynamically updating instruction indices. """

        # Initialize the set to track inserted φ-functions if not already done
        if not hasattr(self, 'phi_inserted_vars'):
            self.phi_inserted_vars = set()

        # Check if a φ-function for this variable already exists
        if variable in self.phi_inserted_vars:
            return  # Avoid duplicate φ-functions

        # Create a new PhiCommand object
        phi_instr = PhiCommand(variable, predecessors)

        # Insert φ-function at the start of the block
        insert_index = 0
        first_instr_index = self.instrlist[0][1] if self.instrlist else 0
        phi_index = first_instr_index

        # Insert the φ-function at the beginning
        self.instrlist.insert(insert_index, (phi_instr, phi_index))

        # Mark the variable as having a φ-function
        self.phi_inserted_vars.add(variable)

        # Shift indices for following instructions
        for i in range(1, len(self.instrlist)):
            instr, index = self.instrlist[i]
            self.instrlist[i] = (instr, index + 1)




class ChironCFG:

    """
    An adapter for Networkx.DiGraph.
    """

    def __init__(self, gname='cfg'):
        self.name = gname
        self.nxgraph = nx.DiGraph(name=gname)
        self.entry = "0"
        self.exit = "END"

    def __iter__(self):
        return self.nxgraph.__iter__()

    def is_directed(self):
        return True

    def add_node(self, node):
        if not isinstance(node, BasicBlock):
            raise ValueError("wrong type for 'node' parameter")

        self.nxgraph.add_node(node)

    def has_node(self, node):
        return self.nxgraph.has_node(node)

    def add_edge(self, u, v, **attr):
        if self.has_node(u):
            if self.has_node(v):
                self.nxgraph.add_edge(u, v, **attr)
            else:
                # TODO: do appropriate error reporting
                raise NameError(v)
        else:
            raise NameError(u)

    def nodes(self):
        return self.nxgraph.nodes()

    def edges(self):
        return self.nxgraph.edges()

    def successors(self, node):
        return self.nxgraph.successors(node)

    def predecessors(self, node):
        return self.nxgraph.predecessors(node)

    def out_degree(self, node):
        return self.nxgraph.out_degree(node)

    def in_degree(self, node):
        return self.nxgraph.in_degree(node)

    def get_edge_label(self, u, v):
        edata = self.nxgraph.get_edge_data(u,v)
        return edata['label'] if len(edata) else 'T'

    # TODO: add more methods to expose other methods of the Networkx.DiGraph