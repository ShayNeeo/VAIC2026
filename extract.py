import zipfile, xml.etree.ElementTree as ET, sys
z = zipfile.ZipFile(sys.argv[1])
root = ET.fromstring(z.read('word/document.xml'))
text = [n.text for n in root.iter() if n.tag.endswith('t') and n.text]
with open('extracted_doc.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(text))
