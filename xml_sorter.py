#!/usr/bin/env python

import contextlib
import re
import sys
import xml.dom.minidom

from collections import namedtuple
from optparse import OptionParser


Options = namedtuple('Options', 'keep_order,use_group,ignore_comment')


class Pattern(object):
  def __init__(self, patterns, case):
    self.case = case
    self.patterns = self._split(patterns)

  @staticmethod
  def _split(patterns):
    rets = dict()

    for pattern in patterns or list():
      if ':' not in pattern:
        pattern = ':%s' % pattern

      elem, attrs = pattern.split(':')
      rets[elem] = attrs.split(',')

    return rets

  def cmp_key(self, name):
    class _Cmp(object):
      @staticmethod
      def _order(obj):
        if name in self.patterns and obj in self.patterns[name]:
          return self.patterns[name].index(obj)

        return 10000 # sys.maxint is removed for python3

      def __init__(this, obj, *args):
        this.obj = obj
        this.order = this._order(obj)

      def __lt__(this, other):
        order = this._order(other.obj)
        if order == this.order:
          if self.case:
            return str(this.obj).lower() < str(other.obj).lower()
          else:
            return str(this.obj) < str(other.obj)
        else:
          return this.order < order

      def __gt__(this, other):
        order = this._order(other.obj)
        if order == this.order:
          if self.case:
            return str(this.obj).lower() > str(other.obj).lower()
          else:
            return str(this.obj) > str(other.obj)
        else:
          return this.order > order

      def __eq__(this, other):
        return this.obj == other.obj

      def __le__(this, other):
        return this.__eq__(other) or this.__lt__(other)

      def __ge__(this, other):
        return this.__eq__(other) or this.__gt__(other)

      def __ne__(this, other):
        return not this.__eq__(other)

    return _Cmp

  def sort(self, values, name=''):
    return sorted(values, key=self.cmp_key(name))


def child_dump(child, indent):
  xml = child.dump(indent=indent)
  if xml:
    return xml + '\n'
  else:
    return ''


class Group(object):
  def __init__(self, name, pattern):
    self.name = name
    self.pattern = pattern
    self.elements = list()

  def __repr__(self):
    return self.name

  def child(self, elem):
    self.elements.append(elem)

  def dump(self, indent=''):
    vals = '%s<!--%s-->\n' % (indent, self.name)
    for elem in self.pattern.sort(self.elements):
      vals += child_dump(elem, indent)

    return vals


class Element(object):
  def __init__(self, name, pattern, keep_order):
    self.name = name
    self.pattern = pattern
    self.keep_order = keep_order

    self.data = ''
    self.attrs = dict()
    self.order = list()
    self.groups = list()
    self.children = dict()
    self.no_order = list()

  def __str__(self):
    return self.dump()

  def normal(self):
    return not self.name.startswith('#')

  def attr(self, attr, value):
    self.attrs[attr] = value

  def child(self, child):
    self.no_order.append(child)
    if self.keep_order:
      if child.name not in self.order:
        self.order.append(child.name)
        self.children[child.name] = list()

      self.children[child.name].append(child)

  def group(self, name):
    for group in self.groups:
      if group.name == name:
        return group
    else:
      self.groups.append(Group(name, self.pattern))

      return self.groups[-1]

  def dump(self, indent=''):
    vals = ''
    if self.normal():
      vals = '%s<%s' % (indent, self.name)

      attrs = self.pattern.sort(self.attrs, self.name)
      for attr in attrs:
        vals += ' %s="%s"' % (attr, self.attrs[attr])
    elif self.name == '#comment':
      vals = '%s<!--' % indent

    if self.data:
      if len(vals) and vals[-1] == '\n':
        vals += '%s%s\n' % (indent, self.data)
      else:
        vals += self.data

    if len(self.no_order) == 0:
      if self.normal():
        vals += '/>'
      elif self.name == '#comment':
        vals += '-->'
    else:
      if self.normal():
        vals += '>\n'

      nindent = indent + ('  ' if self.normal() else '')
      if self.keep_order:
        for order in self.order:
          for child in self.pattern.sort(self.children[order]):
            vals += child_dump(child, nindent)

        for group in self.groups:
          vals += '\n'
          vals += group.dump(nindent)
      else:
        for child in self.pattern.sort(self.no_order):
          vals += child_dump(child, nindent)

        for group in self.pattern.sort(self.groups, 'group'):
          vals += '\n'
          vals += group.dump(nindent)

      if self.normal():
        if len(vals) and vals[-1] == '\n':
          vals += '%s</%s>' % (indent, self.name)
        else:
          vals += '</%s>' % self.name
      elif self.name == '#comment':
        vals += '-->'

    return vals


