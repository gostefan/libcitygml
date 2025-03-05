import re, requests, sys
import xml.etree.ElementTree as ET
import clang.cindex

baseUrl = 'https://schemas.opengis.net/citygml/'

# This assumes python is run in the project's root folder - i.e. `python generator/cityobjects.py`
includeDir = 'C:/dev/git/libcitygml/sources/include'
cityobjectFile = './sources/include/citygml/cityobject.h'
parserFile = './sources/src/parser/cityobjectelementparser.cpp'

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
				relUrl = location[len(baseUrl):]
				namespace = ''
				match relUrl.split('/')[0]:
					case '1.0' | '2.0' | '3.0':
						namespace = 'core'
					case 'appearance':
						namespace = 'app'
					case 'bridge':
						namespace = 'brid'
					case 'building':
						namespace = 'bldg'
					case 'cityfurniture':
						namespace = 'frn'
					case 'cityobjectgroup':
						namespace = 'grp'
					case 'construction':
						namespace = 'con'
					case 'dynamizer':
						namespace = 'dyn'
					case 'generics':
						namespace = 'gen'
					case 'landuse':
						namespace = 'luse'
					case 'pointcloud':
						namespace = 'pcl'
					case 'relief':
						namespace = 'dem'
					case 'texturedsurface':
						namespace = 'tex'
					case 'transportation':
						namespace = 'trans' # TODO: Should be 'tran'
					case 'tunnel':
						namespace = 'sub' # TODO: Should be 'tun'
					case 'vegetation':
						namespace = 'veg'
					case 'versioning':
						namespace = 'vers'
					case 'waterbody':
						namespace = 'wtr'
					case _:
						raise RuntimeError("Unknown namespace.")
				paths.append([namespace, relUrl])
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
	index = clang.cindex.Index.create()
	include_dirs = ['-I', includeDir, '-x', 'c++']
	cityObjectHeader = index.parse(cityobjectFile, args=include_dirs)
	enums = find_enums(cityObjectHeader.cursor, cityobjectFile[2:], 'CityObjectsType')

	enums = [enum for enum in enums if enum[0] != 'COT_All']
	return enums

'''
def output_cursor_and_children(cursor, main_file, level=0):
    """ Output this cursor and its children with minimal formatting """
    if cursor.spelling.startswith('_'):
        return
    if cursor.location.file and cursor.location.file.name == main_file or cursor.spelling == main_file:
        output_cursor(cursor, level)
        if cursor.kind.is_reference():
            print(indent(level) + 'reference to:')
            # output_cursor(clang.cindex.Cursor_ref(cursor), level + 1)

        # Recurse for children of this cursor
        has_children = False
        for c in cursor.get_children():
            if not has_children:
                print(indent(level) + '{')
                has_children = True
            output_cursor_and_children(c, main_file, level + 1)

        if has_children:
            print(indent(level) + '}')

def output_cursor(cursor, level):
    """ Low level cursor output """
    spelling = cursor.spelling if cursor.spelling else ''
    displayname = cursor.displayname if cursor.displayname else ''
    kind = cursor.kind

    print(indent(level) + spelling, '<' + str(kind) + '>')
    print(indent(level + 1) + '"' + displayname + '"')

def indent(level):
    """ Indentation string for pretty-printing """
    return '  ' * level
'''

def parseTypeMapInsert(node):
    node = next(node.get_children(), None)
    node = next((child for child in node.get_children() if child.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR), None)
    node = next(node.get_children(), None)
    node = list(node.get_children())[4]
    node = next(node.get_children(), None)
    node = next(node.get_children(), None)
    node = next(node.get_children(), None)
    node = next(node.get_children(), None)

    matches = re.search(r'([A-Z]+)_(.+)Node', node.spelling)
    return [[matches.groups()[0], matches.groups()[1]], node.location.line]

