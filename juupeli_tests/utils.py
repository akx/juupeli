from xml.dom import minidom


def prettify_xml(xml_string: str) -> str:
    dom = minidom.parseString(xml_string)
    return dom.toprettyxml()
