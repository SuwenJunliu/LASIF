#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import glob
import os

from lasif import LASIFNotFoundError
from .component import Component


class IterationsComponent(Component):
    """
    Component dealing with the iteration xml files.

    :param iterations_folder: The folder with the iteration XML files.
    :param communicator: The communicator instance.
    :param component_name: The name of this component for the communicator.
    """
    def __init__(self, iterations_folder, communicator, component_name):
        self._folder = iterations_folder
        super(IterationsComponent, self).__init__(communicator,
                                                  component_name)

    def _get_filename_for_iteration(self, iteration_name):
        """
        Helper function returning the filename of an iteration.
        """
        return os.path.join(
            self._folder,
            self.get_long_iteration_name(iteration_name) + os.path.extsep +
            "xml")

    def get_iteration_dict(self):
        """
        Returns a dictionary with the keys being the iteration names and the
        values the iteration filenames.

        >>> import pprint
        >>> comm = getfixture('iterations_comm')
        >>> pprint.pprint(comm.iterations.get_iteration_dict()) \
        #  doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
        {'1': '/.../ITERATION_1.xml',
         '2': '/.../ITERATION_2.xml'}
        """
        files = [os.path.abspath(_i) for _i in glob.iglob(os.path.join(
            self._folder, "ITERATION_*%sxml" % os.extsep))]
        it_dict = {os.path.splitext(os.path.basename(_i))[0][10:]: _i
                   for _i in files}
        return it_dict

    def get_long_iteration_name(self, iteration_name):
        """
        Returns the long form of an iteration from its short name.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.get_long_iteration_name("1")
        'ITERATION_1'
        """
        return "ITERATION_%s" % iteration_name

    def list(self):
        """
        Get a list of all iterations managed by this component.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.list()
        ['1', '2']
        """
        return sorted(self.get_iteration_dict().keys())

    def count(self):
        """
        Get the number of iterations managed by this component.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.count()
        2
        """
        return len(self.get_iteration_dict())

    def has_iteration(self, iteration_name):
        """
        Test for existence of an iteration.

        :type iteration_name: str
        :param iteration_name: The name of the iteration.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.has_iteration("1")
        True
        >>> comm.iterations.has_iteration("99")
        False
        """
        return iteration_name in self.get_iteration_dict()

    def create_new_iteration(self, iteration_name, solver_name, events_dict,
                             min_period, max_period):
        """
        Creates a new iteration XML file.

        :param iteration_name: The name of the iteration.
        :param solver_name: The name of the solver to be used for the new
            iteration.
        :param events_dict: A dictionary specifying the used events.
        :param min_period: The minimum period in seconds for the new iteration.
        :param max_period: The maximum period in seconds for the new iteration.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.has_iteration("3")
        False
        >>> comm.iterations.create_new_iteration("3", "ses3d_4_1",
        ...     {"EVENT_1": ["AA.BB", "CC.DD"], "EVENT_2": ["EE.FF"]},
        ...     10.0, 20.0)
        >>> comm.iterations.has_iteration("3")
        True
        >>> os.remove(comm.iterations.get_iteration_dict()["3"])
        """
        if iteration_name in self.get_iteration_dict():
            msg = "Iteration %s already exists." % iteration_name
            raise ValueError(msg)

        from lasif.iteration_xml import create_iteration_xml_string
        xml_string = create_iteration_xml_string(iteration_name,
                                                 solver_name, events_dict,
                                                 min_period, max_period)
        with open(self._get_filename_for_iteration(iteration_name), "wt")\
                as fh:
            fh.write(xml_string)

    def create_successive_iteration(self, existing_iteration_name,
                                    new_iteration_name):
        """
        Create an iteration based on an existing one.

        It will take all settings in one iteration and transfers them to
        another iteration. Any comments will be deleted.

        :param existing_iteration_name: Name of the iteration to be used as
            a template.
        :param new_iteration_name: Name of the new iteration.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.has_iteration("3")
        False
        >>> comm.iterations.create_successive_iteration("1", "3")
        >>> comm.iterations.has_iteration("3")
        True

        # Comments of an iteration will be stripped.
        >>> comm.iterations.get("1").comments
        ['Some', 'random comments']
        >>> comm.iterations.get("3").comments
        []

        >>> os.remove(comm.iterations.get_iteration_dict()["3"])

        If the iteration template does not exist, a
        :class:`~lasif.LASIFNotFoundError` will be raised.

        >>> comm.iterations.create_successive_iteration("99", "100")
        Traceback (most recent call last):
            ...
        LASIFNotFoundError: ...

        A ``ValueError`` will be raised if the new iteration already exists.

        >>> comm.iterations.create_successive_iteration("1", "2")
        Traceback (most recent call last):
            ...
        ValueError: ...
        """
        it_dict = self.get_iteration_dict()
        if existing_iteration_name not in it_dict:
            msg = "Iteration %s does not exists." % existing_iteration_name
            raise LASIFNotFoundError(msg)
        if new_iteration_name in it_dict:
            msg = "Iteration %s already exists." % new_iteration_name
            raise ValueError(msg)

        from lasif.iteration_xml import Iteration

        existing_iteration = Iteration(it_dict[existing_iteration_name])

        # Clone the old iteration, delete any comments and change the name.
        existing_iteration.comments = []
        existing_iteration.iteration_name = new_iteration_name
        self.save_iteration(existing_iteration)

    def save_iteration(self, iteration):
        """
        Save an iteration object to disc.
        :param iteration:
        """
        filename = self._get_filename_for_iteration(iteration.iteration_name)
        iteration.write(filename)

    def get(self, iteration_name):
        """
        Returns an iteration object.

        :param iteration_name: The name of the iteration to retrieve.

        >>> comm = getfixture('iterations_comm')
        >>> comm.iterations.get("1")  # doctest: +ELLIPSIS
        <lasif.iteration_xml.Iteration object at ...>
        >>> print comm.iterations.get("1")  \
        # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
        LASIF Iteration
            Name: 1
            ...

        A :class:`~lasif.LASIFNotFoundError` will be raised, if the
        iteration is not known.

        >>> comm.iterations.get("99")
        Traceback (most recent call last):
            ...
        LASIFNotFoundError: ...
        """
        it_dict = self.get_iteration_dict()
        if iteration_name not in it_dict:
            msg = "Iteration '%s' not found." % iteration_name
            raise LASIFNotFoundError(msg)

        from lasif.iteration_xml import Iteration
        it = Iteration(it_dict[iteration_name])
        return it
