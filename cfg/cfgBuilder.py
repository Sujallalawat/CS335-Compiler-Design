#!/usr/bin/python3

import sys
import networkx as nx
from networkx.drawing.nx_agraph import to_agraph
from cfg.ChironCFG import *
import ChironAST.ChironAST as ChironAST

def buildCFG(ir, cfgName="", isSingle=False):
    startBB = BasicBlock('START')
    endBB = BasicBlock('END')
    leaderIndices = {0, len(ir)}
    leader2IndicesMap = {startBB: 0, endBB: len(ir)}
    indices2LeadersMap = {0: startBB, len(ir): endBB}

    # Finding leaders in the IR
    for idx, item in enumerate(ir):
        if isinstance(item[0], ChironAST.ConditionCommand) or isSingle:
            if idx + 1 < len(ir) and (idx + 1 not in leaderIndices):
                leaderIndices.add(idx + 1)
                thenBranchLeader = BasicBlock(str(idx + 1))
                leader2IndicesMap[thenBranchLeader] = idx + 1
                indices2LeadersMap[idx + 1] = thenBranchLeader

            if idx + item[1] < len(ir) and (idx + item[1] not in leaderIndices):
                leaderIndices.add(idx + item[1])
                elseBranchLeader = BasicBlock(str(idx + item[1]))
                leader2IndicesMap[elseBranchLeader] = idx + item[1]
                indices2LeadersMap[idx + item[1]] = elseBranchLeader

    # Constructing the CFG
    cfg = ChironCFG(cfgName)
    for leader in leader2IndicesMap.keys():
        cfg.add_node(leader)

    # Partitioning IR into basic blocks
    for currLeader in leader2IndicesMap.keys():
        leaderIdx = leader2IndicesMap[currLeader]
        currIdx = leaderIdx
        while currIdx < len(ir):
            currLeader.append((ir[currIdx][0], currIdx))
            currIdx += 1
            if currIdx in leaderIndices:
                break

    # Adding edges between basic blocks
    for node in cfg:
        listSize = len(node.instrlist)
        if listSize:
            irIdx = (node.instrlist[-1])[1]
            lastInstr = (node.instrlist[-1])[0]
            if isinstance(lastInstr, ChironAST.ConditionCommand):
                if not isinstance(lastInstr.cond, ChironAST.BoolFalse):
                    thenIdx = irIdx + 1 if (irIdx + 1 < len(ir)) else len(ir)
                    thenBB = indices2LeadersMap[thenIdx]
                    cfg.add_edge(node, thenBB, label='Cond_True', color='green')

                if not isinstance(lastInstr.cond, ChironAST.BoolTrue):
                    elseIdx = irIdx + ir[irIdx][1] if (irIdx + ir[irIdx][1] < len(ir)) else len(ir)
                    elseBB = indices2LeadersMap[elseIdx]
                    cfg.add_edge(node, elseBB, label='Cond_False', color='red')
            else:
                nextBB = indices2LeadersMap[irIdx + 1] if (irIdx + 1 < len(ir)) else endBB
                cfg.add_edge(node, nextBB, label='flow_edge', color='blue')

    # Convert CFG to SSA form
    cfg = convert_to_ssa(cfg)
    # from irhandler import update_ir_with_phi  # Import the function
    # update_ir_with_phi(irHandler) 

    return cfg

def compute_dominators(cfg):
    entry = next(node for node in cfg if node.name == "START")
    dominators = {node: set(cfg.nodes()) for node in cfg}
    dominators[entry] = {entry}
    changed = True

    while changed:
        changed = False
        for node in cfg:
            if node == entry:
                continue
            new_doms = set(cfg.nodes())
            for pred in cfg.predecessors(node):
                new_doms &= dominators[pred]
            new_doms.add(node)
            if new_doms != dominators[node]:
                dominators[node] = new_doms
                changed = True
    return dominators


def compute_dominance_frontiers(cfg, dominators):
    df = {node: set() for node in cfg}

    for node in cfg:
        preds = list(cfg.predecessors(node))
        if len(preds) >= 2:
            for pred in preds:
                runner = pred
                while runner not in dominators[node]:
                    df[runner].add(node)
                    runner = find_immediate_dominator(runner, dominators)
                    if runner is None:
                        break
    return df


def find_immediate_dominator(node, dominators):
    doms = dominators[node] - {node}
    for candidate in doms:
        if all(candidate in dominators[other] for other in doms if other != candidate):
            return candidate
    return None


