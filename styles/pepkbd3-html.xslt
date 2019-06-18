<?xml version="1.0"?>
<!-- ============================================================= -->
<!--  MODULE:    HTML Preview of PEP-Web KBD3 instances            -->
<!--     BASED-ON:  HTML Preview of NISO JATS Publishing 1.0 XML   -->
<!--  DATE:      April 24, 2019                                    -->
<!--                                                               -->
<!-- ============================================================= -->
<!--
    The design of the conversion from PEP KBD3 to HTML is to use class for 
    the tag name, in either a div, p, or span element, depending on how we 
    whether it's a block element, a char element, or a division.  
    
    The attributes are placed in HTML5 attributes, named data-x where x is the 
    original attribute name.  

    - at least for this first pass! - 2019-04-24
    - this is by no means a complete conversion of the 
       whole DTD, just sampling as a quick test.
    - the class tagging is just temporary to keep track of what I add
    TBD:
    - I've yet to remove the irrelevant JATS rules
    - I haven't implemented or even checked on many structures like tables, figures, footnotes ... 
    - Bib processing is basically per JATs and not what we'd want (e.g., not sure why they do it as a table)
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML"
  exclude-result-prefixes="xlink mml">

  <!-- ============================================================= -->
  <!--  OASIS table handling                                         -->
  <!-- ============================================================= -->

  <!-- Uncomment this call only for OASIS table handling.
       NOTE: works only with XSLT 2.0 processors! -->
  <!--<xsl:import href="../oasis-tables/oasis-table-html.xsl"/>-->

  <!-- $p:hard-styles should be true() if CSS styles should be presented locally on table elements. -->
  <!-- Alternative, call template 'p:table-css' into the HTML header to provide CSS for 'soft'
       (i.e. class-driven) styling for table cells. -->
  <!--<xsl:param name="p:hard-styles" select="true()" xmlns:p="http://www.wendellpiez.com/oasis-tables/util"/>-->



  <!-- Or, that transformation may be run as a pre- or post-process. -->

  <!-- If they are run as a post-process, here is a template to prevent them from being stripped by this stylesheet. -->
  <!--<xsl:template match="oasis:*" xmlns:oasis="http://www.niso.org/standards/z39-96/ns/oasis-exchange/table">
    <xsl:copy><!-\- use copy-namespaces='no' under XSLT 2.0 -\->
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>-->

  <xsl:output doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
    doctype-system="http://www.w3.org/TR/html4/loose.dtd" encoding="UTF-8"/>

  <xsl:strip-space elements="*"/>

  <!-- Space is preserved in all elements allowing #PCDATA -->
  <xsl:preserve-space
    elements="body 
              group
              p
              h1 h2 h3 h4 h5
              "/>

  <xsl:param name="transform" select="'pepkbd3-html.xsl'"/>

  <xsl:param name="css" select="'pep-html-preview.css'"/>
  <xsl:param name="css2" select="'pep.css'"/>
  <xsl:param name="css3" select="'pepepub.css'"/>
  <xsl:param name="report-warnings" select="'no'"/>

  <xsl:variable name="verbose" select="$report-warnings = 'yes'"/>

  <!-- Keys -->

  <!-- To reduce dependency on a DTD for processing, we declare
       a key to use instead of the id() function. -->
  <xsl:key name="element-by-id" match="*[@id]" use="@id"/>

  <!-- Enabling retrieval of cross-references to objects -->
  <xsl:key name="xref-by-rid" match="xref" use="@rid"/>

  <!-- ============================================================= -->
  <!--  ROOT TEMPLATE - HANDLES HTML FRAMEWORK                       -->
  <!-- ============================================================= -->

  <xsl:template match="/">
    <html class="pepkbd3html u20190613">
      <!-- HTML header -->
      <xsl:call-template name="make-html-header"/>
      <xsl:apply-templates/>
      <div id="putciteashere"></div>
      
    </html>
  </xsl:template>

  <xsl:template name="make-html-header">
    <head>
      <title class="head title">
          <xsl:value-of select="pepkbd3/artinfo/arttitle"/>
      </title>
      <link rel="stylesheet" type="text/css" href="{$css}">
      </link>
      <!-- When importing jats-oasis-html.xsl, we can call a template to insert CSS for our tables. -->
      <!--<xsl:call-template name="p:table-css" xmlns:p="http://www.wendellpiez.com/oasis-tables/util"/>-->
    </head>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  TOP LEVEL                                                    -->
  <!-- ============================================================= -->

  <xsl:template match="pepkbd3">
    <div class="pepkbd3" lang="{@lang}">
      <xsl:call-template name="make-article"/>
    </div>
  </xsl:template>
  
  <xsl:template match="sub-article | response">
    <hr class="part-rule"/>
    <xsl:call-template name="make-article"/>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  "make-article" for the document architecture                 -->
  <!-- ============================================================= -->

  <xsl:template name="make-article">
    <!-- Generates a series of (flattened) divs for contents of any
	       article, sub-article or response -->
    <!-- variable for the pep host url -->
    <xsl:variable name="baseurl">www.pep-web.org</xsl:variable>
    <xsl:variable name="document-id">
      <xsl:apply-templates select="//artinfo/@id" mode="id"/>
    </xsl:variable>
    <xsl:variable name="journal-code">
      <xsl:apply-templates select="//artinfo/@j" mode="id"/>
    </xsl:variable>
    <xsl:variable name="authors">
      <xsl:apply-templates select="//aut/@authindexid" mode="id"/>
    </xsl:variable>
        
    <!-- variable to be used in div id's to keep them unique -->
    <xsl:variable name="this-article">
      <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>

    <div id="{$this-article}-front" class="front">
      <xsl:apply-templates select="front | front-stub"/>
      <p class="banner"><a name="{$document-id}" id="{$document-id}"></a>
        <a href="search.php?journal=ijp"><img src="images/banner{$journal-code}logo.gif" alt="International Journal of Psycho-Analysis" /></a>
      </p>
 
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
    </div>

    <!-- abs -->
    <xsl:for-each select="abs">
      <div id="{$this-article}-abs" class="abs abstract">
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>
    
    <!-- body -->
    <xsl:for-each select="body">
      <div id="{$this-article}-body" class="body">
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>

    <!-- body -->
    <xsl:for-each select="bib">
      <div id="{$this-article}-bib" class="biblio">
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>

    <!-- grp (***)  -->
    <xsl:for-each select="body/grp">
      <div id="grp-{$this-article}-{@id}" class="grp sec" data-name="{@name}">
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>

    <xsl:if test="back | $loose-footnotes">
      <!-- $loose-footnotes is defined below as any footnotes outside
           front matter or fn-group -->
      <div id="{$this-article}-back" class="back">
        <xsl:call-template name="make-back"/>
      </div>
    </xsl:if>

    <xsl:for-each select="floats-group | floats-wrap">
      <!-- floats-wrap is from 2.3 -->
      <div id="{$this-article}-floats" class="back">
        <xsl:call-template name="main-title">
          <xsl:with-param name="contents">
            <span class="generated">Floating objects</span>
          </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>

    <!-- sub-article or response (recursively calls
		     this template) -->
    <xsl:apply-templates select="sub-article | response"/>
  </xsl:template>

  <xsl:template match="artinfo">
    <!-- First Table: journal and article metadata -->
    <div class="metadata two-column table">
      <div class="row">
        <!-- Cell 1: journal information -->
        <!-- Cell 2: Article information -->
        <xsl:for-each select="artinfo">
            <h4 class="generated">
              <xsl:text>Article Information</xsl:text>
            </h4>
        </xsl:for-each>
      </div>
    </div>

    <hr class="part-rule"/>

    <!-- change context to front/article-meta (again) -->
    <xsl:for-each select="article-meta | self::front-stub">
      <div class="metadata centered">
        <xsl:apply-templates mode="metadata" select="title-group"/>
      </div>
      <!-- contrib-group, aff, aff-alternatives, author-notes -->
      <xsl:apply-templates mode="metadata" select="contrib-group"/>
      <!-- back in article-meta or front-stub context -->
      <xsl:if test="aff | aff-alternatives | author-notes">
        <div class="metadata two-column table">
          <div class="row">
            <div class="cell empty"/>
            <div class="cell">
              <div class="metadata-group">
                <xsl:apply-templates mode="metadata" select="aff | aff-alternatives | author-notes"
                />
              </div>
            </div>
          </div>
        </div>
      </xsl:if>

      <!-- abstract(s) -->
      <xsl:if test="abstract | trans-abstract">
        <!-- rule separates title+authors from abstract(s) -->
        <hr class="section-rule"/>

        <xsl:for-each select="abstract | trans-abstract">
          <!-- title in left column, content (paras, secs) in right -->
          <div class="metadata two-column table">
            <div class="row">
              <div class="cell" style="text-align: right">
                <h4 class="callout-title">
                  <xsl:apply-templates select="title/node()"/>
                  <xsl:if test="not(normalize-space(string(title)))">
                    <span class="generated">
                      <xsl:if test="self::trans-abstract">Translated </xsl:if>
                      <xsl:text>Abstract</xsl:text>
                    </span>
                  </xsl:if>
                </h4>
              </div>
              <div class="cell">
                <xsl:apply-templates select="*[not(self::title)]"/>
              </div>
            </div>
          </div>
        </xsl:for-each>
        <!-- end of abstract or trans-abstract -->
      </xsl:if>
      <!-- end of dealing with abstracts -->
    </xsl:for-each>
    <xsl:for-each select="notes">
      <div class="metadata">
        <xsl:apply-templates mode="metadata" select="."/>
      </div>
    </xsl:for-each>
    <hr class="part-rule"/>

    <!-- end of big front-matter pull -->
  </xsl:template>


  <!-- ============================================================= -->
  <!--  METADATA PROCESSING                                          -->
  <!-- ============================================================= -->

  <!--  Includes mode "metadata" for front matter, along with 
      "metadata-inline" for metadata elements collapsed into 
      inline sequences, plus associated named templates            -->

  <!-- WAS journal-meta content:
       journal-id+, journal-title-group*, issn+, isbn*, publisher?,
       notes? -->
  <!-- (journal-id+, journal-title-group*, (contrib-group | aff | aff-alternatives)*,
       issn+, issn-l?, isbn*, publisher?, notes*, self-uri*) -->
 
  <!-- journal-title-group content:
       (journal-title*, journal-subtitle*, trans-title-group*,
       abbrev-journal-title*) -->


  <!-- article-meta content:
    (article-id*, article-categories?, title-group,
     (contrib-group | aff)*, author-notes?, pub-date+, volume?,
     volume-id*, volume-series?, issue?, issue-id*, 
     issue-title*, issue-sponsor*, issue-part?, isbn*, 
     supplement?, ((fpage, lpage?, page-range?) | elocation-id)?, 
     (email | ext-link | uri | product | supplementary-material)*, 
     history?, permissions?, self-uri*, related-article*,
     abstract*, trans-abstract*, 
     kwd-group*, funding-group*, conference*, counts?, 
     custom-meta-group?) -->

  <!-- In order of appearance... -->


  <xsl:template match="email" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Email</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="."/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="url" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">URL</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="."/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="grp" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">URL</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="."/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="self-uri" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Self URI</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <a href="{@xlink:href}">
          <xsl:choose>
            <xsl:when test="normalize-space(string(.))">
              <xsl:apply-templates/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="@xlink:href"/>
            </xsl:otherwise>
          </xsl:choose>
        </a>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="product" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Product Information</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:choose>
          <xsl:when test="normalize-space(string(@xlink:href))">
            <a>
              <xsl:call-template name="assign-href"/>
              <xsl:apply-templates/>
            </a>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="permissions" mode="metadata">
    <xsl:apply-templates select="copyright-statement" mode="metadata"/>
    <xsl:if test="copyright-year | copyright-holder">
      <xsl:call-template name="metadata-labeled-entry">
        <xsl:with-param name="label">Copyright</xsl:with-param>
        <xsl:with-param name="contents">
          <xsl:for-each select="copyright-year | copyright-holder">
            <xsl:apply-templates/>
            <xsl:if test="not(position() = last())">, </xsl:if>
          </xsl:for-each>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="license" mode="metadata"/>
  </xsl:template>


  <xsl:template match="copyright-statement" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Copyright statement</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="copyright-year" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Copyright</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="license" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">
        <xsl:text>License</xsl:text>
        <xsl:if test="@license-type | @xlink:href">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="@license-type"/>
            <xsl:if test="@xlink:href">
              <xsl:if test="@license-type">, </xsl:if>
              <a>
                <xsl:call-template name="assign-href"/>
                <xsl:value-of select="@xlink:href"/>
              </a>
            </xsl:if>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="volume-info">
    <!-- handles volume?, volume-id*, volume-series? -->
    <xsl:if test="volume | volume-id | volume-series">
      <xsl:choose>
        <xsl:when test="not(volume-id[2]) or not(volume)">
          <!-- if there are no multiple volume-id, or no volume, we make one line only -->
          <xsl:call-template name="metadata-labeled-entry">
            <xsl:with-param name="label">Volume</xsl:with-param>
            <xsl:with-param name="contents">
              <xsl:apply-templates select="volume | volume-series" mode="metadata-inline"/>
              <xsl:apply-templates select="volume-id" mode="metadata-inline"/>
            </xsl:with-param>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="volume | volume-id | volume-series" mode="metadata"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>


  <xsl:template match="volume | issue" mode="metadata-inline">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="volume-id | issue-id" mode="metadata-inline">
    <span class="generated">
      <xsl:text> (</xsl:text>
      <xsl:for-each select="@pub-id-type">
        <span class="data">
          <xsl:value-of select="."/>
        </span>
        <xsl:text> </xsl:text>
      </xsl:for-each>
      <xsl:text>ID: </xsl:text>
    </span>
    <xsl:apply-templates/>
    <span class="generated">)</span>
  </xsl:template>


  <xsl:template match="volume-series" mode="metadata-inline">
    <xsl:if test="preceding-sibling::volume">
      <span class="generated">,</span>
    </xsl:if>
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
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
  
  <xsl:template match="artbkinfo" mode="metadata">
    <div class="metadata-entry artbookinfo">
      <xsl:if test="@extract">
        <xsl:attribute name="data-extract">
          <xsl:value-of select="@extract"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@prev">
        <xsl:attribute name="data-prev">
          <xsl:value-of select="@prev"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@next">
        <xsl:attribute name="data-next">
          <xsl:value-of select="@next"/>
        </xsl:attribute>
      </xsl:if>
    </div>
  </xsl:template>

  <xsl:template match="artiss" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Artiss</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="artpgrg" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Artpgrg</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="arttitle" mode="metadata">
    <p class="arttitle">
      <xsl:value-of select="."/>
    </p>
  </xsl:template>

  <xsl:template match="artsub" mode="metadata">
    <p class="artsub">
      <xsl:value-of select="."/>
    </p>
  </xsl:template>

  <xsl:template match="artkwds" mode="metadata">
