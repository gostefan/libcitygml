#pragma once

#include <parser/gmlfeaturecollectionparser.h>

#include <citygml/cityobject.h>

#include <functional>
#include <unordered_map>
#include <unordered_set>
#include <mutex>

#include <citygml/cityobject.h>

namespace citygml {

    class CityObjectElementParser : public GMLFeatureCollectionElementParser {
    public:
        CityObjectElementParser(CityGMLDocumentParser& documentParser, CityGMLFactory& factory, std::shared_ptr<CityGMLLogger> logger, std::function<void(CityObject*)> callback);

        // ElementParser interface
        virtual std::string elementParserName() const override;
        virtual bool handlesElement(const NodeType::XMLNode &node) const override;
    protected:

        // CityGMLElementParser interface
        virtual bool parseElementStartTag(const NodeType::XMLNode& node, Attributes& attributes) override;
        virtual bool parseElementEndTag(const NodeType::XMLNode& node, const std::string& characters) override;
        virtual bool parseChildElementStartTag(const NodeType::XMLNode& node, Attributes& attributes) override;
        virtual bool parseChildElementEndTag(const NodeType::XMLNode& node, const std::string& characters) override;

        // GMLFeatureCollectionElementParser interface
        virtual FeatureObject* getFeatureObject() override;

    private:
        CityObject* m_model;
        std::function<void(CityObject*)> m_callback;
        std::string m_lastAttributeName;
        AttributeType m_lastAttributeType;
        CityObjectsTypeMask const m_typeMask; // TODO: Make this a reference once getParserParams doesn't return a copy
        bool m_skipped;

        void parseGeometryForLODLevel(int lod);
        void parseGeometryForLODLevel(int lod, CityObject::CityObjectsType parentType);
        void parseImplicitGeometryForLODLevel(int lod);
        void parseGeometryPropertyElementForLODLevel(int lod, const std::string& id);
    };

}
