Juupeli
=======

![Test](https://github.com/akx/juupeli/workflows/Test/badge.svg)

Encodes arbitrary Python data structures into XML in a reasonably sane way.

Usage
-----

Basically,

```
from juupeli import to_xml_string

x = to_xml_string(my_object)
```

should immediately do something usable.

Please see the tests for more advanced usage for the time being.

TODO
----

* Annotation support (for e.g. attributes)
* Decoding back to Python? Maybe?

Known issues
------------

* Nesting anonymous collections will cause flattening with the default codec