<!--    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Artkwds</xsl:with-param>
    </xsl:call-template>
-->    <div class="artkwds">
      <xsl:apply-templates mode="metadata" select="impx"/>
    </div>
  </xsl:template>
  
  <xsl:template match="impx" mode="metadata">
    <xsl:text>&#10;</xsl:text> <!-- newline character -->
    <xsl:choose>
      <xsl:when test="@rx">
        <span class="impx" data-type="{@type}" data-rx="{@rx}" data-grpname="{@grpname}">
          <xsl:value-of select="."/>
        </span>
      </xsl:when>
      <xsl:otherwise>
        <span class="impx" data-type="{@type}">
          <xsl:value-of select="."/>
        </span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="artauth" mode="metadata">
    <div class="artauth">
      <div class="authorwrapper">
        <xsl:apply-templates mode="metadata" select="aut"/>
      </div>
      <xsl:apply-templates mode="metadata" select="autaff"/>
    </div>
  </xsl:template>

  <xsl:template match="autaff" mode="metadata">
    <div class="autaff" data-affid="{@affid}">
      <xsl:apply-templates mode="metadata" select="addr"/>
    </div>
  </xsl:template>
  
  <!--PEPKBD3 Author Information-->
  <xsl:template match="aut" mode="metadata">
    <div class="aut" data-listed="{@listed}" data-authindexid="{@authindexid}" data-role="{@role}" data-alias="{@alias}" data-asis="{@asis}">
      <xsl:apply-templates mode="metadata" select="nfirst"/>
      <xsl:apply-templates mode="metadata" select="nlast"/>
      <xsl:apply-templates mode="metadata" select="ndeg"/>
      <xsl:apply-templates mode="metadata" select="nbio"/>
    </div>  
  </xsl:template>


  <xsl:template match="nfirst" mode="metadata">
    <xsl:text>&#10;</xsl:text> <!-- newline character -->
    <span class="nfirst" data-type="{@type}" data-initials="{@initials}">
      <xsl:value-of select="."/>
    </span>
    <!--<xsl:text> </xsl:text>--> <!-- space character -->
  </xsl:template>


  <xsl:template match="nlast" mode="metadata">
    <span class="nlast">
      <xsl:value-of select="."/>
    </span>
    
  </xsl:template>


  <xsl:template match="ndeg" mode="metadata">
    <span class="ndeg" data-dgr="{@dgr}" data-other="{@other}">
      <xsl:value-of select="."/>
    </span>
    <xsl:text> </xsl:text> <!-- space character -->
  </xsl:template>


  <xsl:template match="ln" mode="metadata">
    <p class="ln">
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  

  <xsl:template match="addr" mode="metadata">
    <div class="addr">
      <xsl:apply-templates mode="metadata" select="ln"/>
    </div>
  </xsl:template>

  <xsl:template match="nbio" mode="metadata">
    <div class="nbio">
      <xsl:value-of select="."/>
      <xsl:apply-templates mode="metadata" select="webx"/>
    </div>
  </xsl:template>
  

  <xsl:template match="webx" mode="metadata">
    <span class="webx" data-type="{@type}" data-url="{@url}">
      <xsl:value-of select="."/>
    </span>
  </xsl:template>
  
  
  <!--  <xsl:template match="p" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">p</xsl:with-param>
    </xsl:call-template>
  </xsl:template>-->

  <xsl:template match="volume-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Volume ID</xsl:text>
        <xsl:for-each select="@pub-id-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="volume-series" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Series</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="issue-info">
    <!-- handles issue?, issue-id*, issue-title*, issue-sponsor*, issue-part?, supplement? -->
    <xsl:variable name="issue-info"
      select="
        issue | issue-id | issue-title |
        issue-sponsor | issue-part"/>
    <xsl:choose>
      <xsl:when
        test="$issue-info and not(issue-id[2] | issue-title[2] | issue-sponsor | issue-part)">
        <!-- if there are only one issue, issue-id and issue-title and nothing else, we make one line only -->
        <xsl:call-template name="metadata-labeled-entry">
          <xsl:with-param name="label">Issue</xsl:with-param>
          <xsl:with-param name="contents">
            <xsl:apply-templates select="issue | issue-title" mode="metadata-inline"/>
            <xsl:apply-templates select="issue-id" mode="metadata-inline"/>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="$issue-info" mode="metadata"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="issue-title" mode="metadata-inline">
    <span class="generated">
      <xsl:if test="preceding-sibling::issue">,</xsl:if>
    </span>
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="issue" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Issue ID</xsl:text>
        <xsl:for-each select="@pub-id-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue title</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-sponsor" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue sponsor</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-part" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue part</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="page-info">
    <!-- handles (fpage, lpage?, page-range?) -->
    <xsl:if test="fpage | lpage | page-range">
      <xsl:call-template name="metadata-labeled-entry">
        <xsl:with-param name="label">
          <xsl:text>Page</xsl:text>
          <xsl:if
            test="
              normalize-space(string(lpage[not(. = ../fpage)]))
              or normalize-space(string(page-range))">
            <!-- we have multiple pages if lpage exists and is not equal fpage,
               or if we have a page-range -->
            <xsl:text>s</xsl:text>
          </xsl:if>
        </xsl:with-param>
        <xsl:with-param name="contents">
          <xsl:value-of select="fpage"/>
          <xsl:if test="normalize-space(string(lpage[not(. = ../fpage)]))">
            <xsl:text>-</xsl:text>
            <xsl:value-of select="lpage"/>
          </xsl:if>
          <xsl:for-each select="page-range">
            <xsl:text> (pp. </xsl:text>
            <xsl:value-of select="."/>
            <xsl:text>)</xsl:text>
          </xsl:for-each>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>


  <xsl:template match="elocation-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Electronic Location Identifier</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <!-- isbn is already matched in mode 'metadata' above -->

  <xsl:template match="supplement" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Supplement Info</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="related-article | related-object" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Related </xsl:text>
        <xsl:choose>
          <xsl:when test="self::related-object">object</xsl:when>
          <xsl:otherwise>article</xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="@related-article-type | @object-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="translate(., '-', ' ')"/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:choose>
          <xsl:when test="normalize-space(string(@xlink:href))">
            <a>
              <xsl:call-template name="assign-href"/>
              <xsl:apply-templates/>
            </a>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conference" mode="metadata">
    <!-- content model:
      (conf-date, 
       (conf-name | conf-acronym)+, 
       conf-num?, conf-loc?, conf-sponsor*, conf-theme?) -->
    <xsl:choose>
      <xsl:when
        test="
          not(conf-name[2] | conf-acronym[2] | conf-sponsor |
          conf-theme)">
        <!-- if there is no second name or acronym, and no sponsor
             or theme, we make one line only -->
        <xsl:call-template name="metadata-labeled-entry">
          <xsl:with-param name="label">Conference</xsl:with-param>
          <xsl:with-param name="contents">
            <xsl:apply-templates select="conf-acronym | conf-name" mode="metadata-inline"/>
            <xsl:apply-templates select="conf-num" mode="metadata-inline"/>
            <xsl:if test="conf-date | conf-loc">
              <span class="generated"> (</span>
              <xsl:for-each select="conf-date | conf-loc">
                <xsl:if test="position() = 2">, </xsl:if>
                <xsl:apply-templates select="." mode="metadata-inline"/>
              </xsl:for-each>
              <span class="generated">)</span>
            </xsl:if>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="metadata"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="conf-date" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference date</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-name" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-acronym" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-num" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference number</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-loc" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference location</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-sponsor" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference sponsor</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-theme" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference theme</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-name | conf-acronym" mode="metadata-inline">
    <!-- we only hit this template if there is at most one of each -->
    <xsl:variable name="following"
      select="preceding-sibling::conf-name | preceding-sibling::conf-acronym"/>
    <!-- if we come after the other, we go in parentheses -->
    <xsl:if test="$following">
      <span class="generated"> (</span>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:if test="$following">
      <span class="generated">)</span>
    </xsl:if>
  </xsl:template>


  <xsl:template match="conf-num" mode="metadata-inline">
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="conf-date | conf-loc" mode="metadata-inline">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="article-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:choose>
          <xsl:when test="@pub-id-type = 'art-access-id'">Accession ID</xsl:when>
          <xsl:when test="@pub-id-type = 'coden'">Coden</xsl:when>
          <xsl:when test="@pub-id-type = 'doi'">DOI</xsl:when>
          <xsl:when test="@pub-id-type = 'manuscript'">Manuscript ID</xsl:when>
          <xsl:when test="@pub-id-type = 'medline'">Medline ID</xsl:when>
          <xsl:when test="@pub-id-type = 'pii'">Publisher Item ID</xsl:when>
          <xsl:when test="@pub-id-type = 'pmid'">PubMed ID</xsl:when>
          <xsl:when test="@pub-id-type = 'publisher-id'">Publisher ID</xsl:when>
          <xsl:when test="@pub-id-type = 'sici'">Serial Item and Contribution ID</xsl:when>
          <xsl:when test="@pub-id-type = 'doaj'">DOAJ ID</xsl:when>
          <xsl:when test="@pub-id-type = 'arXiv'">arXiv.org ID</xsl:when>
          <xsl:otherwise>
            <xsl:text>Article Id</xsl:text>
            <xsl:for-each select="@pub-id-type">
              <xsl:text> (</xsl:text>
              <span class="data">
                <xsl:value-of select="."/>
              </span>
              <xsl:text>)</xsl:text>
            </xsl:for-each>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="contract-num" mode="metadata">
    <!-- only in 2.3 -->
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Contract</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="contract-sponsor" mode="metadata">
    <!-- only in 2.3 -->
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Contract Sponsor</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="grant-num" mode="metadata">
    <!-- only in 2.3 -->
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Grant Number</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="grant-sponsor" mode="metadata">
    <!-- only in 2.3 -->
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Grant Sponsor</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="award-group" mode="metadata">
    <!-- includes (funding-source*, award-id*, principal-award-recipient*, principal-investigator*) -->
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="funding-source" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Funded by</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="award-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Award ID</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="principal-award-recipient" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Award Recipient</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="principal-investigator" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Principal Investigator</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="funding-statement" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Funding</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="open-access" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Open Access</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="title-group" mode="metadata">
    <!-- content model:
    article-title, subtitle*, trans-title-group*, alt-title*, fn-group? -->
    <!-- trans-title and trans-subtitle included for 2.3 -->
    <xsl:apply-templates
      select="
        article-title | subtitle | trans-title-group |
        trans-title | trans-subtitle"
      mode="metadata"/>
    <xsl:if test="alt-title | fn-group">
      <div class="document-title-notes metadata-group">
        <xsl:apply-templates select="alt-title | fn-group" mode="metadata"/>
      </div>
    </xsl:if>
  </xsl:template>


  <xsl:template match="title-group/article-title" mode="metadata">
    <h1 class="document-title">
      <xsl:apply-templates/>
      <xsl:if test="../subtitle">:</xsl:if>
    </h1>
  </xsl:template>


  <xsl:template match="title-group/subtitle | trans-title-group/subtitle" mode="metadata">
    <h2 class="document-title">
      <xsl:apply-templates/>
    </h2>
  </xsl:template>


  <xsl:template match="title-group/trans-title-group" mode="metadata">
    <!-- content model: (trans-title, trans-subtitle*) -->
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>



  <xsl:template match="title-group/alt-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Alternative title</xsl:text>
        <xsl:for-each select="@alt-title-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="title-group/fn-group" mode="metadata">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template mode="metadata" match="journal-meta/contrib-group">
    <xsl:for-each select="contrib">
      <xsl:variable name="contrib-identification">
        <xsl:call-template name="contrib-identify"/>
      </xsl:variable>
      <!-- placing the div only if it has content -->
      <!-- the extra call to string() makes it type-safe in a type-aware
           XSLT 2.0 engine -->
      <xsl:if test="normalize-space(string($contrib-identification))">
        <xsl:copy-of select="$contrib-identification"/>
      </xsl:if>
      <xsl:variable name="contrib-info">
        <xsl:call-template name="contrib-info"/>
      </xsl:variable>
      <!-- placing the div only if it has content -->
      <xsl:if test="normalize-space(string($contrib-info))">
        <xsl:copy-of select="$contrib-info"/>
      </xsl:if>
    </xsl:for-each>

    <xsl:if test="*[not(self::contrib | self::xref)]">

      <xsl:apply-templates mode="metadata" select="*[not(self::contrib | self::xref)]"/>

    </xsl:if>
  </xsl:template>

  <xsl:template mode="metadata" match="article-meta/contrib-group">
    <!-- content model of contrib-group:
        (contrib+, 
        (address | aff | author-comment | bio | email |
        ext-link | on-behalf-of | role | uri | xref)*) -->
    <!-- each contrib makes a row: name at left, details at right -->
    <xsl:for-each select="contrib">
      <!--  content model of contrib:
          ((contrib-id)*,
           (anonymous | collab | collab-alternatives | name | name-alternatives)*,
           (degrees)*,
           (address | aff | aff-alternatives | author-comment | bio | email |
            ext-link | on-behalf-of | role | uri | xref)*)       -->
      <div class="metadata two-column table">
        <div class="row">
          <div class="cell" style="text-align: right">
            <xsl:call-template name="contrib-identify">
              <!-- handles (contrib-id)*,
                (anonymous | collab | collab-alternatives |
                 name | name-alternatives | degrees | xref) -->
            </xsl:call-template>
          </div>
          <div class="cell">
            <xsl:call-template name="contrib-info">
              <!-- handles
                   (address | aff | author-comment | bio | email |
                    ext-link | on-behalf-of | role | uri) -->
            </xsl:call-template>
          </div>
        </div>
      </div>
    </xsl:for-each>
    <!-- end of contrib -->
    <xsl:variable name="misc-contrib-data" select="*[not(self::contrib | self::xref)]"/>
    <xsl:if test="$misc-contrib-data">
      <div class="metadata two-column table">
        <div class="row">
          <div class="cell">&#160;</div>
          <div class="cell">
            <div class="metadata-group">
              <xsl:apply-templates mode="metadata" select="$misc-contrib-data"/>
            </div>
          </div>
        </div>
      </div>
    </xsl:if>
  </xsl:template>


  <xsl:template name="contrib-identify">
    <!-- Placed in a left-hand pane  -->
    <!--handles
    (anonymous | collab | collab-alternatives |
    name | name-alternatives | degrees | xref)
    and @equal-contrib -->
    <div class="metadata-group">
      <xsl:for-each
        select="
          anonymous |
          collab | collab-alternatives/* | name | name-alternatives/*">
        <xsl:call-template name="metadata-entry">
          <xsl:with-param name="contents">
            <xsl:if test="position() = 1">
              <!-- a named anchor for the contrib goes with its
              first member -->
              <xsl:call-template name="named-anchor"/>
              <!-- so do any contrib-ids -->
              <xsl:apply-templates mode="metadata-inline" select="../contrib-id"/>
            </xsl:if>
            <xsl:apply-templates select="." mode="metadata-inline"/>
            <xsl:if test="position() = last()">
              <xsl:apply-templates mode="metadata-inline" select="degrees | xref"/>
              <!-- xrefs in the parent contrib-group go with the last member
              of *each* contrib in the group -->
              <xsl:apply-templates mode="metadata-inline" select="following-sibling::xref"/>
            </xsl:if>

          </xsl:with-param>
        </xsl:call-template>
      </xsl:for-each>
      <xsl:if test="@equal-contrib = 'yes'">
        <xsl:call-template name="metadata-entry">
          <xsl:with-param name="contents">
            <span class="generated">(Equal contributor)</span>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:if>
    </div>
  </xsl:template>


  <xsl:template match="anonymous" mode="metadata-inline">
    <xsl:text>Anonymous</xsl:text>
  </xsl:template>


  <xsl:template match="
      collab |
      collab-alternatives/*" mode="metadata-inline">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="
      contrib/name |
      contrib/name-alternatives/*"
    mode="metadata-inline">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <xsl:template match="degrees" mode="metadata-inline">
    <xsl:text>, </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="xref" mode="metadata-inline">
    <!-- These are not expected to appear in mixed content, so
      brackets are provided -->
    <span class="generated">[</span>
    <xsl:apply-templates select="."/>
    <span class="generated">]</span>
  </xsl:template>

  <xsl:template match="contrib-id" mode="metadata-inline">
    <span class="generated">[</span>
    <xsl:apply-templates select="."/>
    <span class="generated">] </span>
  </xsl:template>


  <xsl:template name="contrib-info">
    <!-- Placed in a right-hand pane -->
    <div class="metadata-group">
      <xsl:apply-templates mode="metadata"
        select="
          address | aff | author-comment | bio | email |
          ext-link | on-behalf-of | role | uri"
      />
    </div>
  </xsl:template>


  <xsl:template mode="metadata" match="address[not(addr-line) or not(*[2])]">
    <!-- when we have no addr-line or a single child, we generate
         a single unlabelled line -->
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:call-template name="address-line"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="address" mode="metadata">
    <!-- when we have an addr-line we generate an unlabelled block -->
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template mode="metadata" priority="2" match="address/*">
    <!-- being sure to override other templates for these
         element types -->
    <xsl:call-template name="metadata-entry"/>
  </xsl:template>


  <xsl:template match="aff" mode="metadata">
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="author-comment" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Comment</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="bio" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Bio</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="on-behalf-of" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">On behalf of</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="role" mode="metadata">
    <xsl:call-template name="metadata-entry"/>
  </xsl:template>


  <xsl:template match="author-notes" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Author notes</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="author-notes/corresp" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:call-template name="named-anchor"/>
        <xsl:text>Correspondence to</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="author-notes/fn | author-notes/p" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:apply-templates select="@fn-type"/>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="kwd-group" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">
        <xsl:apply-templates select="title | label" mode="metadata-inline"/>
        <xsl:if test="not(title | label)">Keywords</xsl:if>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="title" mode="metadata">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <xsl:template match="kwd" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Keyword</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template mode="metadata"
    match="
      count | fig-count | table-count | equation-count |
      ref-count | page-count | word-count">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:apply-templates select="." mode="metadata-label"/>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:value-of select="@count"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="count" mode="metadata-label">
    <xsl:text>Count</xsl:text>
    <xsl:for-each select="@count-type">
      <xsl:text> (</xsl:text>
      <span class="data">
        <xsl:value-of select="."/>
      </span>
      <xsl:text>)</xsl:text>
    </xsl:for-each>
  </xsl:template>


  <xsl:template match="fig-count" mode="metadata-label">Figures</xsl:template>


  <xsl:template match="table-count" mode="metadata-label">Tables</xsl:template>


  <xsl:template match="equation-count" mode="metadata-label">Equations</xsl:template>


  <xsl:template match="ref-count" mode="metadata-label">References</xsl:template>


  <xsl:template match="page-count" mode="metadata-label">Pages</xsl:template>


  <xsl:template match="word-count" mode="metadata-label">Words</xsl:template>


  <xsl:template mode="metadata" match="custom-meta-group | custom-meta-wrap">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Custom metadata</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="custom-meta" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <span class="data">
          <xsl:apply-templates select="meta-name" mode="metadata-inline"/>
        </span>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="meta-value" mode="metadata-inline"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="meta-name | meta-value" mode="metadata-inline">
    <xsl:apply-templates/>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  REGULAR (DEFAULT) MODE                                       -->
  <!-- ============================================================= -->


  <xsl:template match="sec">
    <div class="section">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="title"/>
      <xsl:apply-templates select="sec-meta"/>
      <xsl:apply-templates mode="drop-title"/>
    </div>
  </xsl:template>

  <xsl:template match="caption">
    <p class="caption" data-nbr="{@mbr}">
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  

  <xsl:template match="*" mode="drop-title">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <xsl:template match="title | sec-meta" mode="drop-title"/>


  <xsl:template match="app">
    <div class="section app">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


<!--  <xsl:template match="bib" name="ref-list">
    <div class="section bib">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates select="*[not(self::be | self::ref-list)]"/>
      <xsl:if test="be">
        <div class="ref-list table">
          <xsl:apply-templates select="be"/>
        </div>
      </xsl:if>
      <xsl:apply-templates select="ref-list"/>
    </div>
  </xsl:template>
-->

  <xsl:template match="sec-meta">
    <div class="section-metadata">
      <!-- includes contrib-group | permissions | kwd-group -->
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="sec-meta/contrib-group">
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="sec-meta/kwd-group">
    <!-- matches only if contrib-group has only contrib children -->
    <xsl:apply-templates select="." mode="metadata"/>
  </xsl:template>



  <!-- ============================================================= -->
  <!--  Titles                                                       -->
  <!-- ============================================================= -->

  <xsl:template name="main-title"
    match="
      abstract/title | body/*/title |
      back/title | back[not(title)]/*/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:if test="normalize-space(string($contents))">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h2 class="main-title">
        <xsl:copy-of select="$contents"/>
      </h2>
    </xsl:if>
  </xsl:template>


  <xsl:template name="section-title"
    match="
      abstract/*/title | body/*/*/title |
      back[title]/*/title | back[not(title)]/*/*/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:if test="normalize-space(string($contents))">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h3 class="section-title">
        <xsl:copy-of select="$contents"/>
      </h3>
    </xsl:if>
  </xsl:template>


  <xsl:template name="subsection-title"
    match="
      abstract/*/*/title | body/*/*/*/title |
      back[title]/*/*/title | back[not(title)]/*/*/*/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:if test="normalize-space(string($contents))">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h4 class="subsection-title">
        <xsl:copy-of select="$contents"/>
      </h4>
    </xsl:if>
  </xsl:template>


  <xsl:template name="block-title" priority="2"
    match="
      list/title | def-list/title | boxed-text/title |
      verse-group/title | glossary/title | gloss-group/title | kwd-group/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:if test="normalize-space(string($contents))">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h4 class="block-title">
        <xsl:copy-of select="$contents"/>
      </h4>
    </xsl:if>
  </xsl:template>


  <!-- default: any other titles found -->
  <xsl:template match="title">
    <xsl:if test="normalize-space(string(.))">
      <h3 class="title">
        <xsl:apply-templates/>
      </h3>
    </xsl:if>
  </xsl:template>


  <xsl:template match="subtitle">
    <xsl:if test="normalize-space(string(.))">
      <h5 class="subtitle">
        <xsl:apply-templates/>
      </h5>
    </xsl:if>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  Figures, lists and block-level objectS                       -->
  <!-- ============================================================= -->

  <!-- abs -->
  <xsl:template match="abs">
    <div id="abs" class="abs">
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="address">
    <xsl:choose>
      <!-- address appears as a sequence of inline elements if
           it has no addr-line and the parent may contain text -->
      <xsl:when
        test="
          not(addr-line) and
          (parent::collab | parent::p | parent::license-p |
          parent::named-content | parent::styled-content)">
        <xsl:call-template name="address-line"/>
      </xsl:when>
      <xsl:otherwise>
        <div class="address">
          <xsl:apply-templates/>
        </div>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template name="address-line">
    <!-- emits element children in a simple comma-delimited sequence -->
    <xsl:for-each select="*">
      <xsl:if test="position() &gt; 1">, </xsl:if>
      <xsl:apply-templates/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="address/*">
    <p class="address-line">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template
    match="
      array | disp-formula-group | fig-group |
      fn-group | license | long-desc | open-access | sig-block |
      table-wrap-foot | table-wrap-group">
    <div class="{local-name()}">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="attrib">
    <p class="attrib">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="h1">
    <h1>
      <xsl:call-template name="assign-id"/>
      <span class="heading">
        <xsl:call-template name="assign-id"/>
        <xsl:apply-templates/>
      </span>
    </h1>
  </xsl:template>

  <xsl:template match="h2">
    <h2>
      <xsl:call-template name="assign-id"/>
      <span class="heading">
        <xsl:call-template name="assign-id"/>
        <xsl:apply-templates/>
      </span>
    </h2>
  </xsl:template>

  <xsl:template match="disp-formula | statement">
    <div class="{local-name()} panel">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="glossary | gloss-group">
    <!-- gloss-group is from 2.3 -->
    <div class="glossary">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="label | title"/>
      <xsl:if test="not(normalize-space(string(title)))">
        <xsl:call-template name="block-title">
          <xsl:with-param name="contents">
            <span class="generated">Glossary</span>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:if>
      <xsl:apply-templates select="*[not(self::label | self::title)]"/>
    </div>
  </xsl:template>


  <xsl:template match="glossary/glossary | gloss-group/gloss-group">
    <!-- the same document shouldn't have both types -->
    <div class="glossary">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="graphic | inline-graphic">
    <xsl:apply-templates/>
    <img alt="{@xlink:href}">
      <xsl:for-each select="alt-text">
        <xsl:attribute name="alt">
          <xsl:value-of select="normalize-space(string(.))"/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:call-template name="assign-src"/>
    </img>
  </xsl:template>


  <xsl:template match="alt-text">
    <!-- handled with graphic or inline-graphic -->
  </xsl:template>

  <xsl:template match="list">
    <div class="list">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="label | title"/>
      <xsl:apply-templates select="." mode="list"/>
    </div>
  </xsl:template>

  <xsl:template priority="2" mode="list" match="list[@list-type = 'simple' or list-item/label]">
    <ul style="list-style-type: none">
      <xsl:apply-templates select="list-item"/>
    </ul>
  </xsl:template>


  <xsl:template match="list[@list-type = 'bullet' or not(@list-type)]" mode="list">
    <ul>
      <xsl:apply-templates select="list-item"/>
    </ul>
  </xsl:template>


  <xsl:template match="list" mode="list">
    <xsl:variable name="style">
      <xsl:choose>
        <xsl:when test="@list-type = 'alpha-lower'">lower-alpha</xsl:when>
        <xsl:when test="@list-type = 'alpha-upper'">upper-alpha</xsl:when>
        <xsl:when test="@list-type = 'roman-lower'">lower-roman</xsl:when>
        <xsl:when test="@list-type = 'roman-upper'">upper-roman</xsl:when>
        <xsl:otherwise>decimal</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <ol style="list-style-type: {$style}">
      <xsl:apply-templates select="list-item"/>
    </ol>
  </xsl:template>


  <xsl:template match="list-item">
    <li>
      <xsl:apply-templates/>
    </li>
  </xsl:template>


  <xsl:template match="list-item/label">
    <!-- if the next sibling is a p, the label will be called as
	       a run-in -->
    <xsl:if test="following-sibling::*[1][not(self::p)]">
      <xsl:call-template name="label"/>
    </xsl:if>
  </xsl:template>


  <xsl:template match="media">
    <a>
      <xsl:call-template name="assign-id"/>
      <xsl:call-template name="assign-href"/>
      <xsl:apply-templates/>
    </a>
  </xsl:template>
  
  <xsl:template match="n">
    <span class="n pagenumber">
      <xsl:if test="@nextpgnum">
        <xsl:attribute name="data-nextpgnum">
          <xsl:value-of select="@nextpgnum"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@prefxused">
          <xsl:attribute name="data-prefxused">
            <xsl:value-of select="@prefxused"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </span>  
  </xsl:template>
  
  
  <xsl:template match="pb">
    <p class="pb pagebreak">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="bx">
    <span class="bx biblioref" data-xref="{@r}">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
 
  <xsl:template match="impx"> <!--when not in metadata mode --> 
    <xsl:choose>
      <xsl:when test="@rx"> <!-- for the generated links -->
        <span class="impx" data-type="{@type}" data-rx="{@rx}" data-grpname="{@grpname}">
          <xsl:value-of select="."/>
        </span>
      </xsl:when>
      <xsl:otherwise> <!-- sometimes impx is manually tagged -->
        <span class="impx" data-type="{@type}">
          <xsl:value-of select="."/>
        </span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="quote">
    <div class="quote">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="src">
    <p class="src source">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  
  <xsl:template match="ftr">
      <div class="footer">
        <xsl:apply-templates/>
      </div>
  </xsl:template>  
  
  <xsl:template match="p | p2">
    <p class="para">
      <xsl:if test="not(preceding-sibling::*)">
        <xsl:attribute name="class">first</xsl:attribute>
      </xsl:if>
      <xsl:if test="name() = 'p2'">
        <!--        if you want to concatenate to the attribute class-->
        <!--          <xsl:value-of select="concat('continued',  ' ', @class)"/>-->
        <xsl:attribute name="class">p2 paracont</xsl:attribute>
      </xsl:if>
      
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="@content-type">
    <!-- <span class="generated">[</span>
    <xsl:value-of select="."/>
    <span class="generated">] </span> -->
  </xsl:template>


  <xsl:template match="list-item/p[not(preceding-sibling::*[not(self::label)])]">
    <p>
      <xsl:call-template name="assign-id"/>
      <xsl:for-each select="preceding-sibling::label">
        <span class="label">
          <xsl:apply-templates/>
        </span>
        <xsl:text> </xsl:text>
      </xsl:for-each>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="def-list">
    <div class="def-list">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="label | title"/>
      <div class="def-list table">
        <xsl:if test="term-head | def-head">
          <div class="row">
            <div class="cell def-list-head">
              <xsl:apply-templates select="term-head"/>
            </div>
            <div class="cell def-list-head">
              <xsl:apply-templates select="def-head"/>
            </div>
          </div>
        </xsl:if>
        <xsl:apply-templates select="def-item"/>
      </div>
      <xsl:apply-templates select="def-list"/>
    </div>
  </xsl:template>


  <xsl:template match="def-item">
    <div class="def-item row">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="term">
    <div class="def-term cell">
      <xsl:call-template name="assign-id"/>
      <p>
        <xsl:apply-templates/>
      </p>
    </div>
  </xsl:template>


  <xsl:template match="def">
    <div class="def-def cell">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="disp-quote">
    <div class="blockquote">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="preformat">
    <pre class="preformat">
      <xsl:apply-templates/>
    </pre>
  </xsl:template>

