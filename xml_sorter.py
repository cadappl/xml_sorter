#!/usr/bin/env python

import sys
import xml.dom.minidom

from optparse import OptionParser

class Pattern(object):
  def __init__(self, patterns):
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

        return sys.maxint

      def __init__(this, obj, *args):
        this.obj = obj
        this.order = this._order(obj)

      def __lt__(this, other):
        order = this._order(other.obj)
        if order == this.order:
          return str(this.obj) < str(other.obj)
        else:
          return this.order < order

      def __gt__(this, other):
        order = this._order(other.obj)
        if order == this.order:
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


class Element(object):
  def __init__(self, name, pattern):
    self.name = name
    self.pattern = pattern
    self.attrs = dict()
    self.children = list()

  def __repr__(self):
    return self.dump()

  def normal(self):
    return not self.name.startswith('#')

  def attr(self, attr, value):
    self.attrs[attr] = value

  def child(self, child):
    self.children.append(child)

  def dump(self, indent=''):
    vals = ''
    if self.normal():
      vals = '%s<%s' % (indent, self.name)

      attrs = self.pattern.sort(self.attrs, self.name)
      for attr in attrs:
        vals += ' %s="%s"' % (attr, self.attrs[attr])

    if len(self.children) == 0:
      if self.normal():
        vals += '/>'
    else:
      if self.normal():
        vals += '>\n'

      extra = '  ' if self.normal() else ''
      for child in self.pattern.sort(self.children):
        nval = child.dump(indent=indent + extra)
        if nval:
          vals += nval
          vals += '\n'

      if self.normal():
        vals += '</%s>' % self.name

    return vals


def _handle_node(node, pattern):
  elem = Element(node.nodeName, pattern)

  # hack into minidom.py
  if hasattr(node, '_attrs'):
    for attr in node._attrs:
      elem.attr(attr, node.getAttribute(attr))

  for child in node.childNodes:
    celem = _handle_node(child, pattern)
    if celem.normal():
      elem.child(celem)

  return elem


def _parse_xml(filename, pattern):
  root = xml.dom.minidom.parse(filename)

  return _handle_node(root, pattern)


if __name__ == '__main__':
  parser = OptionParser('''
%prog [Option] input.xml output.xml''')
  group = parser.add_option_group('Pattern options')
  group.add_option(
    '-p', '--pattern',
    dest='pattern', action='append',
    help='sort pattern like "element:attr1,attr2,..."')

  group = parser.add_option_group('File options')
  group.add_option(
    '-f', '--file',
    dest='file', metavar='INPUT',
    help='file to open for sort')
  group.add_option(
    '-o', '--output',
    dest='output', metavar='OUTPUT',
    help='file to store the sorted xml. stdout will be used if not provided')

  opts, args = parser.parse_args()
  if not opts.file:
    if args:
      opts.file = args.pop(0)
  if not opts.output:
    if args:
      opts.output = args.pop(0)

  if not opts.file:
    print 'Error: No xml file to sort'
  else:
    objx = _parse_xml(opts.file, Pattern(opts.pattern))
    xml = objx.dump()
    if not opts.output:
      print xml
    else:
      with open(opts.output, 'w') as fp:
        fp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fp.write(xml)
