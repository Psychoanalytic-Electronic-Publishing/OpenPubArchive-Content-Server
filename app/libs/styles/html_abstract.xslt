<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    version="2.0">
<!-- xsl template declaration:  
template tells the xlst processor about the section of xml 
document which is to be formatted. It takes an XPath expression. 
In our case, it is matching document root element and will 
tell processor to process the entire document with this template. 
--> 
    
    <!-- variable to be used in div id's to keep them unique -->
    <xsl:variable name="this-article">
        <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>
    
    <xsl:template name="metadata-labeled-entry">
        <xsl:param name="label"/>
        <xsl:param name="contents">
            <span class="{$label}">
                <xsl:apply-templates/>
            </span>
        </xsl:param>
        <xsl:call-template name="metadata-entry">
            <xsl:with-param name="contents">
                <xsl:if test="normalize-space(string($label))">
                    <span class="label generated">
                        <xsl:copy-of select="$label"/>
                        <xsl:text>: </xsl:text>
                    </span>
                </xsl:if>
                <xsl:copy-of select="$contents"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    
    <xsl:template name="metadata-entry">
        <xsl:param name="contents">
            <xsl:apply-templates/>
        </xsl:param>
        <p class="metadata-entry">
            <xsl:copy-of select="$contents"/>
        </p>
    </xsl:template>
    

    <xsl:template match = "/"> 
        <!-- HTML tags 
         Used for formatting purpose. Processor will skip them and browser 
            will simply render them. 
        --> 
            
        <html> 
            <head></head>
            <body>
                <xsl:for-each select="artinfo">
                    <div id="{$this-article}-artinfo" class="artinfo" data-arttype="{@arttype}" data-journal="{@j}">
                        <div class="topciteas">
                            <span class="artyear"><xsl:value-of select="artyear"/></span>
                            <span class="title"><xsl:value-of select="arttitle"/></span>.
                            <span class="artvol"><a class="volx" href="http://www.pep-web.org/search.php?volume=51&amp;journal=ijp"><xsl:value-of select="artvol"/></a><span class="pgrg"><xsl:value-of select="artpgrg"/></span></span>
                        </div>
                        
                        <xsl:apply-templates mode="metadata" select="arttitle"/>
                        <xsl:apply-templates mode="metadata" select="artsub"/>
                        <xsl:apply-templates mode="metadata" select="artauth"/>
                        <xsl:apply-templates mode="metadata" select="artkwds"/>
                        
                        <!--<xsl:apply-templates/>-->
                    </div>
                </xsl:for-each>
                <p class="title"><xsl:value-of select = "//p[@class='arttitle']"/><xsl:value-of select = "//arttitle"/></p>
                <p class="title_author">
                    <xsl:value-of select = "//p[@class='artauth']"/>
                    <xsl:for-each select="//artauth/aut">
                        <xsl:apply-templates select="."/>
                    </xsl:for-each>
                </p>
                <p class="body"><xsl:value-of select = "//p[@class='abs']"/><xsl:value-of select = "//abs"/>
                </p>
            </body> 
        </html> 
    </xsl:template>
    <xsl:template match="artvol" mode="metadata">
        <xsl:call-template name="metadata-labeled-entry">
            <xsl:with-param name="label">Artvol</xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    
    <xsl:template match="artyear" mode="metadata">
        <xsl:call-template name="metadata-labeled-entry">
            <xsl:with-param name="label">Artyear</xsl:with-param>
        </xsl:call-template>
    </xsl:template>
    
</xsl:stylesheet>