<!--
  <xsl:template match="alternatives | name-alternatives | collab-alternatives | aff-alternatives">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="citation-alternatives" priority="2">
    <!-\- priority bumped to supersede match on ref/* -\->
    <!-\- may appear in license-p, p, ref, td, th, title  -\->
    <xsl:apply-templates/>
  </xsl:template>
-->

  <xsl:template match="be">
    <div class="biblio row">
      <xsl:if test="@rx"> <!--matched reference id-->
        <xsl:attribute name="data-rx">
          <xsl:value-of select="@rx"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@rxcf"> <!--possible matched reference id-->
        <xsl:attribute name="data-rxcf">
          <xsl:value-of select="@rxcf"/>
        </xsl:attribute>
      </xsl:if>
      <span class="ref-label cell">
        <xsl:call-template name="named-anchor"/>
      </span>
      <div class="ref-content cell">
        <xsl:apply-templates/>
      </div>
    </div>
  </xsl:template>
  
  
  <xsl:template match="be/a">
    <xsl:text>&#13;</xsl:text>
    <span class="bibauthor a">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  
  <xsl:template match="a/l">
    <span class="bibauthorlastname l">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  
  <xsl:template match="be/y">
    <xsl:text>&#13;</xsl:text>
    <span class="bibyear y">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  
  <xsl:template match="be/t">
    <xsl:text>&#13;</xsl:text>
    <span class="bibtitle t">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  
  <xsl:template match="be/j">
    <xsl:text>&#xA0;</xsl:text>
    <span class="bibjournal j">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="be/bp">
    <span class="bibpublisher bp">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="be/pp">
    <span class="bibpages pp">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  <!--

  <xsl:template match="be/* | be/citation-alternatives/*" priority="0">
    <!-\- should match mixed-citation, element-citation, nlm-citation,
         or citation (in 2.3); note and label should be matched below;
         citation-alternatives is handled elsewhere -\->
    <p class="citation">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="be/note" priority="2">
    <xsl:param name="label" select="''"/>
    <xsl:if
      test="
        normalize-space(string($label))
        and not(preceding-sibling::*[not(self::label)])">
      <p class="label">
        <xsl:copy-of select="$label"/>
      </p>
    </xsl:if>
    <div class="note">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template
    match="
      abs | app/related-article |
      app-group/related-article | bio/related-article |
      body/related-article | boxed-text/related-article |
      disp-quote/related-article | glossary/related-article |
      gloss-group/related-article |
      ref-list/related-article | sec/related-article">
    <xsl:apply-templates select="." mode="metadata"/>
  </xsl:template>
-->


  <xsl:template match="speech">
    <div class="speech">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates mode="speech"/>
    </div>
  </xsl:template>


  <xsl:template match="speech/speaker" mode="speech"/>


  <xsl:template match="speech/p" mode="speech">
    <p>
      <xsl:apply-templates select="self::p[not(preceding-sibling::p)]/../speaker"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="speech/speaker">
    <b>
      <xsl:apply-templates/>
    </b>
    <span class="generated">: </span>
  </xsl:template>


  <xsl:template match="supplementary-material">
    <div class="panel">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="tex-math">
    <span class="tex-math">
      <span class="generated">[TeX:] </span>
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="mml:*">
    <!-- this stylesheet simply copies MathML through. If your browser
         supports it, you will get it -->
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>


  <xsl:template match="verse-group">
    <div class="verse">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="verse-line">
    <p class="verse-line">
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template
    match="
      aff/label | corresp/label | chem-struct/label |
      element-citation/label | mixed-citation/label | citation/label">
    <!-- these labels appear in line -->
    <span class="generated">[</span>
    <xsl:apply-templates/>
    <span class="generated">] </span>
  </xsl:template>


  <xsl:template
    match="
      app/label | boxed-text/label |
      chem-struct-wrap/label | chem-struct-wrapper/label |
      disp-formula/label | fig/label | fn/label | ref/label |
      statement/label | supplementary-material/label | table-wrap/label"
    priority="2">
    <!-- suppressed, since acquired by their parents in mode="label" -->
  </xsl:template>


  <xsl:template match="p/label">
    <span class="label">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="label" name="label">
    <!-- other labels are displayed as blocks -->
    <h5 class="label">
      <xsl:apply-templates/>
    </h5>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  TABLES                                                       -->
  <!-- ============================================================= -->
  <!--  Tables are already in XHTML, and can simply be copied
        through                                                      -->

  <xsl:template match="row">
    <!-- other labels are displayed as blocks -->
    <tr class="tablerow row">
      <xsl:apply-templates/>
    </tr>
  </xsl:template>
  
  <xsl:template match="entry">
    <!-- other labels are displayed as blocks -->
    <td class="tableentry entry">
      <xsl:apply-templates/>
    </td>
  </xsl:template>

  <xsl:template match="tgroup">
    <!-- other labels are displayed as blocks -->
    <tgroup class="tablegroup tgroup">
      <colgroup>
        <xsl:apply-templates select="./colspec" mode="colgroup"/>
      </colgroup>
      <xsl:apply-templates/>
    </tgroup>
  </xsl:template>

  <!--Packaged in colgroup only-->
  <xsl:template match="colspec" mode="colgroup">
    <!-- other labels are displayed as blocks -->
    <col class="columnspec colspec">
      <xsl:if test="@colwidth"> 
        <xsl:attribute name="span">
          <xsl:value-of select="@colwidth"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@align">
        <xsl:attribute name="style">
          <xsl:value-of select="@align"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </col>
  </xsl:template>
  

  <xsl:template match="
      table | thead | tbody | tfoot |
      col | colgroup | tr | th | td">
    <xsl:copy>
      <xsl:apply-templates select="@*" mode="table-copy"/>
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>


  <xsl:template match="array/tbody">
    <table>
      <xsl:copy>
        <xsl:apply-templates select="@*" mode="table-copy"/>
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates/>
      </xsl:copy>
    </table>
  </xsl:template>


  <xsl:template match="@*" mode="table-copy">
    <xsl:copy-of select="."/>
  </xsl:template>


  <xsl:template match="@content-type" mode="table-copy"/>


  <!-- ============================================================= -->
  <!--  INLINE MISCELLANEOUS                                         -->
  <!-- ============================================================= -->
  <!--  Templates strictly for formatting follow; these are templates
        to handle various inline structures -->


  <xsl:template match="abbrev">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="abbrev[normalize-space(string(@xlink:href))]">
    <a>
      <xsl:call-template name="assign-href"/>
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="abbrev/def">
    <xsl:text>[</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]</xsl:text>
  </xsl:template>

  <xsl:template
    match="
      p/address | license-p/address |
      named-content/p | styled-content/p">
    <xsl:apply-templates mode="inline"/>
  </xsl:template>


  <xsl:template match="address/*" mode="inline">
    <xsl:if test="preceding-sibling::*">
      <span class="generated">, </span>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="award-id">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="award-id[normalize-space(string(@rid))]">
    <a href="#{@rid}">
      <xsl:apply-templates/>
    </a>
  </xsl:template>


  <xsl:template match="break">
    <br class="br"/>
  </xsl:template>


  <xsl:template match="email">
    <a href="mailto:{.}">
      <xsl:apply-templates/>
    </a>
  </xsl:template>


  <xsl:template match="ext-link | uri | inline-supplementary-material">
    <a target="xrefwindow">
      <xsl:attribute name="href">
        <xsl:value-of select="."/>
      </xsl:attribute>
      <!-- if an @href is present, it overrides the href
           just attached -->
      <xsl:call-template name="assign-href"/>
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
      <xsl:if test="not(normalize-space(string(.)))">
        <xsl:value-of select="@xlink:href"/>
      </xsl:if>
    </a>
  </xsl:template>


  <xsl:template match="funding-source">
    <span class="funding-source">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="hr">
    <hr class="hr"/>
  </xsl:template>


  <!-- inline-graphic is handled above, with graphic -->


  <xsl:template match="inline-formula | chem-struct">
    <span class="{local-name()}">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="chem-struct-wrap/chem-struct | chem-struct-wrapper/chem-struct">
    <div class="{local-name()}">
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="milestone-start | milestone-end">
    <span class="{substring-after(local-name(),'milestone-')}">
      <xsl:comment>
        <xsl:value-of select="@rationale"/>
      </xsl:comment>
    </span>
  </xsl:template>


  <xsl:template match="object-id">
    <span class="{local-name()}">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <!-- preformat is handled above -->

  <xsl:template match="sig">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="target">
    <xsl:call-template name="named-anchor"/>
  </xsl:template>


  <xsl:template match="styled-content">
    <span>
      <xsl:copy-of select="@style"/>
      <xsl:for-each select="@style-type">
        <xsl:attribute name="class">
          <xsl:value-of select="."/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="named-content">
    <span>
      <xsl:for-each select="@content-type">
        <xsl:attribute name="class">
          <xsl:value-of select="translate(., ' ', '-')"/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="private-char">
    <span>
      <xsl:for-each select="@description">
        <xsl:attribute name="title">
          <xsl:value-of select="."/>
        </xsl:attribute>
      </xsl:for-each>
      <span class="generated">[Private character </span>
      <xsl:for-each select="@name">
        <xsl:text> </xsl:text>
        <xsl:value-of select="."/>
      </xsl:for-each>
      <span class="generated">]</span>
    </span>
  </xsl:template>


  <xsl:template match="glyph-data | glyph-ref">
    <span class="generated">(Glyph not rendered)</span>
  </xsl:template>


  <xsl:template match="related-article">
    <span class="generated">[Related article:] </span>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="related-object">
    <span class="generated">[Related object:] </span>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="xref[not(normalize-space(string(.)))]">
    <a href="#{@rid}">
      <xsl:apply-templates select="key('element-by-id', @rid)" mode="label-text">
        <xsl:with-param name="warning" select="true()"/>
      </xsl:apply-templates>
    </a>
  </xsl:template>


  <xsl:template match="xref">
    <a href="#{@rid}">
      <xsl:apply-templates/>
    </a>
  </xsl:template>



  <!-- ============================================================= -->
  <!--  Formatting elements                                          -->
  <!-- ============================================================= -->


  <xsl:template match="bold">
    <b>
      <xsl:apply-templates/>
    </b>
  </xsl:template>


  <xsl:template match="italic">
    <i>
      <xsl:apply-templates/>
    </i>
  </xsl:template>


  <xsl:template match="monospace">
    <tt>
      <xsl:apply-templates/>
    </tt>
  </xsl:template>


  <xsl:template match="overline">
    <span style="text-decoration: overline">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="price">
    <span class="price">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="roman">
    <span style="font-style: normal">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="sans-serif">
    <span style="font-family: sans-serif; font-size: 80%">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="sc">
    <span style="font-variant: small-caps">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="strike">
    <span style="text-decoration: line-through">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="sub">
    <sub>
      <xsl:apply-templates/>
    </sub>
  </xsl:template>


  <xsl:template match="sup">
    <sup>
      <xsl:apply-templates/>
    </sup>
  </xsl:template>


  <xsl:template match="underline">
    <span style="text-decoration: underline">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  BACK MATTER                                                  -->
  <!-- ============================================================= -->


  <xsl:variable name="loose-footnotes"
    select="//fn[not(ancestor::front | parent::fn-group | ancestor::table-wrap)]"/>


  <xsl:template name="make-back">
    <xsl:apply-templates select="back"/>
    <xsl:if test="$loose-footnotes and not(back)">
      <!-- autogenerating a section for footnotes only if there is no
           back element, and if footnotes exist for it -->
      <xsl:call-template name="footnotes"/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="back">
    <!-- content model for back: 
          (label?, title*, 
          (ack | app-group | bio | fn-group | glossary | ref-list |
           notes | sec)*) -->
    <xsl:if test="not(fn-group) and $loose-footnotes">
      <xsl:call-template name="footnotes"/>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template name="footnotes">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Notes</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="$loose-footnotes" mode="footnote"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="ack">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Acknowledgements</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="app-group">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Appendices</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="back/bio">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Biography</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="back/fn-group">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Notes</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="back/glossary | back/gloss-group">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Glossary</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


<!--  <xsl:template match="back/ref-list">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">References</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:call-template name="ref-list"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
-->

  <xsl:template match="back/notes">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Notes</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="backmatter-section">
    <xsl:param name="generated-title"/>
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <div class="back-section">
      <xsl:call-template name="named-anchor"/>
      <xsl:if test="not(title) and $generated-title">
        <xsl:choose>
          <!-- The level of title depends on whether the back matter itself
               has a title -->
          <xsl:when test="ancestor::back/title">
            <xsl:call-template name="section-title">
              <xsl:with-param name="contents" select="$generated-title"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:call-template name="main-title">
              <xsl:with-param name="contents" select="$generated-title"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:copy-of select="$contents"/>
    </div>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  FOOTNOTES                                                    -->
  <!-- ============================================================= -->

  <xsl:template match="fn">
    <!-- Footnotes appearing outside fn-group
       generate cross-references to the footnote,
       which is displayed elsewhere -->
    <!-- Note the rules for displayed content: if any fn elements
       not inside an fn-group (the matched fn or any other) includes
       a label child, all footnotes are expected to have a label
       child. -->
    <xsl:variable name="id">
      <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>
    <a href="#{$id}">
      <xsl:apply-templates select="." mode="label-text">
        <xsl:with-param name="warning" select="true()"/>
      </xsl:apply-templates>
    </a>
  </xsl:template>

  <xsl:template match="
      fn-group/fn | table-wrap-foot/fn |
      table-wrap-foot/fn-group/fn">
    <xsl:apply-templates select="." mode="footnote"/>
  </xsl:template>


  <xsl:template match="fn" mode="footnote">
    <div class="footnote">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="fn/p">
    <p>
      <xsl:call-template name="assign-id"/>
      <xsl:if test="not(preceding-sibling::p)">
        <!-- drop an inline label text into the first p -->
        <xsl:apply-templates select="parent::fn" mode="label-text"/>
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  MODE 'label-text'
	      Generates label text for elements and their cross-references -->
  <!-- ============================================================= -->
  <!--  This mode is to support auto-numbering and generating of
        labels for certain elements by the stylesheet.
  
        The logic is as follows: for any such element type, if a
        'label' element is ever present, it is expected always to be 
        present; automatic numbering is not performed on any elements
        of that type. For example, the presence of a 'label' element 
        in any 'fig' is taken to indicate that all figs should likewise
        be labeled, and any 'fig' without a label is supposed to be 
        unlabelled (and unnumbered). But if no 'fig' elements have 
        'label' children, labels with numbers are generated for all 
        figs in display.
        
        This logic applies to:
          app, boxed-text, chem-struct-wrap, disp-formula, fig, fn, 
          note, ref, statement, table-wrap.
        
        There is one exception in the case of fn elements, where
        the checking for labels (or for @symbol attributes in the
        case of this element) is performed only within its parent
        fn-group, or in the scope of all fn elements not in an
        fn-group, for fn elements appearing outside fn-group.
        
        In all cases, this logic can be altered simply by overwriting 
        templates in "label" mode for any of these elements.
        
        For other elements, a label is simply displayed if present,
        and auto-numbering is never performed.
        These elements include:
          (label appearing in line) aff, corresp, chem-struct, 
          element-citation, mixed-citation
          
          (label appearing as a block) abstract, ack, app-group, 
          author-notes, back, bio, def-list, disp-formula-group, 
          disp-quote, fn-group, glossary, graphic, kwd-group, 
          list, list-item, media, notes, ref-list, sec, 
          supplementary-material, table-wrap-group, 
          trans-abstract, verse-group -->


  <xsl:variable name="auto-label-app" select="false()"/>
  <xsl:variable name="auto-label-boxed-text" select="false()"/>
  <xsl:variable name="auto-label-chem-struct-wrap" select="false()"/>
  <xsl:variable name="auto-label-disp-formula" select="false()"/>
  <xsl:variable name="auto-label-fig" select="false()"/>
  <xsl:variable name="auto-label-ref" select="not(//ref[label])"/>
  <!-- ref elements are labeled unless any ref already has a label -->

  <xsl:variable name="auto-label-statement" select="false()"/>
  <xsl:variable name="auto-label-supplementary" select="false()"/>
  <xsl:variable name="auto-label-table-wrap" select="false()"/>

  <!--
  These variables assignments show how autolabeling can be 
  configured conditionally.
  For example: "label figures if no figures have labels" translates to
    "not(//fig[label])", which will resolve to Boolean true() when the set of
    all fig elements with labels is empty.
  
  <xsl:variable name="auto-label-app" select="not(//app[label])"/>
  <xsl:variable name="auto-label-boxed-text" select="not(//boxed-text[label])"/>
  <xsl:variable name="auto-label-chem-struct-wrap" select="not(//chem-struct-wrap[label])"/>
  <xsl:variable name="auto-label-disp-formula" select="not(//disp-formula[label])"/>
  <xsl:variable name="auto-label-fig" select="not(//fig[label])"/>
  <xsl:variable name="auto-label-ref" select="not(//ref[label])"/>
  <xsl:variable name="auto-label-statement" select="not(//statement[label])"/>
  <xsl:variable name="auto-label-supplementary"
    select="not(//supplementary-material[not(ancestor::front)][label])"/>
  <xsl:variable name="auto-label-table-wrap" select="not(//table-wrap[label])"/>
-->

  <xsl:template mode="label" match="*" name="block-label">
    <xsl:param name="contents">
      <xsl:apply-templates select="." mode="label-text">
        <!-- we place a warning for missing labels if this element is ever
             cross-referenced with an empty xref -->
        <xsl:with-param name="warning"
          select="boolean(key('xref-by-rid', @id)[not(normalize-space(string(.)))])"/>
      </xsl:apply-templates>
    </xsl:param>
    <xsl:if test="normalize-space(string($contents))">
      <!-- not to create an h5 for nothing -->
      <h5 class="label">
        <xsl:copy-of select="$contents"/>
      </h5>
    </xsl:if>
  </xsl:template>


  <xsl:template mode="label" match="ref">
    <xsl:param name="contents">
      <xsl:apply-templates select="." mode="label-text"/>
    </xsl:param>
    <xsl:if test="normalize-space(string($contents))">
      <!-- we're already in a p -->
      <span class="label">
        <xsl:copy-of select="$contents"/>
      </span>
    </xsl:if>
  </xsl:template>


  <xsl:template match="app" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-app"/>
      <xsl:with-param name="warning" select="$warning"/>
      <!--
      Pass in the desired label if a label is to be autogenerated  
      <xsl:with-param name="auto-text">
        <xsl:text>Appendix </xsl:text>
        <xsl:number format="A"/>
      </xsl:with-param>-->
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="boxed-text" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-boxed-text"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Box </xsl:text>
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="disp-formula" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-disp-formula"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Formula </xsl:text>
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="chem-struct-wrap | chem-struct-wrapper" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-chem-struct-wrap"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Formula (chemical) </xsl:text>
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="fig" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-fig"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Figure </xsl:text>
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="front//fn" mode="label-text">
    <xsl:param name="warning" select="boolean(key('xref-by-rid', @id))"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels);
         by default, we get a warning only if we need a label for
         a cross-reference -->
    <!-- auto-number-fn is true only if (1) this fn is cross-referenced, and
         (2) there exists inside the front matter any fn elements with
         cross-references, but not labels or @symbols. -->
    <xsl:param name="auto-number-fn"
      select="
        boolean(key('xref-by-rid', parent::fn/@id)) and
        boolean(ancestor::front//fn[key('xref-by-rid', @id)][not(label | @symbol)])"/>
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-number-fn"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:number level="any" count="fn" from="front" format="a"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="table-wrap//fn" mode="label-text">
    <xsl:param name="warning" select="boolean(key('xref-by-rid', @id))"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels);
         by default, we get a warning only if we need a label for
         a cross-reference -->
    <xsl:param name="auto-number-fn"
      select="not(ancestor::table-wrap//fn/label | ancestor::table-wrap//fn/@symbol)"/>
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-number-fn"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>[</xsl:text>
        <xsl:number level="any" count="fn" from="table-wrap" format="i"/>
        <xsl:text>]</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="fn" mode="label-text">
    <xsl:param name="warning" select="boolean(key('xref-by-rid', @id))"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels);
         by default, we get a warning only if we need a label for
         a cross-reference -->
    <!-- autonumber all fn elements outside fn-group,
         front matter and table-wrap only if none of them 
         have labels or @symbols (to keep numbering
         orderly) -->
    <xsl:variable name="in-scope-notes"
      select="
        ancestor::article//fn[not(parent::fn-group
        | ancestor::front
        | ancestor::table-wrap)]"/>
    <xsl:variable name="auto-number-fn"
      select="
        not($in-scope-notes/label |
        $in-scope-notes/@symbol)"/>
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-number-fn"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>[</xsl:text>
        <xsl:number level="any" count="fn[not(ancestor::front)]"
          from="article | sub-article | response"/>
        <xsl:text>]</xsl:text>
        <xsl:apply-templates select="@fn-type"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'abbr']" priority="2">
    <span class="generated"> Abbreviation</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'com']" priority="2">
    <span class="generated"> Communicated by</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'con']" priority="2">
    <span class="generated"> Contributed by</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'conflict']" priority="2">
    <span class="generated"> Conflicts of interest</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'corresp']" priority="2">
    <span class="generated"> Corresponding author</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'current-aff']" priority="2">
    <span class="generated"> Current affiliation</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'deceased']" priority="2">
    <span class="generated"> Deceased</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'edited-by']" priority="2">
    <span class="generated"> Edited by</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'equal']" priority="2">
    <span class="generated"> Equal contributor</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'financial-disclosure']" priority="2">
    <span class="generated"> Financial disclosure</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'on-leave']" priority="2">
    <span class="generated"> On leave</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'other']" priority="2"/>

  <xsl:template match="fn/@fn-type[. = 'participating-researchers']" priority="2">
    <span class="generated"> Participating researcher</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'present-address']" priority="2">
    <span class="generated"> Current address</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'presented-at']" priority="2">
    <span class="generated"> Presented at</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'presented-by']" priority="2">
    <span class="generated"> Presented by</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'previously-at']" priority="2">
    <span class="generated"> Previously at</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'study-group-members']" priority="2">
    <span class="generated"> Study group member</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'supplementary-material']" priority="2">
    <span class="generated"> Supplementary material</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type[. = 'supported-by']" priority="2">
    <span class="generated"> Supported by</span>
  </xsl:template>

  <xsl:template match="fn/@fn-type"/>


  <xsl:template match="ref" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-ref"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="statement" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-statement"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Statement </xsl:text>
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="supplementary-material" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-supplementary"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Supplementary Material </xsl:text>
        <xsl:number level="any" format="A" count="supplementary-material[not(ancestor::front)]"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="table-wrap" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-table-wrap"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Table </xsl:text>
        <xsl:number level="any" format="I"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="*" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="warning" select="$warning"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="label" mode="label-text">
    <xsl:apply-templates mode="inline-label-text"/>
  </xsl:template>

  <xsl:template match="text()" mode="inline-label-text">
    <!-- when displaying labels, space characters become non-breaking spaces -->
    <xsl:value-of
      select="translate(normalize-space(string(.)), ' &#xA;&#x9;', '&#xA0;&#xA0;&#xA0;')"/>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  Writing a name                                               -->
  <!-- ============================================================= -->

  <!-- Called when displaying structured names in metadata         -->

  <xsl:template match="name">
    <xsl:apply-templates select="prefix" mode="inline-name"/>
    <xsl:apply-templates select="surname[../@name-style = 'eastern']" mode="inline-name"/>
    <xsl:apply-templates select="given-names" mode="inline-name"/>
    <xsl:apply-templates select="surname[not(../@name-style = 'eastern')]" mode="inline-name"/>
    <xsl:apply-templates select="suffix" mode="inline-name"/>
  </xsl:template>


  <xsl:template match="prefix" mode="inline-name">
    <xsl:apply-templates/>
    <xsl:if test="../surname | ../given-names | ../suffix">
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="given-names" mode="inline-name">
    <xsl:apply-templates/>
    <xsl:if test="../surname[not(../@name-style = 'eastern')] | ../suffix">
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="contrib/name/surname" mode="inline-name">
    <xsl:apply-templates/>
    <xsl:if test="../given-names[../@name-style = 'eastern'] | ../suffix">
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="surname" mode="inline-name">
    <xsl:apply-templates/>
    <xsl:if test="../given-names[../@name-style = 'eastern'] | ../suffix">
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="suffix" mode="inline-name">
    <xsl:apply-templates/>
  </xsl:template>


  <!-- string-name elements are written as is -->

  <xsl:template match="string-name">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="string-name/*">
    <xsl:apply-templates/>
  </xsl:template>


  <!--  *************************************************************
      METADATA GENERATING TEMPLATE HERE! 
      *************************************************************
                                                                -->
  <xsl:template name="top-citeas">
    <xsl:param name="authors"/>
    <xsl:param name="year"/>
    <xsl:param name="title"/>
    <xsl:param name="journal-abbr"/>
    <xsl:param name="vol"/>
    <xsl:param name="pgrg"/>
    <span id="topciteas">
      <span class="authors"><xsl:copy-of select="$authors"/></span><span class="year">((<xsl:copy-of select="$year"/>)).</span><span class="title">($title)</span>
      <span class="jrnlabbr">($journal-abbr)</span>,<span class="vol">($vol)</span><xsl:text>:</xsl:text>><span class="pgrg">($pgrg).</span>
    </span>
  </xsl:template>
  
  
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


  <xsl:template name="metadata-area">
    <xsl:param name="label"/>
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <div class="metadata-area">
      <xsl:if test="normalize-space(string($label))">
        <xsl:call-template name="metadata-labeled-entry">
          <xsl:with-param name="label">
            <xsl:copy-of select="$label"/>
          </xsl:with-param>
          <xsl:with-param name="contents"/>
        </xsl:call-template>
      </xsl:if>
      <div class="metadata-chunk">
        <xsl:copy-of select="$contents"/>
      </div>
    </div>
  </xsl:template>


  <xsl:template name="make-label-text">
    <xsl:param name="auto" select="false()"/>
    <xsl:param name="warning" select="false()"/>
    <xsl:param name="auto-text"/>
    <xsl:choose>
      <xsl:when test="$auto">
        <span class="generated">
          <xsl:copy-of select="$auto-text"/>
        </span>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="label-text" select="label | @symbol"/>
        <xsl:if test="$warning and not(label | @symbol)">
          <span class="warning">
            <xsl:text>{ label</xsl:text>
            <xsl:if test="self::fn"> (or @symbol)</xsl:if>
            <xsl:text> needed for </xsl:text>
            <xsl:value-of select="local-name()"/>
            <xsl:for-each select="@id">
              <xsl:text>[@id='</xsl:text>
              <xsl:value-of select="."/>
              <xsl:text>']</xsl:text>
            </xsl:for-each>
            <xsl:text> }</xsl:text>
          </span>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template name="assign-id">
    <xsl:variable name="id">
      <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>
    <xsl:attribute name="id">
      <xsl:value-of select="$id"/>
    </xsl:attribute>
  </xsl:template>


  <xsl:template name="assign-src">
    <xsl:for-each select="@xlink:href">
      <xsl:attribute name="src">
        <xsl:value-of select="."/>
      </xsl:attribute>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="assign-href">
    <xsl:for-each select="@xlink:href">
      <xsl:attribute name="href">
        <xsl:value-of select="."/>
      </xsl:attribute>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="named-anchor">
    <!-- generates an HTML named anchor -->
    <xsl:variable name="id">
      <xsl:choose>
        <xsl:when test="@id">
          <!-- if we have an @id, we use it -->
          <xsl:value-of select="@id"/>
        </xsl:when>
        <xsl:when
          test="
            not(preceding-sibling::*) and
            (parent::alternatives | parent::name-alternatives |
            parent::citation-alternatives | parent::collab-alternatives |
            parent::aff-alternatives)/@id">
          <!-- if not, and we are first among our siblings inside one of
               several 'alternatives' wrappers, we use its @id if available -->
          <xsl:value-of
            select="
              (parent::alternatives | parent::name-alternatives |
              parent::citation-alternatives | parent::collab-alternatives |
              parent::aff-alternatives)/@id"
          />
        </xsl:when>
        <xsl:otherwise>
          <!-- otherwise we simply generate an ID -->
          <xsl:value-of select="generate-id(.)"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <a id="{$id}" class="mods"></a>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  Process warnings                                             -->
  <!-- ============================================================= -->
  <!-- Generates a list of warnings to be reported due to processing
     anomalies. -->

  <xsl:template name="process-warnings">
    <!-- Only generate the warnings if set to $verbose -->
    <xsl:if test="$verbose">
      <!-- returns an RTF containing all the warnings -->
      <xsl:variable name="xref-warnings">
        <xsl:for-each select="//xref[not(normalize-space(string(.)))]">
          <xsl:variable name="target-label">
            <xsl:apply-templates select="key('element-by-id', @rid)" mode="label-text">
              <xsl:with-param name="warning" select="false()"/>
            </xsl:apply-templates>
          </xsl:variable>
          <xsl:if
            test="
              not(normalize-space(string($target-label))) and
              generate-id(.) = generate-id(key('xref-by-rid', @rid)[1])">
            <!-- if we failed to get a label with no warning, and
               this is the first cross-reference to this target
               we ask again to get the warning -->
            <li>
              <xsl:apply-templates select="key('element-by-id', @rid)" mode="label-text">
                <xsl:with-param name="warning" select="true()"/>
              </xsl:apply-templates>
            </li>
          </xsl:if>
        </xsl:for-each>
      </xsl:variable>

      <xsl:if test="normalize-space(string($xref-warnings))">
        <h4>Elements are cross-referenced without labels.</h4>
        <p>Either the element should be provided a label, or their cross-reference(s) should have
          literal text content.</p>
        <ul>
          <xsl:copy-of select="$xref-warnings"/>
        </ul>
      </xsl:if>


      <xsl:variable name="alternatives-warnings">
        <!-- for reporting any element with a @specific-use different
           from a sibling -->
        <xsl:for-each select="//*[@specific-use != ../*/@specific-use]/..">
          <li>
            <xsl:text>In </xsl:text>
            <xsl:apply-templates select="." mode="xpath"/>
            <ul>
              <xsl:for-each select="*[@specific-use != ../*/@specific-use]">
                <li>
                  <xsl:apply-templates select="." mode="pattern"/>
                </li>
              </xsl:for-each>
            </ul>
            <!--<xsl:text>: </xsl:text>
          <xsl:call-template name="list-elements">
            <xsl:with-param name="elements" select="*[@specific-use]"/>
          </xsl:call-template>-->
          </li>
        </xsl:for-each>
      </xsl:variable>

      <xsl:if test="normalize-space(string($alternatives-warnings))">
        <h4>Elements with different 'specific-use' assignments appearing together</h4>
        <ul>
          <xsl:copy-of select="$alternatives-warnings"/>
        </ul>
      </xsl:if>
    </xsl:if>

  </xsl:template>

  <!-- ============================================================= -->
  <!--  id mode                                                      -->
  <!-- ============================================================= -->
  <!-- An id can be derived for any element. If an @id is given,
     it is presumed unique and copied. If not, one is generated.   -->

  <xsl:template match="*" mode="id">
    <xsl:value-of select="@id"/>
    <xsl:if test="not(@id)">
      <xsl:value-of select="generate-id(.)"/>
    </xsl:if>
  </xsl:template>


  <xsl:template match="pepbd3 | grp | unit" mode="id">
    <xsl:value-of select="@id"/>
    <xsl:if test="not(@id)">
      <xsl:value-of select="local-name()"/>
      <xsl:number from="article" level="multiple" count="pepbd3 | grp | unit" format="1-1"/>
    </xsl:if>
  </xsl:template>




  <!-- ============================================================= -->
  <!--  "author-string" writes authors' names in sequence            -->
  <!-- ============================================================= -->

  <xsl:template name="author-string">
    <xsl:variable name="all-contribs" select="/pepkbd3/artinfo/artauth/aut"/>
    <xsl:for-each select="$all-contribs">
      <xsl:if test="count($all-contribs) &gt; 1">
        <xsl:if test="position() &gt; 1">
          <xsl:if test="count($all-contribs) &gt; 2">,</xsl:if>
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:if test="position() = count($all-contribs)"> and </xsl:if>
      </xsl:if>
      <xsl:value-of select="."/>
    </xsl:for-each>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  Utility templates for generating warnings and reports        -->
  <!-- ============================================================= -->

  <xsl:template match="*" mode="pattern">
    <xsl:value-of select="name(.)"/>
    <xsl:for-each select="@*">
      <xsl:text>[@</xsl:text>
      <xsl:value-of select="name()"/>
      <xsl:text>='</xsl:text>
      <xsl:value-of select="."/>
      <xsl:text>']</xsl:text>
    </xsl:for-each>
  </xsl:template>


  <xsl:template match="node()" mode="xpath">
    <xsl:apply-templates mode="xpath" select=".."/>
    <xsl:apply-templates mode="xpath-step" select="."/>
  </xsl:template>


  <xsl:template match="/" mode="xpath"/>


  <xsl:template match="*" mode="xpath-step">
    <xsl:variable name="name" select="name(.)"/>
    <xsl:text>/</xsl:text>
    <xsl:value-of select="$name"/>
    <xsl:if test="count(../*[name(.) = $name]) > 1">
      <xsl:text>[</xsl:text>
      <xsl:value-of select="count(. | preceding-sibling::*[name(.) = $name])"/>
      <xsl:text>]</xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="@*" mode="xpath-step">
    <xsl:text>/@</xsl:text>
    <xsl:value-of select="name(.)"/>
  </xsl:template>


  <xsl:template match="comment()" mode="xpath-step">
    <xsl:text>/comment()</xsl:text>
    <xsl:if test="count(../comment()) > 1">
      <xsl:text>[</xsl:text>
      <xsl:value-of select="count(. | preceding-sibling::comment())"/>
      <xsl:text>]</xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="processing-instruction()" mode="xpath-step">
    <xsl:text>/processing-instruction()</xsl:text>
    <xsl:if test="count(../processing-instruction()) > 1">
      <xsl:text>[</xsl:text>
      <xsl:value-of select="count(. | preceding-sibling::processing-instruction())"/>
      <xsl:text>]</xsl:text>
    </xsl:if>
  </xsl:template>


  <xsl:template match="text()" mode="xpath-step">
    <xsl:text>/text()</xsl:text>
    <xsl:if test="count(../text()) > 1">
      <xsl:text>[</xsl:text>
      <xsl:value-of select="count(. | preceding-sibling::text())"/>
      <xsl:text>]</xsl:text>
    </xsl:if>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  End stylesheet                                               -->
  <!-- ============================================================= -->

</xsl:stylesheet>
