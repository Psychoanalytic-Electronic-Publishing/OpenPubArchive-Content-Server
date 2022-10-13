<?xml version="1.0"?>
<!-- ============================================================= -->
<!--  MODULE:    HTML Preview of PEP-Web KBD3 instances            -->
<!--     BASED-ON:  HTML Preview of NISO JATS Publishing 1.0 XML   -->
<!--  DATE:      2020-10-10                                       -->
<!--  Revisions:

     TODO:
     - I've yet to remove the irrelevant JATS rules
     - Decide if the data-pagehelper attributes are helpful
     for page return

     2020-10-10  - Substituted font-awesome icon for info, flag,
     and book icons.  Also arrow after biblio
     2020-09-07  - Added GW/SE language attributes so they are included
     in the HTML
     2020-04-21  - Some cleanup (removed commented code)
     - added experimental code to mark top level elements
     to permit easy page returns (for delivering a page
     or set of pages to the client app while keeping the
     html intact)
     - removed some id prefixes (not sure why they were
     being used)
     2020-02-22  Changed doctype generation to exclude ns from being
     included and generic html (5) instead of 4 loose.
     2020-01-09  Added conditionals to footer detection to mark first
     paragraph correctly.
     2019-12-10: set video callout to newest Wistia player which
     allows seek by captions!
     added link to banner icon to search volume
     (required an additon to PEPEasy to support it.
     2019-12-09: add xml to html video callout conversion
     2019-11-25: fix lang attribute insertion
     2019-08:   Misc fixes
     - Fixed functions by adding fn namespace missing
     from declaration
     - Added some cases of list types found.
-->
<!-- ============================================================= -->
<!--

-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xlink="http://www.w3.org/1999/xlink">
    <!--  xmlns:fn="http://www.w3.org/2005/xpath-functions" -->

    <!--  Commented out next line site seems to have availability problems -->
    <!--  <xsl:import href="http://www.w3.org/2003/entities/2007/entitynamesmap.xsl"/>-->

    <xsl:output method="html" encoding="UTF-8" indent="yes" />

    <!--  <xsl:output doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
         doctype-system="http://www.w3.org/TR/html4/loose.dtd" encoding="UTF-8"/>
    -->
    <!-- Space is preserved in all elements allowing #PCDATA -->
    <xsl:preserve-space
        elements="body
              group
              p
              h1 h2 h3 h4 h5
              binc
              "/>

    <xsl:strip-space elements="*"/>
    <!--<xsl:param name="css3" select="'pep-pdf-epub.css'"/>-->
    <xsl:param name="report-warnings" select="'no'"/>
<!--    <xsl:param name="imageUrl"/>-->
    <xsl:variable name="domain" select="'$OPAS_SERVER_DOMAIN;'" />
    <xsl:variable name="imageUrl" select="'$OPAS_IMAGE_URL;'" />
    <xsl:variable name="journalName" select="'$OPAS_JOURNAL_NAME;'"/>
    <xsl:variable name="clientId" select="'$OPAS_CLIENT_ID;'"/>
    <xsl:variable name="sessionId" select="'$OPAS_SESSION_ID;'"/>
    <xsl:variable name="translationConcordanceEnabled" select="'$OPAS_CONCORDANCE_ENABLED;'"/>
    <xsl:variable name="glossaryTermFormattingEnabled" select="'$OPAS_GLOSSARY_TERM_FORMATTING_ENABLED;'"/>
    <xsl:variable name="isBook" select="'$OPAS_IS_BOOK;'"/>
    
<!--    <xsl:param name="journalName"/>
    <xsl:param name="clientId"/>
    <xsl:param name="sessionId"/>
    <xsl:param name="translationConcordanceEnabled" />
    <xsl:param name="glossaryTermFormattingEnabled" />
    <xsl:param name="isBook"/>
-->
    <xsl:variable name="fa-right-arrow">
        <svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="arrow-circle-right" data-prefix="fas" id="ember279" class="pointer-events-none svg-inline--fa fa-arrow-circle-right fa-w-16 ember-view"><path fill="currentColor" d="M256 8c137 0 248 111 248 248S393 504 256 504 8 393 8 256 119 8 256 8zm-28.9 143.6l75.5 72.4H120c-13.3 0-24 10.7-24 24v16c0 13.3 10.7 24 24 24h182.6l-75.5 72.4c-9.7 9.3-9.9 24.8-.4 34.3l11 10.9c9.4 9.4 24.6 9.4 33.9 0L404.3 273c9.4-9.4 9.4-24.6 0-33.9L271.6 106.3c-9.4-9.4-24.6-9.4-33.9 0l-11 10.9c-9.5 9.6-9.3 25.1.4 34.4z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-information">
        <svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="info-circle" data-prefix="fal" id="ember313" class="pointer-events-none svg-inline--fa fa-info-circle fa-w-16 ember-view"><path fill="currentColor" d="M256 40c118.621 0 216 96.075 216 216 0 119.291-96.61 216-216 216-119.244 0-216-96.562-216-216 0-119.203 96.602-216 216-216m0-32C119.043 8 8 119.083 8 256c0 136.997 111.043 248 248 248s248-111.003 248-248C504 119.083 392.957 8 256 8zm-36 344h12V232h-12c-6.627 0-12-5.373-12-12v-8c0-6.627 5.373-12 12-12h48c6.627 0 12 5.373 12 12v140h12c6.627 0 12 5.373 12 12v8c0 6.627-5.373 12-12 12h-72c-6.627 0-12-5.373-12-12v-8c0-6.627 5.373-12 12-12zm36-240c-17.673 0-32 14.327-32 32s14.327 32 32 32 32-14.327 32-32-14.327-32-32-32z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-flag">
        <svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="flag" data-prefix="fal" id="ember313" class="pointer-events-none svg-inline--fa fa-flag fa-w-16 ember-view"><path fill="currentColor" d="M344.348 74.667C287.742 74.667 242.446 40 172.522 40c-28.487 0-53.675 5.322-76.965 14.449C99.553 24.713 75.808-1.127 46.071.038 21.532.999 1.433 20.75.076 45.271-1.146 67.34 12.553 86.382 32 93.258V500c0 6.627 5.373 12 12 12h8c6.627 0 12-5.373 12-12V378.398c31.423-14.539 72.066-29.064 135.652-29.064 56.606 0 101.902 34.667 171.826 34.667 51.31 0 91.933-17.238 130.008-42.953 6.589-4.45 10.514-11.909 10.514-19.86V59.521c0-17.549-18.206-29.152-34.122-21.76-36.78 17.084-86.263 36.906-133.53 36.906zM48 28c11.028 0 20 8.972 20 20s-8.972 20-20 20-20-8.972-20-20 8.972-20 20-20zm432 289.333C456.883 334.03 415.452 352 371.478 352c-63.615 0-108.247-34.667-171.826-34.667-46.016 0-102.279 10.186-135.652 26V106.667C87.117 89.971 128.548 72 172.522 72c63.615 0 108.247 34.667 171.826 34.667 45.92 0 102.217-18.813 135.652-34.667v245.333z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-book">
        <svg viewBox="0 0 576 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="book-open" data-prefix="fal" id="ember314" class="pointer-events-none svg-inline--fa fa-book-open fa-w-18 ember-view"><path fill="currentColor" d="M514.91 32h-.16c-24.08.12-144.75 8.83-219.56 48.09-4.05 2.12-10.33 2.12-14.38 0C205.99 40.83 85.32 32.12 61.25 32h-.16C27.4 32 0 58.47 0 91.01v296.7c0 31.41 25.41 57.28 57.85 58.9 34.77 1.76 122.03 8.26 181.89 30.37 5.27 1.95 10.64 3.02 16.25 3.02h64c5.62 0 10.99-1.08 16.26-3.02 59.87-22.11 147.12-28.61 181.92-30.37 32.41-1.62 57.82-27.48 57.82-58.89V91.01C576 58.47 548.6 32 514.91 32zM272 433c0 8.61-7.14 15.13-15.26 15.13-1.77 0-3.59-.31-5.39-.98-62.45-23.21-148.99-30.33-191.91-32.51-15.39-.77-27.44-12.6-27.44-26.93V91.01c0-14.89 13.06-27 29.09-27 19.28.1 122.46 7.38 192.12 38.29 11.26 5 18.64 15.75 18.66 27.84l.13 100.32V433zm272-45.29c0 14.33-12.05 26.16-27.45 26.93-42.92 2.18-129.46 9.3-191.91 32.51-1.8.67-3.62.98-5.39.98-8.11 0-15.26-6.52-15.26-15.13V230.46l.13-100.32c.01-12.09 7.4-22.84 18.66-27.84 69.66-30.91 172.84-38.19 192.12-38.29 16.03 0 29.09 12.11 29.09 27v296.7z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-book-closed">
        <svg viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="book" data-prefix="fal" id="ember349" class="svg-inline--fa fa-book fa-w-14 ember-view"><path fill="currentColor" d="M356 160H188c-6.6 0-12-5.4-12-12v-8c0-6.6 5.4-12 12-12h168c6.6 0 12 5.4 12 12v8c0 6.6-5.4 12-12 12zm12 52v-8c0-6.6-5.4-12-12-12H188c-6.6 0-12 5.4-12 12v8c0 6.6 5.4 12 12 12h168c6.6 0 12-5.4 12-12zm64.7 268h3.3c6.6 0 12 5.4 12 12v8c0 6.6-5.4 12-12 12H80c-44.2 0-80-35.8-80-80V80C0 35.8 35.8 0 80 0h344c13.3 0 24 10.7 24 24v368c0 10-6.2 18.6-14.9 22.2-3.6 16.1-4.4 45.6-.4 65.8zM128 384h288V32H128v352zm-96 16c13.4-10 30-16 48-16h16V32H80c-26.5 0-48 21.5-48 48v320zm372.3 80c-3.1-20.4-2.9-45.2 0-64H80c-64 0-64 64 0 64h324.3z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-link">
        <svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="link" data-prefix="fal" id="ember280" class="pointer-events-none svg-inline--fa fa-link fa-w-16 ember-view"><path fill="currentColor" d="M301.148 394.702l-79.2 79.19c-50.778 50.799-133.037 50.824-183.84 0-50.799-50.778-50.824-133.037 0-183.84l79.19-79.2a132.833 132.833 0 0 1 3.532-3.403c7.55-7.005 19.795-2.004 20.208 8.286.193 4.807.598 9.607 1.216 14.384.481 3.717-.746 7.447-3.397 10.096-16.48 16.469-75.142 75.128-75.3 75.286-36.738 36.759-36.731 96.188 0 132.94 36.759 36.738 96.188 36.731 132.94 0l79.2-79.2.36-.36c36.301-36.672 36.14-96.07-.37-132.58-8.214-8.214-17.577-14.58-27.585-19.109-4.566-2.066-7.426-6.667-7.134-11.67a62.197 62.197 0 0 1 2.826-15.259c2.103-6.601 9.531-9.961 15.919-7.28 15.073 6.324 29.187 15.62 41.435 27.868 50.688 50.689 50.679 133.17 0 183.851zm-90.296-93.554c12.248 12.248 26.362 21.544 41.435 27.868 6.388 2.68 13.816-.68 15.919-7.28a62.197 62.197 0 0 0 2.826-15.259c.292-5.003-2.569-9.604-7.134-11.67-10.008-4.528-19.371-10.894-27.585-19.109-36.51-36.51-36.671-95.908-.37-132.58l.36-.36 79.2-79.2c36.752-36.731 96.181-36.738 132.94 0 36.731 36.752 36.738 96.181 0 132.94-.157.157-58.819 58.817-75.3 75.286-2.651 2.65-3.878 6.379-3.397 10.096a163.156 163.156 0 0 1 1.216 14.384c.413 10.291 12.659 15.291 20.208 8.286a131.324 131.324 0 0 0 3.532-3.403l79.19-79.2c50.824-50.803 50.799-133.062 0-183.84-50.802-50.824-133.062-50.799-183.84 0l-79.2 79.19c-50.679 50.682-50.688 133.163 0 183.851z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-language">
        <svg viewBox="0 0 640 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="language" data-prefix="fal" id="ember323" class="svg-inline--fa fa-language fa-w-20 ember-view"><path fill="currentColor" d="M616 96H24c-13.255 0-24 10.745-24 24v272c0 13.255 10.745 24 24 24h592c13.255 0 24-10.745 24-24V120c0-13.255-10.745-24-24-24zM304 384H32V128h272v256zm304 0H336V128h272v256zM91.088 352h10.34a12 12 0 0 0 11.397-8.243l13.508-40.973h67.335l13.508 40.973A12.001 12.001 0 0 0 218.573 352h10.339c8.276 0 14.067-8.18 11.319-15.985l-59.155-168A12 12 0 0 0 169.757 160h-19.513a12 12 0 0 0-11.319 8.014l-59.155 168C77.021 343.82 82.812 352 91.088 352zm60.663-128.991c3.787-10.818 8.113-29.747 8.113-29.747h.541s4.057 18.929 7.572 29.747l17.036 51.38h-50.298l17.036-51.38zM384 212v-8c0-6.627 5.373-12 12-12h68v-20c0-6.627 5.373-12 12-12h8c6.627 0 12 5.373 12 12v20h68c6.627 0 12 5.373 12 12v8c0 6.627-5.373 12-12 12h-15.699c-7.505 24.802-23.432 50.942-44.896 74.842 10.013 9.083 20.475 17.265 30.924 24.086 5.312 3.467 6.987 10.475 3.84 15.982l-3.987 6.976c-3.429 6.001-11.188 7.844-16.993 4.091-13.145-8.5-25.396-18.237-36.56-28.5-11.744 10.454-24.506 20.146-37.992 28.68-5.761 3.646-13.409 1.698-16.791-4.221l-3.972-6.95c-3.197-5.594-1.379-12.672 4.058-16.129 11.382-7.237 22.22-15.428 32.24-24.227-10.026-11.272-18.671-22.562-25.687-33.033-3.833-5.721-2.11-13.48 3.803-17.01l6.867-4.099c5.469-3.264 12.55-1.701 16.092 3.592 6.379 9.531 13.719 18.947 21.677 27.953 15.017-16.935 26.721-34.905 33.549-52.033H396c-6.627 0-12-5.373-12-12z"></path>
        </svg>
    </xsl:variable>
    <xsl:variable name="fa-question">
        <svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" role="img" focusable="false" aria-hidden="true" data-icon="question-circle" data-prefix="fal" id="ember280" class="svg-inline--fa fa-question-circle fa-w-16 ember-view"><path fill="currentColor" d="M256 340c-15.464 0-28 12.536-28 28s12.536 28 28 28 28-12.536 28-28-12.536-28-28-28zm7.67-24h-16c-6.627 0-12-5.373-12-12v-.381c0-70.343 77.44-63.619 77.44-107.408 0-20.016-17.761-40.211-57.44-40.211-29.144 0-44.265 9.649-59.211 28.692-3.908 4.98-11.054 5.995-16.248 2.376l-13.134-9.15c-5.625-3.919-6.86-11.771-2.645-17.177C185.658 133.514 210.842 116 255.67 116c52.32 0 97.44 29.751 97.44 80.211 0 67.414-77.44 63.849-77.44 107.408V304c0 6.627-5.373 12-12 12zM256 40c118.621 0 216 96.075 216 216 0 119.291-96.61 216-216 216-119.244 0-216-96.562-216-216 0-119.203 96.602-216 216-216m0-32C119.043 8 8 119.083 8 256c0 136.997 111.043 248 248 248s248-111.003 248-248C504 119.083 392.957 8 256 8z"></path>
        </svg>
    </xsl:variable>

    <!-- Keys -->

    <!-- To reduce dependency on a DTD for processing, we declare
         a key to use instead of the id() function. -->
    <xsl:key name="element-by-id" match="*[@id]" use="@id"/>

    <!-- Enabling retrieval of cross-references to objects -->
    <xsl:key name="xref-by-rid" match="xref" use="@rid"/>

    <xsl:key name="role" match="artauth/aut" use="@role" />

    <xsl:key name="affid" match="artauth/aut" use="@affid" />

    <!-- ============================================================= -->
    <!--  ROOT TEMPLATE - HANDLES HTML FRAMEWORK                       -->
    <!-- ============================================================= -->

  <xsl:template match="/">
    <xsl:text disable-output-escaping='yes'>&lt;!DOCTYPE html&gt;</xsl:text>
    <xsl:text>&#13;</xsl:text>
    <html>
      <!-- HTML header -->
      <xsl:call-template name="make-html-header"/>
      <!--      <xsl:call-template name="make-article"/>-->
      <xsl:apply-templates/>
      <div id="putciteashere"></div>
    </html>
  </xsl:template>

  <xsl:template name="make-html-header">
    <head>
      <title class="head title">
        <xsl:variable name="authors">
          <xsl:call-template name="author-string"/>
        </xsl:variable>
        <xsl:value-of select="normalize-space(string($authors))"/>
        <xsl:if test="normalize-space(string($authors))">: </xsl:if>
        <xsl:value-of select="pepkbd3/artinfo/arttitle"/>
      </title>
      <!-- <link rel="stylesheet" type="text/css" href="{$css}"></link>-->
      <!--<link rel="stylesheet" type="text/css" href="{$css2}"></link>-->
      <!--<link rel="stylesheet" type="text/css" href="{$css3}"></link>-->
      <!--<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/fork-awesome@1.2.0/css/fork-awesome.min.css" integrity="sha256-XoaMnoYC5TH6/+ihMEnospgm0J1PM/nioxbOUdnM8HY=" crossorigin="anonymous"></link>-->
      <!-- When importing jats-oasis-html.xsl, we can call a template to insert CSS for our tables. -->
      <!--<xsl:call-template name="p:table-css" xmlns:p="http://www.wendellpiez.com/oasis-tables/util"/>-->
    </head>
  </xsl:template>
    <xsl:template name="data-pagehelper">
        <!-- If the previous element is a page break, add the data attribute page-start and give it a value of the next page break  -->
        <xsl:if test="name(preceding-sibling::*[1])='pb'">
            <xsl:attribute name="data-page-start">
                <!-- For padding the numbers - pick a string that is large enough that we will never need to pad that much (I think 5 characters would have been fine, but it doesn't hurt to have more) -->
                <xsl:variable name="zero-string" select="'00000000000000000000000000000000000'" />
                <!-- Select the next page number for the current page -->
                <xsl:variable name="next-page-number-string" select="following-sibling::pb/n/@nextpgnum" />
                <!-- Remove the numbers from it -ex. PR0004 becomes PR -->
                <xsl:variable name="next-page-number-letters" select="translate($next-page-number-string, '0123456789', '')" />
                <!-- Remove the letters from the next page string -ex. PR0004 becomes 0004 -->
                <xsl:variable name="next-page-number-string-translated" select="translate($next-page-number-string, $next-page-number-letters, '')" />
                <!-- Get the length of that string - so 4 -->
                <xsl:variable name="next-page-number-string-length" select="string-length($next-page-number-string-translated)" />
                <!-- Generate a string of padded zeros however long the next-page-number-string is i.e 4 -->
                <xsl:variable name="padded-zeros" select="substring($zero-string, 0, $next-page-number-string-length + 1)"/>
                <!-- Translate next-page-number-string-translated to a number ex. 0004 now becomes 4 -->
                <xsl:variable name="next-page-number-value" select="number($next-page-number-string-translated)" />
                <!-- Subtract 1 to get the current page number (in this example it would be 3) -->
                <xsl:variable name="page-number-value" select="number($next-page-number-value - 1)" />
                <!-- Padd the current page number with the appropriate number of zeros (in this example 0003)  -->
                <xsl:variable name="page-number-string" select="substring(concat($padded-zeros, $page-number-value), string-length($page-number-value) + 1, string-length($padded-zeros))" />
                <!-- Combine the letters from before with the new page number PR0003 and that is our correct current page value -->
                <xsl:value-of select="concat($next-page-number-letters, $page-number-string)" />
            </xsl:attribute>
        </xsl:if>
        <!-- If there is no preceding sibling i.e. its the first element, grab the first page break value and put it into the data attribute -->
        <xsl:if test="not(preceding-sibling::*)">
            <xsl:attribute name="data-page-start">
                <!-- For padding the numbers - pick a string that is large enough that we will never need to pad that much (I think 5 characters would have been fine, but it doesn't hurt to have more) -->
                <xsl:variable name="zero-string" select="'00000000000000000000000000000000000'" />
                <!-- Select the next page number for the current page -->
                <xsl:variable name="next-page-number-string" select="../following-sibling::pb/n/@nextpgnum" />
                <!-- Remove the numbers from it -ex. PR0004 becomes PR -->
                <xsl:variable name="next-page-number-letters" select="translate($next-page-number-string, '0123456789', '')" />
                <!-- Remove the letters from the next page string -ex. PR0004 becomes 0004 -->
                <xsl:variable name="next-page-number-string-translated" select="translate($next-page-number-string, $next-page-number-letters, '')" />
                <!-- Get the length of that string - so 4 -->
                <xsl:variable name="next-page-number-string-length" select="string-length($next-page-number-string-translated)" />
                <!-- Generate a string of padded zeros however long the next-page-number-string is i.e 4 -->
                <xsl:variable name="padded-zeros" select="substring($zero-string, 0, $next-page-number-string-length + 1)"/>
                <!-- Translate next-page-number-string-translated to a number ex. 0004 now becomes 4 -->
                <xsl:variable name="next-page-number-value" select="number($next-page-number-string-translated)" />
                <!-- Subtract 1 to get the current page number (in this example it would be 3) -->
                <xsl:variable name="page-number-value" select="number($next-page-number-value - 1)" />
                <!-- Padd the current page number with the appropriate number of zeros (in this example 0003)  -->
                <xsl:variable name="page-number-string" select="substring(concat($padded-zeros, $page-number-value), string-length($page-number-value) + 1, string-length($padded-zeros))" />
                <!-- Combine the letters from before with the new page number PR0003 and that is our correct current page value -->
                <xsl:value-of select="concat($next-page-number-letters, $page-number-string)" />
            </xsl:attribute>
        </xsl:if>
    </xsl:template>


    <!-- ============================================================= -->
    <!--  TOP LEVEL                                                    -->
    <!-- ============================================================= -->
    
    <!--Global Variables-->
    <!--  used with translate to convert between case, since this is for XSLT 1.0 -->
    <xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz'" />
    <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />
    <!--  <xsl:variable name="baseurl">www.pep-web.org</xsl:variable>-->
    <xsl:variable name="artgraphfolder">g</xsl:variable>
    <xsl:variable name="document-id">
        <xsl:apply-templates select="//artinfo/@id"/>
    </xsl:variable>
    <xsl:variable name="journal-code">
        <xsl:apply-templates select="//artinfo/@j"/>
    </xsl:variable>
    <xsl:variable name="artvol">
        <xsl:apply-templates select="//artinfo/artvol"/>
    </xsl:variable>
    <xsl:variable name="artpgrg">
        <xsl:apply-templates select="//artinfo/artpgrg"/>
    </xsl:variable>
    <xsl:variable name="artstartpg">
        <xsl:value-of select="substring-before(($artpgrg), '-')"/>
    </xsl:variable>

    <xsl:template match="pepkbd3">
        <body>
            <div class="pepkbd3" data-ver="2021-09-26.FULL">
                <xsl:call-template name="assign-lang"/>
                <xsl:call-template name="make-article"/>
            </div>
        </body>
    </xsl:template>

    <!-- ============================================================= -->
    <!--  "make-article" for the document architecture                 -->
    <!-- ============================================================= -->
    <xsl:template name="make-article">
        <!-- variable to be used in div id's to keep them unique -->
        <xsl:variable name="this-article">
            <xsl:apply-templates select="." mode="id"/>
        </xsl:variable>

        <div id="front" class="frontmatter">
            <xsl:apply-templates select="front | front-stub" mode="metadata"/>
            <p class="banner d-flex ">


                <a class="toc-link" data-journal-code="{$journal-code}">
                    <xsl:choose>
                        <xsl:when test="$isBook">
                            <xsl:attribute name="href"></xsl:attribute>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:attribute name="href">/browse/journal/{$journal-code}/volumes</xsl:attribute>
                        </xsl:otherwise>
                    </xsl:choose>
                    <img class="img-fluid">
                        <xsl:attribute name="data-type">document-banner</xsl:attribute>
                        <xsl:attribute name="src">
                            <xsl:value-of select="concat($imageUrl, 'banner', $journal-code, 'Logo.gif')"/>
                        </xsl:attribute>
<!--                        <xsl:attribute name="data-image">
                            <xsl:value-of select="concat($imageUrl, 'banner', $journal-code, 'Logo.gif')"/>
                        </xsl:attribute>
-->                        <xsl:attribute name="alt">Journal Logo</xsl:attribute>
                    </img>
                </a>


            </p>
            <div class="pubinfotop small">
                <xsl:for-each select="artinfo">
                    <span class="mr-1">(<xsl:apply-templates select="artyear" mode="text"/>).</span>
                    <span class="mr-1"><xsl:value-of select="$journalName" />,</span>
                    <span><xsl:apply-templates mode="text" select="artvol"/></span>
                    <span>(<xsl:apply-templates mode="text" select="artiss"/>)</span>
                    <span>:<xsl:apply-templates mode="text" select="artpgrg"/></span>
                </xsl:for-each>
            </div>



            <xsl:for-each select="artinfo">
                <div id="{$this-article}-artinfo" class="artinfo" data-arttype="{@arttype}" data-journal="{@j}">

                    <xsl:if test="artsectinfo">
                        <div class="section-title section-title border-bottom my-2">
                            <xsl:apply-templates mode="metadata" select="artsectinfo" />
                        </div>
                    </xsl:if>
                    <div class="art-title mt-3 text-center">
                        <span>
                            <a href="/browse/{$journal-code}/volumes/{$artvol}?page={$artstartpg}"
                               data-journal-code="{$journal-code}"
                               data-volume="{$artvol}"
                               data-page="{$artstartpg}"
                               data-type="document-title"
                                >
                                <xsl:apply-templates mode="metadata" select="arttitle" />
                                <xsl:apply-templates mode="metadata" select="artsub"/>
                            </a>
                            <xsl:apply-templates select="arttitle/ftnx" />
                            <xsl:apply-templates select="artsub/ftnx" />
                        </span>

                    </div>

                    <xsl:apply-templates mode="metadata" select="artauth"/>


                    <!--<xsl:apply-templates/>-->
                </div>
            </xsl:for-each>
        </div>

        <!-- tagline -->
        <xsl:for-each select="tagline">
            <div id="{$this-article}-tagline" class="tagline">
                <xsl:apply-templates/>
            </div>
        </xsl:for-each>


        <!-- abs -->
        <xsl:for-each select="abs">
            <div id="{$this-article}-abs" class="abs abstract text-muted mx-5">
                <xsl:apply-templates/>
            </div>
        </xsl:for-each>

        <div class="keywords mx-5 mt-2 mb-4">
            <xsl:for-each select="artinfo">
                <xsl:apply-templates mode="metadata" select="artkwds"/>
            </xsl:for-each>
        </div>

        <!-- body -->
        <xsl:for-each select="body">
            <div id="body" class="body">
                <xsl:call-template name="assign-lang"/>
                <xsl:apply-templates/>
                <!-- If the body is empty AND there is a preview attribute on the artinfo tag it means we need to show a video preview -->
                <xsl:if test="not(node()) and ../artinfo/@preview != ''">
                    <xsl:variable name="videoUrl" select="concat('https://pep-web-video-previews.s3.amazonaws.com/', ../artinfo/@preview, '.mp4')"/>
                    <xsl:variable name="captionUrl" select="concat('https://pep-web-video-previews.s3.amazonaws.com/', ../artinfo/@preview, '.vtt')"/>
                    <xsl:variable name="posterUrl" select="concat('https://pep-web-video-previews.s3.amazonaws.com/', ../artinfo/@preview, '.jpg')"/>
                    <div class="embed-responsive embed-responsive-16by9">
                        <video id="clip" controls='controls' preload='auto'  class="embed-responsive-item" crossorigin="anonymous" poster="{$posterUrl}">
                            <source src="{$videoUrl}" type='video/mp4' />
                            <track label="English" kind="subtitles" srclang="en" src="{$captionUrl}" />
                        </video>
                    </div>
                </xsl:if>
            </div>
        </xsl:for-each>

        <!-- summaries -->
        <xsl:for-each select="summaries">
            <div id="{$this-article}-summaries" class="summaries">
                <xsl:call-template name="data-pagehelper"/>
                <xsl:call-template name="assign-lang"/>
                <xsl:apply-templates/>
            </div>
        </xsl:for-each>

        <!-- body -->
        <xsl:for-each select="bib">
            <div id="{$this-article}-bib" class="biblio">
                <xsl:apply-templates/>
            </div>
        </xsl:for-each>

        <xsl:for-each select="idx">
            <div id="{$this-article}-idx" class="idx">
                <xsl:apply-templates/>
            </div>
        </xsl:for-each>


        <xsl:for-each select="appxs">
            <div id="{$this-article}-appendix" class="appendix">
                <xsl:apply-templates/>
            </div>
        </xsl:for-each>


    </xsl:template>

    <!-- ============================================================= -->
    <!--  "artinfo" for the document metadata                          -->
    <!-- ============================================================= -->
    <xsl:template match="artinfo">
        <!-- First: journal and article metadata -->
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
                <div class="metadata two-column table nrsmbee">
                    <div class="row">
                        <div class="cell empty"/>
                        <div class="cell">
                            <div class="metadata-group">
                                <xsl:apply-templates mode="metadata" select="aff | aff-alternatives | author-notes"/>
                            </div>
                        </div>
                    </div>
                </div>
            </xsl:if>

            <!-- end of dealing with abstracts -->
        </xsl:for-each>
        <xsl:for-each select="notes">
            <div class="metadata">
                <xsl:apply-templates mode="metadata" select="."/>
            </div>
        </xsl:for-each>
        <!-- end of big front-matter pull -->
    </xsl:template>

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

    <xsl:template match="journalname" mode="metadata">
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
        <span class="title pointer-events-none">
            <xsl:choose>
                <xsl:when test="text()">
                    <xsl:apply-templates select="(node())[not(self::ftnx)]"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates/>
                </xsl:otherwise>
            </xsl:choose>
            <!-- <xsl:apply-templates select="ftnx" mode="title"/> -->
        </span>
    </xsl:template>

    <xsl:template match="artsectinfo" mode="metadata">
        <span class="section-title" data-type="section-title">
            <xsl:choose>
                <xsl:when test="text()">
                    <xsl:apply-templates select="(node())[not(self::ftnx)]"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates/>
                </xsl:otherwise>
            </xsl:choose>
            <!-- <xsl:apply-templates select="ftnx" mode="title"/> -->
        </span>
    </xsl:template>

    <xsl:template match="artsub" mode="metadata">
        <span class="artsub pointer-events-none">&#58;
            <xsl:choose>
                <xsl:when test="text()">
                    <xsl:apply-templates select="(node())[not(self::ftnx)]"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates/>
                </xsl:otherwise>
            </xsl:choose>
            <!-- <xsl:apply-templates select="ftnx" mode="title"/> -->
        </span>
    </xsl:template>

    <xsl:template match="artkwds" mode="metadata">
        <div class="artkwds mb-2">
            <strong class="mr-1">
                Keywords:
            </strong>
            <xsl:for-each select="//impx[@type='KEYWORD']">
                <a class="keyword" >
                    <xsl:attribute name="data-type">
                        <xsl:value-of select="@type"/>
                    </xsl:attribute>
                    <xsl:attribute name="data-keyword">
                        <xsl:value-of select="."/>
                    </xsl:attribute>
                    <xsl:value-of select="."/>
                    <xsl:if test="position() != last()">
                        <xsl:text>, </xsl:text>
                    </xsl:if>
                </a>
            </xsl:for-each>
        </div>
    </xsl:template>

    <xsl:template match="artauth" mode="metadata">
        <div class="artauth">
            <div class="authorwrapper title-author text-center" data-class="artauth">
                <xsl:variable name="by-role" select="aut[generate-id(.)=generate-id(key('role',@role)[1])]"/>

                <xsl:apply-templates select="$by-role" mode="metadata" />

            </div>
        </div>
    </xsl:template>

    <xsl:template match="autaff" mode="metadata">
        <div data-class="autaff">
            <xsl:if test="@affid">
                <xsl:attribute name="data-affid">
                    <xsl:value-of select="@affid"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates mode="metadata" select="addr"/>
        </div>
    </xsl:template>

    <!--PEPKBD3 Author Information-->
    <!-- Documents needed to test the roles correctly
         AJP.063.0149A [3 authors, 1 autaff, no affid] = 3 authors, 1 autaff
         ZBK.061.0001A [2 authors, 10 in-collaboration, 2 translated by, 1 forwarded by, 3 autaff, 3 affids] = show 2 authors with autaff, 10 collabs, 2 translated by with autaff and 1 forwarwd by
         RFP.053.1405A [1 author, 1 autaff, no affid] = show 1 author and 1 autaff
    -->
    <xsl:template match="artauth/aut" mode="metadata">

        <div class="author-grouping" data-grouping="{@role}">
            <xsl:if test="@role != 'author'">
                <div>
                    <xsl:choose>
                        <xsl:when test="@role = 'additional-cinematography-by'" >
                            Additional Cinematography by:
                        </xsl:when>
                        <xsl:when test="@role = 'assisted-by'" >
                            Assisted by:
                        </xsl:when>
                        <xsl:when test="@role = 'coordinator'">
                            Coordinated by:
                        </xsl:when>
                        <xsl:when test="@role = 'chaired-by'" >
                            Chaired by:
                        </xsl:when>
                        <xsl:when test="@role = 'compiled-by'" >
                            Compiled by:
                        </xsl:when>
                        <xsl:when test="@role = 'commentary-by'" >
                            Commentary by:
                        </xsl:when>
                        <xsl:when test="@role = 'director'" >
                            Directed by:
                        </xsl:when>
                        <xsl:when test="@role = 'director-and-producer'" >
                            Directed and produced by:
                        </xsl:when>
                        <xsl:when test="@role = 'director-assistant'" >
                            Director's Assistants:
                        </xsl:when>
                        <xsl:when test="@role = 'deputy-editor'" >
                            Deputy Editor:
                        </xsl:when>
                        <xsl:when test="@role = 'editorial-assistant'" >
                            Editorial assistance by:
                        </xsl:when>

                        <xsl:when test="@role = 'editor-in-chief'" >
                            Editor in chief:
                        </xsl:when>
                        <xsl:when test="@role = 'edited-by'">
                            Edited by:
                        </xsl:when>
                        <xsl:when test="@role = 'excerpted-by'">
                            Excerpt by:
                        </xsl:when>
                        <xsl:when test="@role = 'executive-producer'">
                            Executive Producer:
                        </xsl:when>
                        <xsl:when test="@role = 'assistant-producer'">
                            Assistant Producer:
                        </xsl:when>
                        <xsl:when test="@role = 'associate-producer'">
                            Associate Producer:
                        </xsl:when>

                        <xsl:when test="@role = 'in-collaboration'">
                            In Collaboration with:
                        </xsl:when>
                        <xsl:when test="@role = 'interviewer'">
                            Interviewer:
                        </xsl:when>
                        <xsl:when test="@role = 'interviewee'">
                            Interviewee:
                        </xsl:when>
                        <xsl:when test="@role = 'intro'">
                            Introduction by:
                        </xsl:when>
                        <xsl:when test="@role = 'issue-editor'">
                            Issue editor:
                        </xsl:when>
                        <xsl:when test="@role = 'line-producer'">
                            Line producer:
                        </xsl:when>

                        <xsl:when test="@role = 'moderator'">
                            Moderated by:
                        </xsl:when>
                        <xsl:when test="@role = 'narrated-by'">
                            Narrated by:
                        </xsl:when>
                        <xsl:when test="@role = 'panelist'">
                            Panelist:
                        </xsl:when>
                        <xsl:when test="@role = 'preface'">
                            Preface:
                        </xsl:when>

                        <xsl:when test="@role = 'presenter'">
                            Presented by:
                        </xsl:when>
                        <xsl:when test="@role = 'published-by'">
                            Published by:
                        </xsl:when>
                        <xsl:when test="@role = 'produced-by'">
                            Produced by:
                        </xsl:when>
                        <xsl:when test="@role = 'reporter'">
                            Reported by:
                        </xsl:when>

                        <xsl:when test="@role = 'reviewer'">
                            Reviewed by:
                        </xsl:when>
                        <xsl:when test="@role = 'series-editor'">
                            Series edited by:
                        </xsl:when>
                        <xsl:when test="@role = 'translator'">
                            Translated by:
                        </xsl:when>
                        <xsl:when test="@role = 'transcribed-by'">
                            Transcribed by:
                        </xsl:when>
                        <xsl:when test="@role = 'under-supervision-of'">
                            Under supervision of:
                        </xsl:when>
                        <xsl:when test="@role = 'other'">
                            <xsl:value-of select="@other" />:
                        </xsl:when>

                    </xsl:choose>
                </div>
            </xsl:if>

            <xsl:for-each select="key('role', @role)">
                <span class="title-author" data-listed="{@listed}" data-authindexid="{@authindexid}" data-role="{@role}" data-alias="{@alias}" data-asis="{@asis}">
                    <a class="author" href="#/Search/?author={@authindexid}" data-type="search-author">
                        <xsl:apply-templates mode="metadata" select="nfirst"/>
                        <xsl:apply-templates mode="metadata" select="nlast"/>
                    </a>
                    <xsl:apply-templates mode="metadata" select="ndeg"/>
                    <xsl:choose>
                        <xsl:when test="position() = last() -1 ">
                            <xsl:text> and </xsl:text>
                        </xsl:when>
                        <xsl:when test="position() = last()">
                            <xsl:text></xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>, </xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </span>
                <xsl:text>&#13;</xsl:text>
            </xsl:for-each>

            <xsl:choose>
                <xsl:when test="current()[@affid!=''] or current()/nbio" >
                    <xsl:text> </xsl:text>
                    <a class="peppopup authortip" href="#author-information">
                        <xsl:copy-of select="$fa-information" />
                        <xsl:text></xsl:text>
                        <br></br>
                        <div class="peppopuptext" hidden="True" role="dialog">
                            <div class="autcontent">
                                <xsl:for-each select="key('role', @role)">
                                    <div class="author-information">
                                        <p class="autaffname">
                                            <xsl:apply-templates mode="metadata" select="nfirst"/>
                                            <xsl:apply-templates mode="metadata" select="nlast"/>
                                        </p>
                                        <xsl:apply-templates mode="metadata" select="../autaff[@affid=current()/@affid]"/>
                                        <xsl:apply-templates mode="metadata" select="nbio"/>
                                    </div>
                                </xsl:for-each>
                            </div>
                        </div>
                    </a>
                </xsl:when>

                <xsl:when test="count(../autaff) = 1">
                    <xsl:text> </xsl:text>
                    <a class="peppopup authortip" href="#author-information">
                        <xsl:copy-of select="$fa-information" />
                        <xsl:text></xsl:text>
                        <br></br>

                        <div class="peppopuptext" hidden="True" role="dialog">

                            <div class="autcontent">
                                <xsl:for-each select="key('role', @role)">
                                    <div class="author-information">
                                        <p class="autaffname">
                                            <xsl:apply-templates mode="metadata" select="nfirst"/>
                                            <xsl:apply-templates mode="metadata" select="nlast"/>
                                        </p>
                                        <xsl:apply-templates mode="metadata" select="nbio"/>
                                    </div>
                                </xsl:for-each>
                                <xsl:apply-templates mode="metadata" select="../autaff"/>
                            </div>
                        </div>
                    </a>
                </xsl:when>
                <xsl:when test="@role = 'author'">
                    <xsl:text> </xsl:text>
                    <a class="peppopup newauthortip" href="#new-author-information">
                        <xsl:copy-of select="$fa-information" />
                        <br></br>
                        <xsl:text>&#xa;</xsl:text>
                        <div class="peppopuptext" id="autaffinfo" hidden="True" role="dialog">
                            <div id="autcontent" class="autcontent">
                                <p class="autaffname">
                                    <xsl:apply-templates mode="metadata" select="nfirst"/>
                                    <xsl:apply-templates mode="metadata" select="nlast"/>
                                </p>
                                <xsl:apply-templates mode="metadata" select="nbio"/>
                            </div>
                        </div>
                    </a>
                </xsl:when>
            </xsl:choose>
        </div>
    </xsl:template>

    <xsl:template match="ln" mode="metadata">
        <span data-class="ln">
            <xsl:apply-templates/><br/>
        </span>
    </xsl:template>

    <xsl:template match="addr" mode="metadata">
        <p class="autaffaddr" data-class="addr">
            <xsl:apply-templates mode="metadata"/>
        </p>
    </xsl:template>

    <xsl:template match="nbio" mode="metadata">
        <span data-class="nbio">
            <xsl:apply-templates mode="metadata"/>
        </span>
    </xsl:template>

    <xsl:template match="webx">
        <xsl:choose>
            <xsl:when test="@type">
                <a class="webx" data-type="{@type}" data-url="{@url}" target="_blank" href="{@url}">
                    <xsl:value-of select="."/>
                </a>
            </xsl:when>
            <xsl:otherwise>
                <a class="webx" data-type="web-link" data-url="{@url}" target="_blank" href="{@url}">
                    <xsl:value-of select="."/>
                </a>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="hdix">
        <a class="hdix" data-type="pagelink" target="_blank" href="?target={@r}" data-r="{@r}">
            <xsl:apply-templates/>
        </a>
    </xsl:template>

    <xsl:template match="cr">
        <br/>
    </xsl:template>

    <xsl:template match="nfirst" mode="metadata">
        <xsl:text>&#10;</xsl:text> <!-- newline character -->
        <span class="nfirst pointer-events-none" data-type="{@type}" data-initials="{@initials}">
            <xsl:value-of select="."/>
        </span>
        <xsl:text> </xsl:text> <!-- space character -->
    </xsl:template>


    <xsl:template match="nlast" mode="metadata">
        <span class="nlast pointer-events-none">
            <xsl:value-of select="."/>
        </span>
    </xsl:template>


    <xsl:template match="ndeg" mode="metadata">

        <xsl:variable name="phdBefore" select="'PHD'" />
        <xsl:variable name="phdAfter" select="'PhD'" />
        <xsl:choose>
            <xsl:when test="@other"> <!-- then i test if the attr exists -->
                <span class="ndeg" data-dgr="{@dgr}" data-other="{@other}">
                    <xsl:text> </xsl:text> <!-- space character -->
                    <xsl:value-of select="@other"/>
                </span>
            </xsl:when>
            <xsl:otherwise>
                <span class="ndeg" data-dgr="{@dgr}" data-other="{@other}">
                    <xsl:text> </xsl:text> <!-- space character -->
                    <xsl:value-of select="translate(@dgr, $phdBefore, $phdAfter)"/>
                </span>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text> </xsl:text> <!-- space character -->
    </xsl:template>

    <xsl:template match="videoplayer">
        <xsl:if test="'1'='1'">
            <!--This is the new Wistia player-\-it allows seeking in the transcript, press the arrow on the captions, or use the "Search Video" on the cc menu.
                 This works for old and new videos!
            -->
            <div class="wistia_responsive_padding" style="padding:56.25% 0 0 0;position:relative;">
                <div class="wistia_responsive_wrapper" style="height:100%;left:0;position:absolute;top:0;width:100%;">
                    <iframe src="https://fast.wistia.net/embed/iframe/{@videoid}?videoFoam=true" allowtransparency="true" frameborder="0" scrolling="no" class="wistia_embed" name="wistia_embed" width="100%" height="100%" allowfullscreen="allowfullscreen" mozallowfullscreen="mozallowfullscreen" webkitallowfullscreen="webkitallowfullscreen" oallowfullscreen="oallowfullscreen" msallowfullscreen="msallowfullscreen"></iframe></div>
            </div>
            <script src="https://fast.wistia.net/assets/external/E-v1.js" async="async"></script>
        </xsl:if>
    </xsl:template>

    <xsl:template match="pgx">
        <span class="pgx" data-type="pagelink" data-r="{@rx}">
            <a class="pgx" href="#/Document/{@rx}" data-type="pagelink" data-r="{@rx}">
                <xsl:value-of select="."/>
            </a>
        </span>
    </xsl:template>


    <xsl:template match="bxe">
        <span class="bxe" data-type="pagelink" data-r="{@rx}">
            <a class="bxe" href="#/Document/{@rx}" data-type="pagelink" data-r="{@rx}">
                <xsl:value-of select="."/>
            </a>
        </span>
    </xsl:template>


    <xsl:template match="xref" mode="metadata-inline">
        <!-- These are not expected to appear in mixed content, so
             brackets are provided -->
        <span class="generated">[</span>
        <xsl:apply-templates select="."/>
        <span class="generated">]</span>
    </xsl:template>

    <xsl:template match="ftnx">
        <sup>
            <a class="ftnx" data-type="{@type}" data-r="{@r}">
                <xsl:value-of select="."/>
            </a>
        </sup>
    </xsl:template>

    <xsl:template match="ftnx" mode="title">
        <sup>
            <span class="ftnx" data-type="{@type}" data-r="{@r}">
                <xsl:value-of select="."/>
            </span>
        </sup>
    </xsl:template>

    <xsl:template match="ftr">
        <xsl:text>&#13;</xsl:text>
        <div class="document-footer pt-1" data-class="ftr">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="ftn">
        <div class="ftn" data-class="ftn_group">
            <xsl:attribute name="id">
                <xsl:value-of select="@id"/>
            </xsl:attribute>
            <span class="ftnlabel">
                <sup>
                    <xsl:value-of select="@label"/>
                </sup>
            </span>
            <xsl:apply-templates />
        </div>
    </xsl:template>

    <xsl:template match="aff" mode="metadata">
        <xsl:call-template name="metadata-entry">
            <xsl:with-param name="contents">
                <xsl:call-template name="named-anchor"/>
                <xsl:apply-templates/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="role" mode="metadata">
        <xsl:call-template name="metadata-entry"/>
    </xsl:template>

    <xsl:template match="title" mode="metadata">
        <xsl:apply-templates select="."/>
    </xsl:template>

    <!-- ============================================================= -->
    <!--  REGULAR (DEFAULT) MODE                                       -->
    <!-- ============================================================= -->

    <!--  Additional author info in document authsectinfo
         Note this works right, but PEP-Easy loads the wrong
         info due to the fixed popup id in javascript
         the
    -->
    <xsl:template match="hauth">
        <div data-class="hauth" class="text-center">
            <xsl:for-each select="aut">
                <a class="author" href="#/Search/?author={@authindexid}" data-type="search-author">
                    <xsl:apply-templates mode="metadata" select="nfirst"/>
                    <xsl:apply-templates mode="metadata" select="nlast"/>
                </a>
                <xsl:apply-templates mode="metadata" select="ndeg"/>
                <xsl:choose>
                    <xsl:when test="position() = last() -1 ">
                        <xsl:text> and </xsl:text>
                    </xsl:when>
                    <xsl:when test="position() != last()">
                        <xsl:text>, </xsl:text>
                    </xsl:when>
                </xsl:choose>
                <xsl:if test="nbio">
                    <xsl:text> </xsl:text>
                    <a class="peppopup authortip" href="#author-bio-information">
                        <xsl:copy-of select="$fa-information" />
                        <xsl:text></xsl:text>
                        <br></br>
                        <div class="peppopuptext" id="autaffinfo" hidden="True" role="dialog">
                            <div id="autcontent" class="autcontent">
                                <p class="autaffname">
                                    <xsl:apply-templates mode="metadata" select="nfirst"/>
                                    <xsl:apply-templates mode="metadata" select="nlast"/>
                                </p>
                                <xsl:apply-templates mode="metadata" select="autaff"/>
                                <p class="autaffbio">
                                    <span class="autaffname" data-class="nbio">
                                        <xsl:apply-templates mode="metadata" select="nfirst"/>
                                        <xsl:apply-templates mode="metadata" select="nlast"/>
                                    </span>
                                    &#160; <!--&nbsp;-->
                                    <xsl:apply-templates mode="metadata" select="nbio"/>
                                </p>
                            </div>
                        </div>
                    </a>
                </xsl:if>
            </xsl:for-each>
        </div>
    </xsl:template>

    <xsl:template match="figure">
        <div class="figure d-flex flex-column" id="{@id}">
            <xsl:call-template name="data-pagehelper"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="ctitle">
      <xsl:if test="not(preceding-sibling::ctitle) and following-sibling::ctitle">
        <span class="fignumber caption">
          <xsl:value-of select="."/>
          <xsl:text>. </xsl:text>
        </span>
      </xsl:if>
      <xsl:if test="(preceding-sibling::ctitle)">
        <span class="figtitle ctitle">
          <xsl:apply-templates/><br/>
        </span>
      </xsl:if>
    </xsl:template>

    <xsl:template match="span[@class='figtitle']">
      <xsl:value-of select="."/>
    </xsl:template>
      
    <xsl:template match="caption">
      <span class="caption">
        <xsl:call-template name="data-pagehelper"/>
        <xsl:apply-templates/>
      </span>
    </xsl:template>   

    <xsl:template match="graphic">
        <xsl:apply-templates/>
        <p class="figure-graphic d-flex justify-content-center">
            <img alt="{@xlink:href}" class="image">
                <xsl:if test="ancestor::figure">
                    <xsl:attribute name="data-type">figure</xsl:attribute>
                </xsl:if>
                <xsl:if test="ancestor::tbl">
                    <xsl:attribute name="data-type">table-figure</xsl:attribute>
                </xsl:if>
                <xsl:for-each select="alt-text">
                    <xsl:attribute name="alt">
                        <xsl:value-of select="normalize-space(string(.))"/>
                    </xsl:attribute>
                </xsl:for-each>
                <xsl:for-each select="@source">
                    <xsl:attribute name="src">
                        <xsl:variable name="image">
                            <xsl:value-of select="."/>
                        </xsl:variable>
                        <!--<xsl:value-of select="concat('g/', $image, '.jpg')"/>-->
                        <!--Use api call to grab image-->
                        <xsl:value-of select="concat($imageUrl, $image)"/>
                        <!--          <xsl:value-of select="."/>-->
                    </xsl:attribute>
                </xsl:for-each>      
            </img>
        </p>
    </xsl:template>

    <xsl:template name="figure-graphic" >
        <p class="figure">
            <img alt="{@xlink:href}" class="img-fluid">
                <xsl:for-each select="alt-text">
                    <xsl:attribute name="alt">
                        <xsl:value-of select="normalize-space(string(.))"/>
                    </xsl:attribute>
                </xsl:for-each>

                <xsl:for-each select="@source">
                    <xsl:attribute name="src">
                        <xsl:variable name="image">
                            <xsl:value-of select="."/>
                        </xsl:variable>
                        <!--<xsl:value-of select="concat('g/', $image, '.jpg')"/>-->
                        <!--Use api call to grab image-->
                        <xsl:value-of select="concat($imageUrl, $image)"/>
                        <!--          <xsl:value-of select="."/>-->
                    </xsl:attribute>
                </xsl:for-each>      

            </img>
        </p>
    </xsl:template>

    <!--
         <xsl:template match="*" mode="drop-title">
         <xsl:apply-templates select="."/>
         </xsl:template>

         <xsl:template match="title | sec-meta" mode="drop-title"/>
    -->




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
            <h3 class="title nrsmbee">
                <xsl:apply-templates/>
            </h3>
        </xsl:if>
    </xsl:template>


    <!--  <xsl:template match="subtitle">
         <xsl:if test="normalize-space(string(.))">
         <h5 class="subtitle">
         <xsl:apply-templates/>
         </h5>
         </xsl:if>
         </xsl:template>
    -->

    <!-- ============================================================= -->
    <!--  Figures, lists and block-level objectS                       -->
    <!-- ============================================================= -->

    <xsl:template match="idxdiv">
        <div class="index-div mb-3">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="idxent">
        <div class="index-item">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="idxent/idxent">
        <div class="index-item ml-4">
            <xsl:apply-templates/>
        </div>
    </xsl:template>



    <!-- abs -->
    <xsl:template match="abs">
        <div id="abs" class="abs">
            <xsl:call-template name="assign-lang"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="h1|h2|h3|h4|h5|h6">
        <xsl:copy>
            <xsl:call-template name="assign-lang"/>
            <xsl:if test="@align">
                <xsl:attribute name="style">
                    <xsl:value-of select="concat('text-align:',  @align)"/>
                    <!--        <xsl:value-of select="@align"/>  -->
                </xsl:attribute>
            </xsl:if>
            <xsl:call-template name="data-pagehelper"/>
            <xsl:call-template name="named-anchor"/>
            <xsl:apply-templates/>
        </xsl:copy>
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

    <xsl:template match="alt-text">
        <!-- handled with graphic or inline-graphic -->
    </xsl:template>

    <!--  Since lxml only supports XSLT 1.0, can't use the above functions, so do it the imperfect way!-->
    <xsl:template match="list[@type = 'ALP' or @type = 'AUP' or @type = 'AUR' or @type = 'ALR' or @type = 'RLP' or @type = 'RUP' or @type = 'NNP' or @type = 'NNB' or @type = 'NNS']">
        <xsl:variable name="style">
            <xsl:choose>
                <xsl:when test="@type = 'ALP'">a</xsl:when>
                <xsl:when test="@type = 'AUP'">A</xsl:when>
                <xsl:when test="@type = 'AUR'">upper-alpha-right-paren</xsl:when>
                <xsl:when test="@type = 'ALR'">lower-alpha-right-paren</xsl:when>
                <xsl:when test="@type = 'RLP'">i</xsl:when>
                <xsl:when test="@type = 'RUP'">I</xsl:when>
                <xsl:when test="@type = 'NNP'">number-period</xsl:when>
                <xsl:when test="@type = 'NNB'">number-both-parens</xsl:when>
                <xsl:when test="@type = 'NNS'">number-underscore</xsl:when>
                <xsl:otherwise>other</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <ol style="list-style-type: {$style}">
            <xsl:attribute name="data-style">
                <xsl:value-of select="@type"/>
            </xsl:attribute>
            <xsl:apply-templates mode="list"/>
        </ol>
    </xsl:template>

    <xsl:template match="list[@type = 'DASH' or @type = 'DIAMOND' or @type = 'ASTERISK' or @type= 'NONE']">
        <ul>
            <xsl:call-template name="data-pagehelper"/>
            <xsl:attribute name="class">
                <xsl:choose>
                    <xsl:when test="@type = 'DASH'">ml-5 dash</xsl:when>
                    <xsl:when test="@type = 'DIAMOND'">ml-5 diamond</xsl:when>
                    <xsl:when test="@type = 'ASTERISK'">ml-5 asterisk</xsl:when>
                    <xsl:otherwise>ml-5 list-unstyled</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <xsl:attribute name="data-style">
                <xsl:value-of select="@type"/>
            </xsl:attribute>
            <xsl:apply-templates mode="list"/>
        </ul>
    </xsl:template>

    <xsl:template match="li" mode="list">
        <li>
            <xsl:apply-templates select="label"/>
            <xsl:apply-templates/>
        </li>
    </xsl:template>

    <xsl:template match="list-item/p[not(preceding-sibling::*[not(self::label)])]">
        <p>
            <xsl:call-template name="assign-id"/>
            <xsl:for-each select="preceding-sibling::label">
                <span class="label nrsmbee">
                    <xsl:apply-templates/>
                </span>
                <xsl:text> </xsl:text>
            </xsl:for-each>
            <xsl:apply-templates select="@content-type"/>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="n">
        <xsl:apply-templates select="@content-type"/>
        <p class="pagenumber text-center text-muted small">
            <xsl:attribute name="data-pgnum">
                <xsl:apply-templates/>
                <!-- <xsl:value-of select=
                     "number(translate(@nextpgnum,translate(@nextpgnum, '0123456789', ''), '')) - 1"/> -->
                <!-- <xsl:value-of select="number(@nextpgnum)" /> -->
            </xsl:attribute>
            <xsl:if test="@nextpgnum">
                <xsl:attribute name="data-nextpgnum">
                    <xsl:value-of select="@nextpgnum"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@prefixused">
                <xsl:attribute name="data-prefixused">
                    <xsl:value-of select="@prefixused"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates select="@content-type"/>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="pb">
        <div class="pagebreak" data-class="pb">
            <xsl:attribute name="data-page-end">
                <!-- For padding the numbers - pick a string that is large enough that we will never need to pad that much (I think 5 characters would have been fine, but it doesn't hurt to have more) -->
                <xsl:variable name="zero-string" select="'00000000000000000000000000000000000'" />
                <!-- Select the next page number for the current page -->
                <xsl:variable name="next-page-number-string" select="n/@nextpgnum" />
                <!-- Remove the numbers from it -ex. PR0004 becomes PR -->
                <xsl:variable name="next-page-number-letters" select="translate($next-page-number-string, '0123456789', '')" />
                <!-- Remove the letters from the next page string -ex. PR0004 becomes 0004 -->
                <xsl:variable name="next-page-number-string-translated" select="translate($next-page-number-string, $next-page-number-letters, '')" />
                <!-- Get the length of that string - so 4 -->
                <xsl:variable name="next-page-number-string-length" select="string-length($next-page-number-string-translated)" />
                <!-- Generate a string of padded zeros however long the next-page-number-string is i.e 4 -->
                <xsl:variable name="padded-zeros" select="substring($zero-string, 0, $next-page-number-string-length + 1)"/>
                <!-- Translate next-page-number-string-translated to a number ex. 0004 now becomes 4 -->
                <xsl:variable name="next-page-number-value" select="number($next-page-number-string-translated)" />
                <!-- Subtract 1 to get the current page number (in this example it would be 3) -->
                <xsl:variable name="page-number-value" select="number($next-page-number-value - 1)" />
                <!-- Padd the current page number with the appropriate number of zeros (in this example 0003)  -->
                <xsl:variable name="page-number-string" select="substring(concat($padded-zeros, $page-number-value), string-length($page-number-value) + 1, string-length($padded-zeros))" />
                <!-- Combine the letters from before with the new page number PR0003 and that is our correct current page value -->
                <xsl:value-of select="concat($next-page-number-letters, $page-number-string)" />
            </xsl:attribute>
            <xsl:call-template name="named-anchor"/>
            <xsl:apply-templates select="@content-type"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>


    <xsl:template match="bx">
        <span class="peppopup bibtip text-nowrap" data-type="velcro" data-element="{@r}" data-maxwidth="300" data-direction="southeast">
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates select="@content-type"/>
            <xsl:apply-templates/>
        </span>
    </xsl:template>


    <xsl:template match="impx"> <!--when not in metadata mode -->
        <xsl:choose>
            <xsl:when test="@rx"> <!-- for the generated links -->
                <a href="/search/document/{@rx}?glossary={@grpanme}" class="peppopup glosstip impx text-nowrap" data-type="{@type}" data-doc-id="{@rx}" data-grpname="{@grpname}">
                    <xsl:choose>
                        <xsl:when test="$glossaryTermFormattingEnabled = 'true'">
                            <xsl:value-of select="."/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="."/>
                        </xsl:otherwise>
                    </xsl:choose>
                </a>
            </xsl:when>
            <xsl:otherwise> <!-- sometimes impx is manually tagged -->
                <span class="impx" data-type="{@type}">
                    <xsl:choose>
                        <xsl:when test="$glossaryTermFormattingEnabled = 'true'">
                            <xsl:value-of select="."/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="."/>
                        </xsl:otherwise>
                    </xsl:choose>

                </span>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="figx"> <!--when not in metadata mode -->
        <xsl:choose>
            <xsl:when test="@r"> <!-- for the generated links -->
                <a class="peppopup figuretip figx text-nowrap" data-type="figure-id" data-figure-id="{@r}" data-grpname="{@grpname}">
                    <xsl:value-of select="."/>
                </a>
            </xsl:when>
            <xsl:otherwise> <!-- sometimes impx is manually tagged -->
                <a class="figx figuretip" data-type="figure-id">
                    <xsl:value-of select="."/>
                </a>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="poem">
        <div class="poem">
            <xsl:call-template name="data-pagehelper"/>
            <xsl:call-template name="assign-lang"/>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="quote">
        <div class="quote">
            <xsl:call-template name="data-pagehelper"/>
            <xsl:call-template name="assign-lang"/>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="dream">
        <div class="dream">
            <xsl:call-template name="data-pagehelper"/>
            <xsl:call-template name="assign-lang"/>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="dialog">
        <div class="dialog">
            <xsl:call-template name="data-pagehelper"/>
            <xsl:call-template name="assign-lang"/>
            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="p | p2">
        <p class="para my-1">
            <xsl:call-template name="assign-lang"/>
            <xsl:call-template name="data-pagehelper"/>


            <xsl:choose>
                <xsl:when test="ancestor::ftr and not(preceding-sibling::*)">
                    <xsl:attribute name="class">ftr first</xsl:attribute>
                </xsl:when>
                <xsl:when test="ancestor::ftr">
                    <xsl:attribute name="class">ftr</xsl:attribute>
                </xsl:when>
            </xsl:choose>
            <xsl:if test="name() = 'p2'">
                <!--        if you want to concatenate to the attribute class-->
                <!--          <xsl:value-of select="concat('continued',  ' ', @class)"/>-->
                <xsl:attribute name="class">paracont</xsl:attribute>
            </xsl:if>

            <xsl:call-template name="assign-id"/>
            <xsl:apply-templates select="@content-type"/>
            <xsl:apply-templates />
            <xsl:if test="$translationConcordanceEnabled = 'true'">
                <xsl:if test="@lgrx">
                    <span class="ml-2 translation">
                        <xsl:if test="@lgrid">
                            <xsl:attribute name="data-lgrid">
                                <xsl:value-of select="@lgrid"/>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:if test="@lgrx">
                            <xsl:attribute name="data-lgrx">
                                <xsl:value-of select="@lgrx"/>
                            </xsl:attribute>
                        </xsl:if>

                        <xsl:if test="@lgrtype">
                            <xsl:attribute name="data-type">
                                <xsl:value-of select="@lgrtype"/>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:copy-of select="$fa-language" />
                    </span>
                </xsl:if>
            </xsl:if>
        </p>

    </xsl:template>

    <xsl:template match="note">
        <div class="note" id='{@id}'>
            <xsl:call-template name="data-pagehelper"/>
            <xsl:if test="@label">
                <xsl:attribute name="label">
                    <xsl:value-of select="@label"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="notex">
        <span class="peppopup notetip" >
            <a href="#note-information">
                <sup>
                    <xsl:apply-templates/>
                </sup>
            </a>
            <xsl:text></xsl:text>
            <br></br>
            <span class="peppopuptext" hidden="True" role="dialog">
                <xsl:value-of select="key('element-by-id', @r)/p" />
            </span>
        </span>
    </xsl:template>

    <xsl:template match="dictentrygrp">
        <div class="dictentrygrp" id='{@id}'>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="dictalso">
        <p class="dictentrygrp-dictalso d-flex flex-wrap">
            <xsl:copy-of select="$fa-flag" />
            <xsl:text> </xsl:text>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="dictalso/term">
        <span class="dictentrygrp-dictalso-term smallcaps">
            <!-- xslt 1.0-->
            <xsl:value-of select="translate(@lang, $lowercase,$uppercase)"/>
            <xsl:text>: </xsl:text>
            <xsl:apply-templates/>
            <xsl:text>; </xsl:text>
        </span>
    </xsl:template>

    <xsl:template match="def">
        <div class="def-def body">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="defrest">
        <div class="seemore">
            <xsl:text>&#13;</xsl:text>
            <details>
                <summary>...excerpted...click for more...</summary>
                <div class="def-def body">
                    <xsl:apply-templates/>
                </div>
            </details>
        </div>
    </xsl:template>

    <xsl:template match="term">
        <div class="dictentrygrp-term">
            <xsl:call-template name="assign-id"/>
            <p>
                <xsl:apply-templates/>
            </p>
        </div>
    </xsl:template>

    <xsl:template match="src">
        <p class="dictentry-src">
            <xsl:call-template name="assign-id"/>
            <xsl:copy-of select="$fa-book" />
            <xsl:text> </xsl:text>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="binc/j">
        <span class="font-italic">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="bst">
        <span class="font-italic">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="binc">
        <span class="bibentry" id="{@id}">
            <span class="ref-content cell">
                <xsl:apply-templates/>
            </span>
            <!--matched reference id-->
            <xsl:if test="@rx">
                <a class="bibx pl-2" data-type="BIBX">
                    <xsl:attribute name="data-document-id">
                        <xsl:value-of select="@rx"/>
                    </xsl:attribute>
                    <xsl:copy-of select="$fa-right-arrow" />
                </a>
            </xsl:if>
            <xsl:if test="@rxcf">
                <a class="bibx pl-2" data-type="BIBX">
                    <xsl:attribute name="data-document-id">
                        <xsl:value-of select="@rxcf"/>
                    </xsl:attribute>
                    <xsl:copy-of select="$fa-link" />
                </a>
                <span class="bibx-related-info ml-1">
                    <xsl:copy-of select="$fa-question" />
                </span>
            </xsl:if>
        </span>
    </xsl:template>

    <xsl:template match="be">
        <p class="bibentry" id="{@id}">
            <span class="ref-content cell">
                <xsl:apply-templates/>
            </span>
            <!--matched reference id-->
            <xsl:if test="@rx">
                <a class="bibx pl-2" data-type="BIBX">
                    <xsl:attribute name="data-document-id">
                        <xsl:value-of select="@rx"/>
                    </xsl:attribute>
                    <xsl:copy-of select="$fa-right-arrow" />
                </a>
            </xsl:if>
            <xsl:if test="@rxcf">
                <a class="bibx pl-2" data-type="BIBX">
                    <xsl:attribute name="data-document-id">
                        <xsl:value-of select="@rxcf"/>
                    </xsl:attribute>
                    <xsl:copy-of select="$fa-link" />
                </a>
                <span class="bibx-related-info ml-1">
                    <xsl:copy-of select="$fa-question" />
                </span>
            </xsl:if>
        </p>
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
        <span class="bibyear y">
            <xsl:apply-templates/>
        </span>
    </xsl:template>


    <xsl:template match="be/bst">
        <xsl:text>&#13;</xsl:text>
        <span class="bibyear bst">
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

    <xsl:template match="be/v">
        <xsl:text>&#xA0;</xsl:text>
        <span class="bibjournal v">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="be/bp">
        <xsl:text>&#xA0;</xsl:text>
        <span class="bibpublisher bp">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="be/pp">
        <xsl:text>&#xA0;</xsl:text>
        <span class="bibpages pp">
            <xsl:apply-templates/>
        </span>
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

    <xsl:template match="tbl">
        <!-- other labels are displayed as blocks -->
        <div class="table-responsive nrs my-3">
            <xsl:call-template name="data-pagehelper"/>
            <xsl:attribute name="id">
                <xsl:value-of select="@id"/>
            </xsl:attribute>
            <xsl:attribute name="data-toc">
                <xsl:value-of select="@TOC"/>
            </xsl:attribute>
            <xsl:attribute name="data-align">
                <xsl:value-of select="@align"/>
            </xsl:attribute>
            <xsl:attribute name="data-ewide">
                <xsl:value-of select="@ewide"/>
            </xsl:attribute>
            <!--      <xsl:apply-templates select="@*" mode="table-copy"/>-->
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <!--
         <xsl:template match="tbl">
         <table class="table table-responsive">
         <xsl:apply-templates/>
         </table>
         </xsl:template> -->

    <xsl:template match="row">
        <!-- other labels are displayed as blocks -->
        <tr>
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

    <xsl:template match="@*" mode="table-copy">
        <xsl:apply-templates/>
    </xsl:template>


    <xsl:template match="@content-type" mode="table-copy"/>

<!--    <xsl:template match="table">
        <table class="table mb-0">
            <xsl:apply-templates/>
        </table>
    </xsl:template>
-->


    <!-- ============================================================= -->
    <!--  INLINE MISCELLANEOUS                                         -->
    <!-- ============================================================= -->
    <!--  Templates strictly for formatting follow; these are templates
         to handle various inline structures -->

    <xsl:template match="break">
        <br class="br"/>
    </xsl:template>

    <xsl:template match="email">
        <a href="mailto:{.}">
            <xsl:apply-templates/>
        </a>
    </xsl:template>

    <xsl:template match="hr">
        <hr class="hr"/>
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

    <xsl:template match="bi">  <!--bold italics-->
        <b><i>
                <xsl:apply-templates/>
            </i></b>
    </xsl:template>

    <xsl:template match="bold|b">  <!--We use b, but left in "bold"-->
        <b>
            <xsl:apply-templates/>
        </b>
    </xsl:template>

    <xsl:template match="italic|i"> <!--We use i, but left in "italics"-->
        <i>
            <xsl:apply-templates/>
        </i>
    </xsl:template>

    <xsl:template match="overline">  <!--we (PEP) don't have this-->
        <span style="text-decoration: overline">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="roman">  <!--we (PEP) don't have this-->
        <span style="font-style: normal">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="sc|sm">  <!--sc is for future JATS-->
        <span style="font-variant: small-caps">
            <xsl:apply-templates/>
        </span>
    </xsl:template>


    <xsl:template match="so">  <!--Strikeout-->
        <span style="text-decoration: line-through">
            <xsl:apply-templates/>
        </span>
    </xsl:template>


    <xsl:template match="sb"> <!--Subscript-->
        <sub>
            <xsl:apply-templates/>
        </sub>
    </xsl:template>


    <xsl:template match="su"> <!--superscript-->
        <sup>
            <xsl:apply-templates/>
        </sup>
    </xsl:template>


    <xsl:template match="underline|u"> <!--underlined-->
        <span style="text-decoration: underline">
            <xsl:apply-templates/>
        </span>
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

    <xsl:template match="figx" mode="label-text">
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

    <xsl:template name="assign-lang">
        <xsl:choose>
            <xsl:when test="@lang">
                <xsl:attribute name="lang">
                    <xsl:value-of select="@lang"/>
                </xsl:attribute>
            </xsl:when>
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
            <b>
                <xsl:apply-templates select="nfirst"/>
                <xsl:text> </xsl:text>
                <xsl:apply-templates select="nlast"/>
            </b>
        </xsl:for-each>
    </xsl:template>



    <!-- ============================================================= -->
    <!--  End stylesheet                                               -->
    <!-- ============================================================= -->

</xsl:stylesheet>
