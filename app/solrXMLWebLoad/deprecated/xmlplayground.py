import sys
import lxml
from lxml import etree
from io import StringIO, BytesIO
# import queue


filename = r"X:\_PEPA1\_PEPa1v\_PEPArchive\IJP\043\IJP.043.0306A(bEXP_ARCH1).XML"
filename = r"X:\_PEPA1\_PEPa1v\_PEPArchive\APA\001.1953\APA.001.0706A(bEXP_ARCH1).XML"
filename = r"X:\_PEPa1\_PEPa1v\_PEPCurrent\rfp\RFP.2019.083\RFP.083.1605A(bKBD3).xml"

# fileXMLContents = f.read()
xml_data = b""
with open(filename, 'rb') as filehandle:
    for line in filehandle:
        xml_data += line
        
skiptagging = ["impx", "tab"]

#xml_tree = lxml.etree()
#parser = etree.XMLParser(ns_clean=True)
#tree   = etree.parse(StringIO(xml), parser)
#print etree.tostring(tree.getroot())

class FirstPageCollector:
    def __init__(self, skip_tags=["impx", "tab"]):
        self.events = []
        self.doc = "<abs>"
        self.in_body = False
        self.tag_stack = []
        self.skip_tags = skip_tags
        
    def start(self, tag, attrib):
        if tag not in self.skip_tags and self.in_body:
            self.events.append("start %s %r" % (tag, dict(attrib)))
            att_str = ""
            for key, val in attrib.items():
                att_str += f"{key}='{val}' "
            if att_str == "":
                att_str = att_str.rstrip()
                self.doc += f"<{tag}>"
            else:
                self.doc += f"<{tag} {att_str}>"
            self.tag_stack.append(tag)
        if tag == "body":
            self.in_body = True
    def end(self, tag):
        if tag not in self.skip_tags and self.in_body:
            self.events.append("end %s" % tag)
            self.doc += f"</{tag}>"
            self.tag_stack.pop()
        if self.in_body and tag == "pb":
            self.in_body = False # skip the rest.
            print ("Closing Document!",self.tag_stack)
            while len(self.tag_stack) > 0:
                tag_to_close = self.tag_stack.pop()
                self.doc += f"</{tag_to_close}>"
                print(f"Closed tag: {tag_to_close}")
            self.doc += "</abs>"
    def data(self, data):
        if self.in_body:
            self.events.append("data %r" % data)
            self.doc += f"{data}"
    def comment(self, text):
        self.events.append("comment %s" % text)
    def close(self):
        self.events.append("close")
        return self.doc

# xml_data = xml_data.decode("utf8")
parser = etree.XMLParser(target = FirstPageCollector(skip_tags=["impx"]))
result = etree.XML(xml_data, parser=parser)        # doctest: +ELLIPSIS

sys.exit()


parser = etree.XMLParser(load_dtd=True, resolve_entities=True)
try:
    doc = etree.parse(filename, parser=parser)
except Exception as e:
    logger.error(f"Error reading XML file {xml_file}", e)
    file_xml = ""
else:
    file_xml = etree.tostring(doc)


lines = 0
txt = ""
print (doc.getroot())
events = ("start", "end")
context = etree.iterparse(BytesIO(file_xml), events=events)
for action, elem in context:
    lines += 1
    if elem.tag == "body" and action == "start":
        txt = "<div>"
    elif txt == "":
        continue
    else:
        print (f"{lines}: {elem.tag} ({action})")
        if action == "start" and elem.tag not in skiptagging:
            txt += f"<{elem.tag}>"
            if elem.tag == "p":
                p_open = True
                
        if action == "end" and elem.text is not None:
            txt += elem.text

        if action == "end" and elem.tail is not None:
            txt += elem.tail

        if action == "end" and elem.tag not in skiptagging:
            txt += f"</{elem.tag}>"
            if elem.tag == "p":
                p_open = False
                
        if elem.tag == "pb" and action == "end":
            if p_open:
                txt += "</p>"
            txt += "</div>"
            break
    
print ("Done!")