def _handle_node(node, options, pattern):
  elem = elem2 = Element(node.nodeName, pattern, options.keep_order)
  if hasattr(node, 'data'):
    elem.data = node.data.strip('\r\n')

  # hack into minidom.py
  if hasattr(node, '_attrs'):
    for attr in node._attrs or list():
      elem.attr(attr, node.getAttribute(attr))

  for child in node.childNodes:
    el = _handle_node(child, options, pattern)

    if el.normal():
      elem.child(el)
    elif el.name == '#text':
      if el.data.strip():
        elem.child(el)
    elif el.name == '#comment':
      if options.use_group and re.search(r'@\w+\(.+\)', el.data):
        elem = elem2.group(el.data)
      elif not options.ignore_comment:
        elem.child(el)

  return elem2


def _parse_xml(filename, pattern, options):
  root = xml.dom.minidom.parse(filename)

  return _handle_node(root, options, pattern)


if __name__ == '__main__':
  ANDROID_PATTERN = (
    "project:path,name,revision,group",
    "remote:name,fetch,review",
    "copyfile:src,dest",
    "linkfile:src,dest")

  parser = OptionParser('''
%prog [Option] input.xml output.xml''')
  group = parser.add_option_group('File options')
  group.add_option(
    '-f', '--file',
    dest='file', metavar='INPUT',
    help='file to open for sort')
  group.add_option(
    '-o', '--output',
    dest='output', metavar='OUTPUT',
    help='file to store the sorted xml. stdout will be used if not provided')
  group.add_option(
    '-i', '--inplace',
    dest='inplace', action='store_true', default=False,
    help='update the input file in place instead of an output file')

  group = parser.add_option_group('Pattern options')
  group.add_option(
    '-p', '--pattern',
    dest='pattern', action='append',
    help='sort pattern like "element:attr1,attr2,..."')
  group.add_option(
    '--android',
    dest='android', action='store_true',
    help='set pattern to "project:path,name,revision,group '
         'remote:name,fetch,review copyfile:src,dest linkfile:src,dest"')

  group = parser.add_option_group('Sorting options')
  group.add_option(
    '-C', '--case-insensitive',
    dest='case', action='store_true', default=False,
    help='sort with case insenstive comparison')
  group.add_option(
    '-c', '--comment',
    dest='ignore_comment', action='store_true', default=False,
    help='ignore the comment elements')
  group.add_option(
    '-k', '--keep-element-order',
    dest='keep_order', action='store_true', default=False,
    help='keep the occurrence order for elements')
  group.add_option(
    '-g', '--group',
    dest='use_group', action='store_true', default=False,
    help='group the elements with a blank and a comment ahead')

  opts, args = parser.parse_args()
  if not opts.file:
    if args:
      opts.file = args.pop(0)
  if not opts.output:
    if args:
      opts.output = args.pop(0)

  if opts.inplace:
    if opts.output:
      print 'Warning: "%s" will be replaced with "%s" in place' % (
        opts.file, opts.output)

    opts.output = opts.file

  if not opts.file:
    print('Error: No xml file to sort')
  else:
    if opts.android:
      if opts.pattern:
        opts.pattern.extend(ANDROID_PATTERN)
      else:
        opts.pattern = ANDROID_PATTERN

    objx = _parse_xml(
        opts.file, Pattern(opts.pattern, opts.case),
        Options(opts.keep_order, opts.use_group, opts.ignore_comment))

    @contextlib.contextmanager
    def _open(output, mode):
      if output:
        fp = open(output, mode)
      else:
        fp = sys.stdout

      try:
        yield fp
      finally:
        if fp is not sys.stdout:
          fp.close()

    xml = objx.dump()
    with _open(opts.output, 'w') as fp:
      fp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
      fp.write(xml)
