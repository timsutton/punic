from __future__ import division, absolute_import, print_function

__all__ = ['Resolver']

from collections import defaultdict
from networkx import (DiGraph, dfs_preorder_nodes, topological_sort, number_of_nodes, number_of_edges)
from .logger import *


def dump(stream, graph, node, depth=0):
    count = len(graph.predecessors(node))

    stream.write("{}{} {}\n".format('\t' * depth, node, count))
    for child in sorted(graph[node].keys()):
        dump(stream, graph, child, depth + 1)


class Resolver(object):
    def __init__(self, punic, fetch=True):
        self.punic = punic
        self.root = (self.punic.root_project.identifier, None)
        self.fetch = fetch

    def build_graph(self, dependency_filter=None):
        # type: ([str]) -> DiGraph

        # TODO: Probably don't need to pass dependency_filter to populate_graph
        def populate_graph(graph, parent, parent_version, depth=0):
            graph.add_node((parent, parent_version))
            for child, child_versions in self.punic.dependencies_for_project_and_tag(parent,
                    parent_version.revision if parent_version else None,
                    fetch=self.fetch):
                for child_version in child_versions:
                    if dependency_filter and dependency_filter(child, child_version) == False:
                        continue
                    graph.add_edge((parent, parent_version), (child, child_version))
                    populate_graph(graph, child, child_version, depth=depth + 1)

        graph = DiGraph()
        populate_graph(graph=graph, parent=self.punic.root_project.identifier, parent_version=None)
        return graph

    def resolve(self):
        # type: () -> DiGraph
        for dependency, revisions in self.punic.dependencies_for_project_and_tag(self.punic.root_project.identifier,
                None, fetch=self.fetch):
            logger.debug('<ref>{}</ref> <rev>{}</rev>'.format(dependency, revisions))

        logger.debug('Building universal graph')

        # Build a graph up of _all_ version of _all_ dependencies
        graph = self.build_graph()

        logger.debug('Universal graph has {} nodes, {} edges.'.format(number_of_nodes(graph), number_of_edges(graph)))

        # Build a dictionary of all versions of all dependencies
        all_dependencies = defaultdict(set)
        for dependency, version in dfs_preorder_nodes(graph):
            all_dependencies[dependency].add(version)

        ################################################################################################################

        def prune_1():
            for dependency, versions in all_dependencies.items():
                if len(versions) <= 1:
                    continue
                for version in sorted(versions):
                    if len(graph.predecessors((dependency, version))) <= 1:
                        graph.remove_node((dependency, version))
                        all_dependencies[dependency].remove(version)
                    if len(versions) <= 1:
                        break

        def prune_2():
            def prune(node):
                mini = defaultdict(set)
                for dependency, version in graph.successors(node):
                    mini[dependency].add(version)
                for dependency, versions in mini.items():
                    some = all_dependencies[dependency]
                    difference = some.difference(versions)
                    for version in difference:
                        graph.remove_node((dependency, version))
                        all_dependencies[dependency].remove(version)
                for successor in graph.successors(node):
                    prune(successor)

            prune(self.root)

        ################################################################################################################

        logger.debug('<sub>Pruning graph</sub>')

        prune_1()
        prune_2()

        logger.debug(
            'Pruned universal graph has {} nodes, {} edges.'.format(number_of_nodes(graph), number_of_edges(graph)))

        ################################################################################################################

        dependencies = set(
            [(dependency, sorted(versions)[-1]) for dependency, versions in sorted(all_dependencies.items())])

        ################################################################################################################

        graph = self.build_graph(dependency_filter=lambda child, child_version: (child, child_version) in dependencies)

        logger.debug(
            'Pruned universal graph has {} nodes, {} edges.'.format(number_of_nodes(graph), number_of_edges(graph)))

        ################################################################################################################

        return graph

    def resolve_build_order(self):
        # type: () -> [(ProjectIdentifier, Revision)]
        graph = self.resolve()
        logger.debug('<sub>Topologically sorting graph</sub>')
        build_order = topological_sort(graph, reverse=True)
        return build_order

    def resolve_versions(self, dependencies, fetch=False):
        # type: (ProjectIdentifier, Revision) -> [ProjectIdentifier, Tag]
        """Given an array of project identifier/version pairs work out the build order"""
        graph = DiGraph()
        versions_for_identifier = dict(dependencies)
        for identifier, version in dependencies:
            parent = (identifier, version)
            graph.add_node(parent)
            for dependency, _ in self.punic.dependencies_for_project_and_tag(identifier=identifier,
                    tag=version.revision, fetch=fetch):
                version = versions_for_identifier[dependency]
                child = (dependency, version)
                graph.add_edge(parent, child)
        build_order = topological_sort(graph, reverse=True)
        return build_order
