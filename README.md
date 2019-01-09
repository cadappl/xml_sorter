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

The tool could be used to sort the elements, and element attributes. The pattern
has the format `element:attr1,attr2,...`. If element isn't provided, the
attributes will be effective to all existent elements. For example, the
attributes of an Android project could be sorted:

`<project groups="pdk" name="platform/art" path="art" revision="refs/tags/android-8.1.0_r43"/>`

With the matched pattern only for the element `project`
`project:path,name,revision,groups`, the output element would be:

`<project path="art" name="platform/art" revision="refs/tags/android-8.1.0_r43" groups="pdk"/>`

The output `project` starting with sorted attribute `path` would be good to
investigate the directory structures of git-repositories in an Android project.

# Options

Option `-C` can do case-insenstive compare of two elements. And with the option
`-k`, the occurence order will be kept not to change the XML so much. It'll
keep the orders of `remote` and `default` in Android `default.xml`.

Option `-g` will detect the flags like `@foo(bar)` in the xml comments and
categorize the elements following the comments as a group for sorting. It'll be
useful when spliting the xml into several parts with the specific comment lines.

A new option `--android` is added to append following patterns for Android
specific xml file:

- `project:path,name,revision,groups`
- `remote:name,fetch,review`
- `copyfile:src,dest`
- `linkfile:src,dest`

To handle the Android xml file, the command link could be:

```bash
$ xml_sorter.py -C -k --android -f default.xml -o sorted.xml
```

The option `-o` would be ignored if option `-i` is used to update the xml file
in place.

What's more. An extra option `-r` (`--omit`) has been implemented to omit some
elmenent or element attributes. The matched pattern are the same like the one
for sort. The only difference is the pattern will be treated as `element` if no
colon as the delimiter is provided.

And option `-x` is designed to omit the duplicates attributes if corresponding
patterns are provided. The original pattern has been expanded like
`elem:attr1=attr2,attr3,...`. With the option, once the value of `attr2` is
equaling to the one of `attr1`, the entire attribute `attr2` will be omitted
in the output. For example, with the option `-x "project:name=path"`:

```xml
<project path="device/generic/x86" name="device/generic/x86" groups="pdk" />
```

the duplicated `path` attribute will be omitted to

```xml
<project name="device/generic/x86" groups="pdk" />
```
