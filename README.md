![](https://img.shields.io/badge/python-2.7%2C%203.6-blue.svg)

# XML sorting tool

The tool isn't a common to handle almost all XML files - it's the mere tool to
accomplish the author's work. What's more, it *hacked* `xml.dom.minidom` with
internal attributes (`Element._attr` and `Element.data`) for all element
attributes and data to simplify the code - Though it works with both Python 2.7
and 3.6, it's not an official implementation.

It works only with XML normal elements, comments and common data fields. It
hasn't supported CDATA, characters, etc. Because it's a specific tool (to
handle Android `manifest.xml` frankly), new features may not be impelemented.

The tool could be used to sort the element attributes, for example, the
attributes of an Android project:

`<project groups="pdk" name="platform/art" path="art" revision="refs/tags/android-8.1.0_r43"/>`

With the matched pattern for the element `project`
`project:path,name,revision,groups`, the output xml would be:

`<project path="art" name="platform/art" revision="refs/tags/android-8.1.0_r43" groups="pdk"/>`

And with the option `-k`, the occurence order will be kept not to change the XML
so much. It'll keep the orders of `remote` and `default` in Android
`default.xml`.

Option `-g` will detect the flags like `@foo(bar)` in the xml comments and
categorize the elements following the comments as a group for sorting. It'll be
useful when spliting the xml into several parts with the specific comment lines.