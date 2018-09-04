#!/usr/bin/env python

import sys
import xml.dom.minidom


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
  objx = _parse_xml(sys.argv[1])
  print objx.dump()
