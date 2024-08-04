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
#include <memory>

// Parsing methods
namespace citygml
{
    std::shared_ptr<const CityModel> load(std::istream& stream, const ParserParams& params, std::unique_ptr<TesselatorBase> tesselator, std::shared_ptr<CityGMLLogger> logger)
    {
        return std::shared_ptr<const CityModel>();
    }

    std::shared_ptr<const CityModel> load( const std::string& fname, const ParserParams& params, std::unique_ptr<TesselatorBase> tesselator, std::shared_ptr<CityGMLLogger> logger)
    {
        return std::shared_ptr<const CityModel>();
    }
}

