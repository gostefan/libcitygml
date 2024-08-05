/* -*-c++-*- libcitygml - Copyright (c) 2010 Joachim Pouderoux, BRGM
*
* This file is part of libcitygml library
* http://code.google.com/p/libcitygml
*
* libcitygml is free software: you can redistribute it and/or modify
* it under the terms of the GNU Lesser General Public License as published by
* the Free Software Foundation, either version 2.1 of the License, or
* (at your option) any later version.
*
* libcitygml is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Lesser General Public License for more details.
*/

#include <citygml/citygml.h>
#include <citygml/citygmllogger.h>

#include <fstream>
#include <string>
#include <memory>
#include <mutex>

#include <citygml/citygml_api.h>
#include "citygml/tesselatorbase.h"
#include "parser/citygmldocumentparser.h"
#include "parser/documentlocation.h"
#include "parser/attributes.h"
#include "parser/stdlogger.h"

#include <libxml/tree.h>
#include <libxml/parser.h>
#include <libxml/parserInternals.h>

using namespace citygml;

/*
std::string toStdString( const XMLCh* const wstr )
{
    if (wstr == nullptr) {
        return "";
    }

    char* tmp = xercesc::XMLString::transcode(wstr);
    std::string str(tmp);
    xercesc::XMLString::release(&tmp);
    return str;
}

std::shared_ptr<XMLCh> toXercesString(const std::string& str) {

    XMLCh* conv = xercesc::XMLString::transcode(str.c_str());
    // Pack xerces string into shared_ptr with custom delete function
    return std::shared_ptr<XMLCh>(conv, [=](XMLCh* str) {
        xercesc::XMLString::release(&str);
    });
}
*//*
class DocumentLocationLibxml2Adapter : public citygml::DocumentLocation {
public:
    explicit DocumentLocationXercesAdapter(const std::string& fileName)
        : m_locator(nullptr)
        , m_fileName(fileName)
    {

    }

    void setLocator(const xercesc::Locator* locator) {
        m_locator = locator;
    }

    // DocumentLocation interface
    const std::string& getDocumentFileName() const override {
        return m_fileName;
    }

    uint64_t getCurrentLine() const override {
        return m_locator != nullptr ? m_locator->getLineNumber() : 0;
    }
    uint64_t getCurrentColumn() const override {
        return m_locator != nullptr ? m_locator->getColumnNumber() : 0;
    }

protected:
    const xercesc::Locator* m_locator;
    std::string m_fileName;
};
*//*
class AttributesLibxml2Adapter : public citygml::Attributes {
public:
    AttributesXercesAdapter(const xercesc::Attributes& attrs, const citygml::DocumentLocation& docLoc, std::shared_ptr<CityGMLLogger> logger)
     : citygml::Attributes(logger), m_attrs(attrs), m_location(docLoc) {}

    // Attributes interface
    std::string getAttribute(const std::string& attname, const std::string& defvalue) const override {
        std::shared_ptr<XMLCh> name = toXercesString(attname);
        std::string value = toStdString(m_attrs.getValue(name.get()));
        return value.empty() ? defvalue : value;
    }

    const DocumentLocation& getDocumentLocation() const override {
        return m_location;
    }

protected:
    const xercesc::Attributes& m_attrs;
    const citygml::DocumentLocation& m_location;
};
*/
// CityGML Xerces-c SAX parsing handler
/*
class CityGMLHandlerLibxml2 : public xercesc::DefaultHandler, public citygml::CityGMLDocumentParser
{
public:
    CityGMLHandlerLibxml2( const ParserParams& params, const std::string& fileName, std::shared_ptr<CityGMLLogger> logger, std::unique_ptr<TesselatorBase> tesselator)
        : citygml::CityGMLDocumentParser(params, logger, std::move(tesselator)), m_documentLocation(DocumentLocationXercesAdapter(fileName)) {}


    // ContentHandler interface
    void startElement(const XMLCh* const, const XMLCh* const, const XMLCh* const qname, const xercesc::Attributes& attrs) override {
        AttributesLibxml2Adapter attributes(attrs, m_documentLocation, m_logger);
        // We need to empty m_lastcharacters here, because if a tag is empty, characters(...) will never be called and this variable will contain wrong values
        m_lastcharacters = "";
        CityGMLDocumentParser::startElement(toStdString(qname), attributes);
    }

    void endElement(const XMLCh* const, const XMLCh* const, const XMLCh* const qname) override {
        CityGMLDocumentParser::endElement(toStdString(qname), m_lastcharacters);
        m_lastcharacters = "";
    }

    void characters(const XMLCh* const chars, const XMLSize_t) override {
        m_lastcharacters += toStdString(chars);
    }

    void startDocument() override {
        CityGMLDocumentParser::startDocument();
    }

    void endDocument() override {
        CityGMLDocumentParser::endDocument();
    }

    void setDocumentLocator(const xercesc::Locator* const locator) override {
        m_documentLocation.setLocator(locator);
    }

    // CityGMLDocumentParser interface
    const citygml::DocumentLocation& getDocumentLocation() const override {
        return m_documentLocation;
    }
protected:
    DocumentLocationLibxml2Adapter m_documentLocation;
    std::string m_lastcharacters;

};
*/
/*
class StdBinInputStream : public xercesc::BinInputStream
{
public:
    explicit StdBinInputStream( std::istream& stream ) : BinInputStream(), m_stream( stream ) {}

    ~StdBinInputStream() override {}

    XMLFilePos curPos() const override { return m_stream.tellg(); }

    XMLSize_t readBytes( XMLByte* const buf, const XMLSize_t maxToRead ) override
    {
        assert( sizeof(XMLByte) == sizeof(char) );
        if ( !m_stream ) return 0;
        m_stream.read( reinterpret_cast<char*>(buf), maxToRead );
        return (XMLSize_t)m_stream.gcount();
    }

    const XMLCh* getContentType() const override { return nullptr; }

private:
    std::istream& m_stream;
};

class StdBinInputSource : public xercesc::InputSource
{
public:
    explicit StdBinInputSource( std::istream& stream ) : m_stream( stream ) {}

    xercesc::BinInputStream* makeStream() const override
    {
        return new StdBinInputStream( m_stream );
    }

    ~StdBinInputSource() override {
    }

private:
    std::istream& m_stream;
};
*/
// Parsing methods
namespace citygml
{
    std::mutex libxml2_init_mutex;
    std::atomic_bool libxml2_initialized;

