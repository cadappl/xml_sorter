#!/usr/bin/env python

import xml.dom.minidom

from optparse import OptionParser


class Element(object):
  def __init__(self, name):
    self.name = name
    self.attrs = dict()
    self.children = list()

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

      for attr, value in self.attrs.items():
        vals += ' %s="%s"' % (attr, value)

    if len(self.children) == 0:
      if self.normal():
        vals += '/>'
    else:
      if self.normal():
        vals += '>\n'

      extra = '  ' if self.normal() else ''
      for child in self.children:
        nval = child.dump(indent=indent + extra)
        if nval:
          vals += nval
          vals += '\n'

      if self.normal():
        vals += '</%s>' % self.name

    return vals


def _handle_node(node):
  elem = Element(node.nodeName)

  # hack into minidom.py
  if hasattr(node, '_attrs'):
    for attr in node._attrs:
      elem.attr(attr, node.getAttribute(attr))

  for child in node.childNodes:
    elem.child(_handle_node(child))

  return elem


def _parse_xml(filename):
  root = xml.dom.minidom.parse(filename)

  return _handle_node(root)


if __name__ == '__main__':
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
    objx = _parse_xml(opts.file)
    xml = objx.dump()
    if not opts.output:
      print xml
    else:
      with open(opts.output, 'w') as fp:
        fp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fp.write(xml)