def findTypeMap(node, mainFile, enumName):
    result = []
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL and node.spelling == 'getTypeIDTypeMap':
        # grab method content
        initLambda = next((child for child in node.get_children() if child.kind == clang.cindex.CursorKind.COMPOUND_STMT), None)
        # grab declaration
        initLambda = next((child for child in initLambda.get_children() if child.kind == clang.cindex.CursorKind.DECL_STMT), None)
        initLambda = next(initLambda.get_children(), None)
        # grab lambda
        initLambda = next((child for child in initLambda.get_children() if child.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)
        initLambda = next(initLambda.get_children(), None)

        for child in initLambda.get_children():
            if child.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR:
                result.append(parseTypeMapInsert(child))
    else:
        for child in node.get_children():
            # only check the file we actually want to parse - ignore includes
            if child.location.file != None and child.location.file.name.endswith(mainFile):
                result += findTypeMap(child, mainFile, enumName)
    return result

def getCityObjectTypesFromParser():
    index = clang.cindex.Index.create()
    args = ['-I', includeDir, '-x', 'c++']
    cityObjectHeader = index.parse(parserFile, args=args)

    enums = findTypeMap(cityObjectHeader.cursor, parserFile, 'CityObjectsType')

    return enums

def removeSchema(name):
	return name if ':' not in name else name.split(':')[1]

def readCompleteXsdElementsThatExtend(xsdPaths, initialTypes):
	cityObjectTypes = set(initialTypes)
	completeCityObjectTypes = {}
	completeCityObjectElements = {}

	for xsdDoc in xsdPaths + xsdPaths:
		content = requests.get(baseUrl + xsdDoc[1])
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
								completeCityObjectTypes.setdefault(typeName, set()).add(xsdDoc[0])
					case 'element' | '{http://www.w3.org/2001/XMLSchema}element':
						type = removeSchema(rootElement.attrib['type'])
						if ('abstract' not in rootElement.attrib or rootElement.attrib['abstract'] != 'true') and type in completeCityObjectTypes:
							# We don't need to loop again if we detect new elements - these are terminal i.e. not referenced
							completeCityObjectElements.setdefault(rootElement.attrib['name'], set()).add(xsdDoc[0])
		if 'progress' in sys.argv:
			print("Done with", xsdDoc)

	if 'verbose' in sys.argv:
		print("All Types:", sorted(cityObjectTypes))
		print("Complete Types:", sorted(completeCityObjectTypes, key=lambda x: x[0]))

	return completeCityObjectElements


if __name__ == '__main__':
	clang.cindex.Config.set_library_path('C:/Program Files/LLVM/bin')

	# Handling all types from all versions together is a bit of a gamble but hopefully it's fine.
	xsdPaths = [['core', '1.0/cityGMLBase.xsd']] + getProfilePaths("profiles/base/1.0/CityGML.xsd") + [['core', '2.0/cityGMLBase.xsd']] + getProfilePaths("profiles/base/2.0/CityGML.xsd") + [['core', '3.0/core.xsd']] + getProfilePaths("profiles/base/3.0/CityGML.xsd")
	completeCityObjectElements = readCompleteXsdElementsThatExtend(xsdPaths, ['AbstractFeatureType'])

	headerTypes = getCityObjectTypesFromHeader()
	parserTypes = getCityObjectTypesFromParser()

	if 'check' in sys.argv:
		oldHeaderTypes = [enum[0].replace('COT_', '') for enum in headerTypes]
		oldParserTypes = [enum[0][0] + enum[0][1] for enum in parserTypes]
		newParserTypes = []
		for element, namespaces in completeCityObjectElements.items():
			if len(namespaces) > 1:
				print(element, "occurs in multiple namespaces:", namespaces)
			for namespace in namespaces:
				newParserTypes.append(namespace.upper() + element)

		missingHeaderTypes = set(oldHeaderTypes) - set(completeCityObjectElements) - set(['All'])
		if len(missingHeaderTypes) == 0:
			print("All old header types found.")
		else:
			print("Missing Header Types:", sorted(missingHeaderTypes))
			print("New Header Types:", sorted(completeCityObjectElements))
			print("Old Header Types:", sorted(oldHeaderTypes))

		missingParserTypes = set(oldParserTypes) - set(newParserTypes)
		if len(missingParserTypes) == 0:
			print("All old parser types found.")
		else:
			print("Missing Parser Types:", sorted())
			print("New Parser Types:", sorted(newParserTypes))
			print("Old Parser Types:", sorted(oldParserTypes))

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

		elementsByNamespace = {}
		for element, namespaces in completeCityObjectElements.items():
			for namespace in namespaces:
				elementsByNamespace.setdefault(namespace, []).append(element)
		with open(parserFile, 'r') as inFile:
			inLines = inFile.readlines()
		lineStart = min(parserTypes, key=lambda x: x[1])
		lineEnd = max(parserTypes, key=lambda x: x[1])
		outLines = inLines[0:lineStart[1]-2] # we also remove the comment line above the first entry
		for namespace, elements in elementsByNamespace.items():
			outLines.append(f'                // {namespace.upper()}\n')
			for element in sorted(elements):
				outLines.append(f'                tmpTypeIDTypeMap.insert(HANDLE_TYPE({namespace.upper()}, {element}));\n')
		outLines += inLines[lineEnd[1]+1:]
		with open(parserFile, 'w') as outFile:
			outFile.writelines(outLines)
