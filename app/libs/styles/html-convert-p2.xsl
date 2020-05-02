<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:xlink="http://www.w3.org/1999/xlink" 
    xmlns:mml="http://www.w3.org/1998/Math/MathML"
    exclude-result-prefixes="xlink mml">

    <xsl:template name="assign-lang">
        <xsl:choose>
            <xsl:when test="@lang">
                <xsl:attribute name="lang">
                    <xsl:value-of select="@lang"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="assign-class">
        <xsl:choose>
            <xsl:when test="@class">
                <xsl:attribute name="class">
                    <xsl:value-of select="@class"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="assign-id">
        <xsl:choose>
            <xsl:when test="@id">
                <xsl:attribute name="id">
                    <xsl:value-of select="@id"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
    <!--    Root template    -->
    <xsl:template match="/">
        <html>
            <!-- HTML header -->
            <!-- <xsl:call-template name="make-html-header"/>-->
            <xsl:apply-templates/>
        </html>
    </xsl:template>
    
    <xsl:template match="body">
        <body>
            <div class="pepkbd3">
                <xsl:for-each select="//p[@class='pb pagebreak']">
                    <div class="page">
                        <xsl:copy>
                            <xsl:for-each select="//*/*[preceding-sibling::p[@class='pb pagebreak'] and not (p[2])]">
                                <xsl:copy>
                                    <xsl:call-template name="assign-class"/>
                                    <xsl:call-template name="assign-id"/>
                                    <xsl:apply-templates/>
                                </xsl:copy>
                            </xsl:for-each>
<!--                        <xsl:copy-of select="//*/*[preceding-sibling::p[@class='pb'] and not (preceding-sibling::p[@class='pb pagebreak'])]">
--><!--                            <xsl:select="//*/*[preceding-sibling::p[@class='pb'] and not (preceding-sibling::p[@class='pb pagebreak'])]">-->
                        <!--</xsl:copy-of>-->
                        </xsl:copy>
                    </div>
                </xsl:for-each>    
            </div>
        </body>
    </xsl:template>

    <xsl:template match="p">
            <div class="para">
                <xsl:copy>
                    <xsl:call-template name="assign-class"/>
                    <xsl:call-template name="assign-id"/>
                    <xsl:apply-templates/>
                </xsl:copy>
            </div>
    </xsl:template>

<!--    <xsl:template match="div[@id='d0e1-front']">
        <div id="d0e1-front" class="front">
            <xsl:copy>
                <xsl:apply-templates/>
            </xsl:copy>
        </div>
    </xsl:template>
-->    
    <xsl:template match="div">
        <xsl:copy>
            <xsl:call-template name="assign-class"/>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>