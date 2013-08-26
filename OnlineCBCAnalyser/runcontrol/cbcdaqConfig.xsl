<!-- Copyright 2012 Institut Pluridisciplinaire Hubert Curien
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Programmer : 	Christian Bonnin
   Version : 		1.0
   Date of creation :   14/01/2013
   Support : 		mail to : christian.bonnin@iphc.cnrs.fr
-->
<!--HTML presentation of DAQ runcontrol XML configuration file -->
<!--Uses XSL attribute, sort, param -->
<xsl:stylesheet version = '1.0' 
   xmlns:supervisor='urn:xdaq-application:GlibSupervisor'
   xmlns:streamer='urn:xdaq-application:GlibStreamer'
   xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
   xmlns:xc='http://xdaq.web.cern.ch/xdaq/xsd/2004/XMLConfiguration-30'>

<xsl:template match="/"> 
<html><body>
<H2>RunControl applications</H2>
	Board name for GlibSupervisor: <b><xsl:value-of select="/xc:Partition/xc:Context/xc:Application/supervisor:properties/supervisor:BoardName"/></b>,
	GlibStreamer: <b><xsl:value-of select="/xc:Partition/xc:Context/xc:Application/streamer:properties/streamer:BoardName"/></b><br/>
	<a href="http://localhost.localdomain:9999/urn:xdaq-application:lid=10/">JobControl</a>

	<xsl:apply-templates select="/xc:Partition/xc:Context">
		<xsl:sort select="@url"/>
	</xsl:apply-templates>
</body></html> 
</xsl:template>

<xsl:template match="xc:Context">
	<h3>Context: <a><xsl:attribute name="href"><xsl:value-of select="@url"/></xsl:attribute><xsl:value-of select="@url"/></a></h3>
	<table border="1">	
	<tr><th>Class</th><th>ID</th><th>Instance</th><th>network</th></tr>
	<xsl:apply-templates select="xc:Application">
		<xsl:with-param name="url" select="@url"/>
	</xsl:apply-templates>
	</table>
</xsl:template>

<xsl:template match="xc:Application">
	<xsl:param name="url"/>
	<xsl:variable name="afterHttp" select="substring-after($url, 'http://')"/>
	<tr>
		<td>
		  <a>
		    <xsl:attribute name="href"> 
			<xsl:value-of select="concat('http://',substring-before($afterHttp, ':'), '.localdomain:', substring-after($afterHttp, ':'))"/>/urn:xdaq-application:lid=<xsl:value-of select="@id"/>/
		    </xsl:attribute>
		    <xsl:value-of select="@class"/>
 		  </a>
		</td>
		<td><xsl:value-of select="@id"/></td>
		<td><xsl:value-of select="@instance"/></td>
		<td><xsl:value-of select="@network"/></td>
	</tr>
</xsl:template>

</xsl:stylesheet>


