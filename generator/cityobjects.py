import re, requests, sys
import xml.etree.ElementTree as ET
import clang.cindex

baseUrl = 'https://schemas.opengis.net/citygml/'

# This assumes python is run in the project's root folder - i.e. `python generator/cityobjects.py`
cityobjectFile = './sources/include/citygml/cityobject.h'

def getProfilePaths(xsdDoc):
	content = requests.get(baseUrl + xsdDoc)
	root = ET.fromstring(content.text)
	paths = []
	for rootElement in root:
		match rootElement.tag:
			case 'import' | '{http://www.w3.org/2001/XMLSchema}import':
				location = rootElement.attrib['schemaLocation'].replace("http", "https")
				if baseUrl not in location:
					print(location)
					raise RuntimeError("import comes from other url.")
				paths.append(location[len(baseUrl):])
	return paths

def findExtension(element):
	for path in [
			'./{http://www.w3.org/2001/XMLSchema}complexContent/{http://www.w3.org/2001/XMLSchema}extension',
			'./complexContent/extension',
			'./{http://www.w3.org/2001/XMLSchema}complexContent/{http://www.w3.org/2001/XMLSchema}restriction',
			'./complexContent/restriction'
		]:
		extension = element.find(path)
		if extension != None:
			return extension
	return None

def extendsAnyInSet(element, types):
	extension = findExtension(element)
	if extension != None:
		base = extension.attrib['base']
		# Do some sloppy namespace handling. It's safe because we know that the citygml spec doesn't have duplicate types
		if ':' in base:
			base = base.split(':')[1]
		return base in types
	return False

def find_enums(node, mainFile, enumName):
	result = []
	if node.kind == clang.cindex.CursorKind.ENUM_DECL and node.spelling == enumName:
		for enum_constant in node.get_children():
			if enum_constant.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
				result.append([enum_constant.spelling, enum_constant.location.line])
	else:
		for child in node.get_children():
			# only check the file we actually want to parse - ignore includes
			if child.location.file != None and child.location.file.name.endswith(mainFile):
				result += find_enums(child, mainFile, enumName)
	return result

def getCityObjectTypesFromHeader():
	clang.cindex.Config.set_library_path('C:/Program Files/LLVM/bin')
	index = clang.cindex.Index.create()
	include_dirs = ['-I', 'C:/dev/git/libcitygml/sources/include', '-x', 'c++']
	cityObjectHeader = index.parse(cityobjectFile, args=include_dirs)
	enums = find_enums(cityObjectHeader.cursor, cityobjectFile[2:], 'CityObjectsType')

	enums = [enum for enum in enums if enum[0] != 'COT_All']
	return enums

def removeSchema(name):
	return name if ':' not in name else name.split(':')[1]

def readCompleteXsdElementsThatExtend(xsdPaths, initialTypes):
	cityObjectTypes = set(initialTypes)
	completeCityObjectTypes = set()
	completeCityObjectElements = set()

	for xsdDoc in xsdPaths + xsdPaths:
		content = requests.get(baseUrl + xsdDoc)
		root = ET.fromstring(content.text)

		# The order of types and elements in the xsd file is free - therefore types can be used before they are defined
		# This breaks our "stupid" approach of reading top to bottom and we need to loop through the xsd file until nothing new is discovered
		changed = True
		while changed:
			changed = False
			for rootElement in root:
				match rootElement.tag:
					case 'complexType' | '{http://www.w3.org/2001/XMLSchema}complexType':
						typeName = removeSchema(rootElement.attrib['name'])
						if typeName not in cityObjectTypes and extendsAnyInSet(rootElement, cityObjectTypes):
							changed = True
							cityObjectTypes.add(typeName)
							if 'abstract' not in rootElement.attrib or rootElement.attrib['abstract'] != 'true':
								completeCityObjectTypes.add(typeName)
					case 'element' | '{http://www.w3.org/2001/XMLSchema}element':
						type = removeSchema(rootElement.attrib['type'])
						if ('abstract' not in rootElement.attrib or rootElement.attrib['abstract'] != 'true') and type in completeCityObjectTypes:
							# We don't need to loop again if we detect new elements - these are terminal i.e. not referenced
							completeCityObjectElements.add(rootElement.attrib['name'])
		if 'progress' in sys.argv:
			print("Done with", xsdDoc)

	if 'verbose' in sys.argv:
		print("All Types:", sorted(cityObjectTypes))
		print("Complete Types:", sorted(completeCityObjectTypes))

	return completeCityObjectElements


if __name__ == '__main__':
	# Handling all types from all versions together is a bit of a gamble but hopefully it's fine.
	xsdPaths = ['1.0/cityGMLBase.xsd'] + getProfilePaths("profiles/base/1.0/CityGML.xsd") + ['2.0/cityGMLBase.xsd'] + getProfilePaths("profiles/base/2.0/CityGML.xsd") + ['3.0/core.xsd'] + getProfilePaths("profiles/base/3.0/CityGML.xsd")
	completeCityObjectElements = readCompleteXsdElementsThatExtend(xsdPaths, ['AbstractFeatureType'])

	headerTypes = getCityObjectTypesFromHeader()

	if 'check' in sys.argv:
		print("Elements:", sorted(completeCityObjectElements))
		oldTypes = [enum[0].replace('COT_', '') for enum in headerTypes]
		print("Old Types:", sorted(oldTypes))

		print("Missing Types:", sorted(set(oldTypes) - set(completeCityObjectElements) - set(['All'])))

	if 'fix' in sys.argv:
		with open(cityobjectFile, 'r') as inFile:
			inLines = inFile.readlines()

		lineStart = min(headerTypes, key=lambda x: x[1])
		lineEnd = max(headerTypes, key=lambda x: x[1])
		outLines = inLines[0:lineStart[1]-1]
		for element in sorted(completeCityObjectElements, key=lambda x: x[0]):
			outLines.append(f'            COT_{element},\n')
		outLines += inLines[lineEnd[1]+1:]
		with open(cityobjectFile, 'w') as outFile:
			outFile.writelines(outLines)