    bool initLibxml2(std::shared_ptr<CityGMLLogger> logger) {

        if (libxml2_initialized.load()) {
            return true;
        }

        try {
            std::lock_guard<std::mutex> lock(libxml2_init_mutex);
            // Check xerces_initialized again... it could have changed while waiting for the mutex
            if (!libxml2_initialized.load()) {
                xmlInitParser();
                libxml2_initialized.exchange(true);
            }
        }
        catch (...) { // TODO: const xercesc::XMLException& e) {
            // TODO: CITYGML_LOG_ERROR(logger, "Could not initialize xercesc XMLPlatformUtils, a XML Exception occurred : " << toStdString(e.getMessage()));
            return false;
        }

        return true;

    }

	constexpr size_t TMP_DATA_SIZE = 10 * 1024 * 1024;

	void parse(xmlSAXHandlerPtr sax, void* userData, std::string const& filename) {
		xmlSAXUserParseFile(sax, userData, filename.c_str());
	}

	void parse(xmlSAXHandlerPtr sax, void* userData, std::istream& stream) {
		xmlParserCtxtPtr parserCtxt = xmlCreatePushParserCtxt(sax, userData, nullptr, 0, "default.gml");
		char tmpData[TMP_DATA_SIZE];
		int readCount;
		do {
			stream.read(tmpData, TMP_DATA_SIZE);
			readCount = static_cast<int>(stream.gcount()); // this is bounded by TMP_DATA_SIZE
			static_assert(std::numeric_limits<decltype(readCount)>::max() > TMP_DATA_SIZE, "readCount cannot cover the size of TMP_DATA_SIZE");
			xmlParseChunk(parserCtxt, tmpData, readCount, readCount == TMP_DATA_SIZE ? 0 : 1);
		} while (readCount == TMP_DATA_SIZE);
	}

	template <typename T>
    std::shared_ptr<const CityModel> parse(T& input, const ParserParams& params, std::shared_ptr<CityGMLLogger> logger, std::unique_ptr<TesselatorBase> tesselator, std::string filename = "") {

        xmlSAXHandler saxHandler;
        /*CityGMLHandlerXerces handler( params, filename, logger, std::move(tesselator) );

        xercesc::SAX2XMLReader* parser = xercesc::XMLReaderFactory::createXMLReader();
        parser->setFeature(xercesc::XMLUni::fgSAX2CoreNameSpaces, false);
        parser->setContentHandler( &handler );
        parser->setErrorHandler( &handler );*/

#ifdef NDEBUG
        try
        {
#endif
            parse(&saxHandler, nullptr, input);
#ifdef NDEBUG
        }
        /*catch ( const xercesc::XMLException& e )
        {
            CITYGML_LOG_ERROR(logger, "XML Exception occurred: " << toStdString(e.getMessage()));
        }
        catch ( const xercesc::SAXParseException& e )
        {
            CITYGML_LOG_ERROR(logger, "SAXParser Exception occurred: " << toStdString(e.getMessage()));
        }*/
        catch ( const std::exception& e )
        {
            CITYGML_LOG_ERROR(logger, "Unexpected Exception occurred: " << e.what());
        }
#endif

        /*    delete parser;

        return handler.getModel();*/
    }

    template <typename T>
    std::shared_ptr<const CityModel> loadInternal(T& input, const ParserParams& params, std::unique_ptr<TesselatorBase>& tesselator, std::shared_ptr<CityGMLLogger>& logger)
    {
        if (!logger) {
            logger = std::make_shared<StdLogger>();
            if(tesselator) {
                tesselator->setLogger(logger);
            }
        }

        if (!initLibxml2(logger)) {
            return nullptr;
        }

#ifdef NDEBUG
        try {
#endif
        return parse(input, params, logger, std::move(tesselator));
#ifdef NDEBUG
        } catch (...) { // TODO: xercesc::XMLException& e) {
            // TODO: CITYGML_LOG_ERROR(logger, "Error parsing file " << fname << ": " << e.getMessage());
            return nullptr;
        }
#endif

    }
    std::shared_ptr<const CityModel> load(std::istream& stream, const ParserParams& params, std::unique_ptr<TesselatorBase> tesselator, std::shared_ptr<CityGMLLogger> logger)
    {
        return loadInternal(stream, params, tesselator, logger);
    }

    std::shared_ptr<const CityModel> load( const std::string& fname, const ParserParams& params, std::unique_ptr<TesselatorBase> tesselator, std::shared_ptr<CityGMLLogger> logger)
    {
        return loadInternal(fname, params, tesselator, logger);
    }
}

