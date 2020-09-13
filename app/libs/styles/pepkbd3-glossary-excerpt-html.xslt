<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">  
  <xsl:output method="xml" indent="yes"/>  
  
  <xsl:template match="node() | @*">  
    <xsl:copy>  
      <xsl:apply-templates select="node() | @*" />  
    </xsl:copy>  
  </xsl:template>  
  
  <xsl:template match="//p2">
  </xsl:template>
  
  <xsl:template match="//defrest">
  </xsl:template>

  <xsl:template match="//bib">
  </xsl:template>
 
  <xsl:template match="//impx">
    <xsl:value-of select="."/>
  </xsl:template>

  <xsl:template match="//p[position()!=1]">
  </xsl:template>
  
  <xsl:template match="//p[position()=1]">
    <p>
      <xsl:value-of select="."/>
    </p>
    <div>
      <p>
        This is an excerpt from the glossary.  The full-text is available to PEP subscribers.
      </p>
    </div>
  </xsl:template>
  
  <xsl:template match="//dictentrygrp">
    <div class="dictentrygrp">
      <xsl:if test="@id"> 
        <xsl:attribute name="id">
          <xsl:value-of select="@id"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </div>    
  </xsl:template>

  <xsl:template match="//dictentrygrp/term">
    <div class="dictentrygrp-term" >
      <xsl:if test="@lang"> 
        <xsl:attribute name="lang">
          <xsl:value-of select="@lang"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </div>    
  </xsl:template>

  <xsl:template match="//dictalso/term">
    <div class="dictentrygrp-dictalso-term smallcaps" >
      <xsl:if test="@lang"> 
        <xsl:attribute name="lang">
        <xsl:value-of select="@lang"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </div>    
  </xsl:template>
  
  <xsl:template match="//dictalso">
    <div class="dictentrygrp-dictalso">
      <xsl:apply-templates/>
    </div>    
  </xsl:template>

  <xsl:template match="//src">
    <div class="dictentry-src">
      <xsl:if test="@id"> 
        <xsl:attribute name="id">
          <xsl:value-of select="@id"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="//def">
    <div class="def-def body">
      <xsl:if test="@name"> 
        <xsl:attribute name="name">
          <xsl:value-of select="@name"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@type"> 
        <xsl:attribute name="type">
          <xsl:value-of select="@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <xsl:template match="i">
    <i>
      <xsl:apply-templates/>
    </i>
  </xsl:template>
  
  <xsl:template match="b">
    <b>
      <xsl:apply-templates/>
    </b>
  </xsl:template>

  <xsl:template match="//dictentry">
    <div class="dictentry">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  
  
</xsl:stylesheet>