def insert_phi_functions(cfg, df, variables):
    phi_inserted = {var: set() for var in variables}
    defsites = {var: set() for var in variables}

    for node in cfg:
        for instr in node.instrlist:
            if isinstance(instr[0], ChironAST.AssignmentCommand):
                var = instr[0].lvar
                if var in variables:
                    defsites[var].add(node)

    for var in variables:
        work = list(defsites[var])
        while work:
            block = work.pop()
            for df_node in df[block]:
                if df_node not in phi_inserted[var]:
                    df_node.insert_phi(var, [var] * len(list(cfg.predecessors(df_node))))
                    phi_inserted[var].add(df_node)
                    if df_node not in defsites[var]:
                        work.append(df_node)


def convert_to_ssa(cfg):
    dominators = compute_dominators(cfg)
    df = compute_dominance_frontiers(cfg, dominators)
    variables = {instr[0].lvar for node in cfg for instr in node.instrlist if isinstance(instr[0], ChironAST.AssignmentCommand)}
    insert_phi_functions(cfg, df, variables)
    return cfg



# import collections

# def rename_variables(cfg, variables):
#     """Renames variables in SSA form correctly using a stack-based SSA renaming algorithm."""
    
#     version_count = collections.defaultdict(int)
#     var_stack = {var: [var] for var in variables}  # Initialize stack for each variable
    
#     def new_name(var):
#         """Generate a new SSA versioned name for a variable."""
#         version_count[var] += 1
#         new_var = f"{var}_{version_count[var]}"
#         var_stack[var].append(new_var)
#         return new_var
    
#     def get_latest(var):
#         """Get the latest SSA version of a variable from the stack."""
#         if var not in var_stack:
#             var_stack[var] = [var]  # Ensure every variable has an entry
#         return var_stack[var][-1]

#     def rename_block(block):
#         """Renames variables within a block using DFS traversal."""
#         renamed_instrs = []

#         # Step 1: Rename φ-functions
#         for i, (instr, idx) in enumerate(block.instrlist):
#             if isinstance(instr, str) and "φ" in instr:
#                 var_name, phi_args = instr.split("=")[0].strip(), instr.split("(")[1].split(")")[0].split(", ")
                
#                 # Ensure φ-function variables exist in var_stack
#                 if var_name not in var_stack:
#                     var_stack[var_name] = [var_name]
                
#                 # Rename φ-function arguments using the latest available version
#                 new_phi_args = [get_latest(arg) for arg in phi_args]
#                 block.instrlist[i] = (f"{var_name} = φ({', '.join(new_phi_args)})", idx)

#         # Step 2: Rename assignments
#         for instr, idx in block.instrlist:
#             if isinstance(instr, ChironAST.AssignmentCommand):
#                 # Rename right-hand side variables
#                 rhs = instr.rexpr
#                 if isinstance(rhs, ChironAST.Var):
#                     rhs = ChironAST.Var(get_latest(rhs.varname))  # Rename RHS
                
#                 # Rename left-hand side variable
#                 var = instr.lvar
#                 new_var_name = new_name(var)
#                 renamed_instrs.append((ChironAST.AssignmentCommand(ChironAST.Var(new_var_name), rhs), idx))
#             else:
#                 renamed_instrs.append((instr, idx))  # Keep other instructions unchanged

#         block.instrlist = renamed_instrs

#         # Step 3: Rename φ-function arguments in successor blocks
#         for succ in cfg.successors(block):
#             for i, (instr, idx) in enumerate(succ.instrlist):
#                 if isinstance(instr, str) and "φ" in instr:
#                     var_name, phi_args = instr.split("=")[0].strip(), instr.split("(")[1].split(")")[0].split(", ")
                    
#                     # Ensure all variables are in var_stack before accessing
#                     for var in phi_args:
#                         if var not in var_stack:
#                             var_stack[var] = [var]  # Initialize if missing
                    
#                     new_phi_args = [get_latest(var) for var in phi_args]
#                     succ.instrlist[i] = (f"{var_name} = φ({', '.join(new_phi_args)})", idx)

#         # Step 4: Recursively rename variables in dominated blocks
#         for child in cfg.successors(block):
#             rename_block(child)

#         # Step 5: Restore variable names (pop from stack)
#         for instr, idx in block.instrlist:
#             if isinstance(instr, ChironAST.AssignmentCommand):
#                 var = instr.lvar.varname
#                 if var in var_stack and var_stack[var]:  # Ensure safe pop
#                     var_stack[var].pop()

#     # Find the actual entry block
#     entry_block = next(node for node in cfg if node.name == "START")
#     rename_block(entry_block)





def dumpCFG(cfg, filename="out"):
    G = cfg.nxgraph
    
    # Generating custom labels for graph nodes
    labels = {node: node.label() for node in cfg}

    G = nx.relabel_nodes(G, labels)
    A = to_agraph(G)
    A.layout('dot')
    A.draw(filename + ".png")