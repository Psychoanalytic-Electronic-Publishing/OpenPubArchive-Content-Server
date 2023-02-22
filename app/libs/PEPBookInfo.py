# -*- coding: utf-8 -*-
# Note this must be utf-8, not Latin-1
"""
This module adapted from a much older module used in PEPXML to compile PEP instances since 200x!

  ** Slowly being adopted to opas **
  
  Should probably be integrated into opasProductLib - some routines are perhaps done better there from the database rather than code (newer module), and from the database

"""
import sys
sys.path.append('../libs')
sys.path.append('../config')
sys.path.append('../libs/configLib')

import logging
logger = logging.getLogger(__name__)

#PROJECT_ROOT = os.path.abspath(os.path.join(
                  #os.path.dirname(__file__), 
                  #os.pardir)
#)
#sys.path.append(PROJECT_ROOT)

import re

#import html.parser
# import xml.sax.saxutils

from opasConfig import gClassicBookTOCList, gSEIndex, gGWIndex, RX_CONFIDENCE_PROBABLE

import opasGenSupportLib as opasgenlib
#import opasDocuments
#import codecs

gDbg1 = 0   # details
gBell = False

#--------------------------------------------------------------------------------
class PEPBookInfo:
    """
    A class to recognize books from plain text strings or XML.
       Reuse for many searches

       Parses XML strings into ReferenceMetadata to do the search,
           using the PEPReferenceMetadata class.

       Can return an object dictionary of ReferenceMetaData for the book
           in the XML specified for search,
           or from the actual PEP reference.

        >>> pepBInfo = PEPBookInfo()
        >>> tgt = "Ferenczi, S., Abraham, K., Simmel, E., & Jones, E. (1921). Psychoanalysis and the War Neuroses. London: Int. Psychoanal. Press."
        >>> pepBInfo.getPEPBookCodeStr(tgt) # doctest: +ELLIPSIS
        ('IPL.002.0000A', 0.91, None)

        >>> tgt = "Winnicott, D. W. (1965). On the contribution of direct child observation to psycho-analysis. In <bst>The Maturational Processes and the Facilitating Environment. New York: Int. Univ. Press, 1965, pp. 109-114."
        >>> pepBInfo.getPEPBookCodeStr(tgt) # doctest: +ELLIPSIS
        ('IPL.064.0000A', 0.91, None)

        >>> tgt = "Rosenfeld, H. (1987). Impasse and Interpretation. London and New York: Tavistock."
        >>> pepBInfo.getPEPBookCodeStr(tgt) # doctest: +ELLIPSIS
        ('NLP.001.0000A', 0.91, None)

        >>> pepBInfo.getPEPBookCodeStr("Anderson, R. (1992). Introduction to Clinical Lectures on Klein and Bion.")[0]
        'NLP.014.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Anzieu, D. (1986). Freud's Self-Analysis: Translated from the French by Peter Graham.  With a Preface by M. Masud R. Khan.")[0]
        'IPL.118.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Balint, M. (1979). The Basic Fault: Therapeutic Aspects of Regression.")[0]
        'ZBK.033.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bion, W. R. (1959). Experiences in Groups And Other Papers.")[0]
        'ZBK.006.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bion, W. R. (1962). Learning from Experience.")[0]
        'ZBK.003.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bion, W. R. (1963). Elements of Psycho-Analysis.")[0]
        'ZBK.004.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bion, W. R. (1965). Transformations: Change from Learning to Growth.")[0]
        'ZBK.005.0001A'
        >>> pepBInfo.getPEPBookCodeStr("Bion, W. R. (1970). Attention and Interpretation: A Scientific Approach to Insight in Psycho-Analysis and Groups.")[0]
        'ZBK.002.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Boehlich, W. (1990). The Letters of Sigmund Freud to Eduard Silberstein 1871-1881.")[0]
        'ZBK.029.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bowlby, J. (1969). Attachment and Loss: Volume 1: Attachment.")[0]
        'IPL.079.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bowlby, J. (1973). Attachment and Loss: Volume II: Separation, Anxiety and Anger.")[0]
        'IPL.095.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Bowlby, J. (1980). Attachment and Loss: Volume III: Loss, Sadness and Depression.")[0]
        'IPL.109.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Brabant, E., Falzeder, E. and Giampieri-Deutsch, P. (1993). The Correspondence of Sigmund Freud and Sandor Ferenczi Volume 1, 1908-1914.")[0]
        'ZBK.025.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Fairbairn, W. D. (1952). Psychoanalytic Studies of the Personality.")[0]
        'ZBK.007.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Falzeder, E. (2002). The Complete Correspondence of Sigmund Freud and Karl Abraham 1907-1925.")[0]
        'ZBK.052.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Falzeder, E. and Brabant, E. (1996). The Correspondence of Sigmund Freud and Sandor Ferenczi Volume 2, 1914-1919.")[0]
        'ZBK.026.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Falzeder, E. and Brabant, E. (2000). The Correspondence of Sigmund Freud and Sandor Ferenczi, Volume 3, 1920-1933.")[0]
        'ZBK.027.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Feldman, M. and Spillius, E. B. (1989). Psychic Equilibrium and Psychic Change: Selected Papers of Betty Joseph.")[0]
        'NLP.009.0001A'
        >>> pepBInfo.getPEPBookCodeStr("Ferenczi, S. (1952). First Contributions to Psycho-Analysis.")[0]
        'IPL.045.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Ferenczi, S., Abraham, K., Simmel, E. and Jones, E. (1921). Psychoanalysis and the War Neurosis.")[0]
        'IPL.002.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Freud, E. L. (1961). Letters of Sigmund Freud 1873-1939.")[0]
        'ZBK.051.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Freud, E. L. (1970). The Letters of Sigmund Freud and Arnold Zweig.")[0]
        'IPL.084.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Groddeck, G. (1977). The Meaning of Illness: Selected Psychoanalytic Writings Including his Correspondence with Sigmund Freud.")[0]
        'IPL.105.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Jones, E. (1955). Sigmund Freud Life and Work, Volume Two: Years of Maturity 1901-1919.")[0]
        'ZBK.046.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Jones, E. (1957). Sigmund Freud Life And Work, Volume Three: The Last Phase 1919-1939.")[0]
        'ZBK.047.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Jones, E. (1972). Sigmund Freud Life and Work, Volume One: The Young Freud 1856-1900.")[0]
        'ZBK.045.0000A'
        >>> pepBInfo.getPEPBookCodeStr("King, P. and Steiner, R. (1991). The Freud/Klein Controversies 1941-45")[0]
        'NLP.011.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Klein, M. (1932). The Psycho-Analysis of Children.")[0]
        'IPL.022.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Klein, M. (1961). Narrative of a Child Analysis: The Conduct of the Psycho-Analysis of Children as seen in the Treatment of a Ten year old Boy.")[0]
        'IPL.055.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Klein, M. (1975). Envy and Gratitude and Other Works 1946\xef\xbf\xbd1963: Edited By:  M. Masud R. Khan.")[0]
        'IPL.104.0000A'
        >>> #pepBInfo.getPEPBookCodeStr("Kohut, H. (1971). The Analysis of the self: A Systematic Approach to the Psychoanalytic Treatment of Narcissistic Personality Disorders.")[0]
        >>> #'ZBK.049.0001A'
        >>> pepBInfo.getPEPBookCodeStr("Kohut, H. (1984). How does psychoanalysis cure?.")[0]
        'ZBK.034.0001A'
        >>> pepBInfo.getPEPBookCodeStr("Laplanche, J. and Pontalis, J. B. (1973). The Language of Psycho-Analysis: Translated by Donald Nicholson-Smith.")[0]
        'IPL.094.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Masson, J. M. (1985). The Complete Letters of Sigmund Freud to Wilhelm Fliess, 1887-1904.")[0]
        'ZBK.042.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Matte-Blanco, I. (1988). Thinking, Feeling, and Being: Clinical Reflections on the Fundamental Antinomy of Human Beings and World.")[0]
        'NLP.005.0000A'
        >>> pepBInfo.getPEPBookCodeStr("McGuire, W. (1974). The Freud/Jung Letters: The Correspondence Between Sigmund Freud and C. G. Jung.")[0]
        'ZBK.041.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Meng, H. and Freud, E. L. (1963). Psychoanalysis and Faith: The Letters of Sigmund Freud and Oskar Pfister.")[0]
        'IPL.059.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Milner, M. (1969). The Hands of the Living God: An Account of a Psycho-analytic Treatment.")[0]
        'IPL.076.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Paskauskas, R. A. (1993). The Complete Correspondence of Sigmund Freud and Ernest Jones 1908-1939.")[0]
        'ZBK.028.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Pfeiffer, E. (1963). Sigmund Freud and Lou Andreas-Salom\xef\bf\bde Letters.")[0]
        'IPL.089.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Racker, H. (1988). Transference and Countertransference.")[0]
        'IPL.073.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Rickman, J. (1957). Selected Contributions to Psycho-Analysis.")[0]
        'IPL.052.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Roberts, T. (2003). Translator' Notes to the English Edition of The Sigmund Freud-Ludwig Binswanger Correspondence 1908-1938.")[0]
        'ZBK.050.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Rodman, F. (1987). The Spontaneous Gesture: Selected Letters of D. W. Winnicott.")[0]
        'ZBK.020.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Rosenfeld, H. (1987). Impasse and Interpretation: Therapeutic and anti-therapeutic factors in the psychoanalytic treatment of psychotic, borderline, and neurotic patients.")[0]
        'NLP.001.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Sandler, J., Michels, R. and Fonagy, P. (2000). Changing Ideas In A Changing World: The Revolution in Psychoanalysis.: Essays in Honour of Arnold Cooper.")[0]
        'ZBK.038.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Spence, D. P. (1982). Narrative Truth and Historical Truth: Meaning and Interpretation in Psychoanalysis.")[0]
        'ZBK.015.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Stern, D. N. (1985). The Interpersonal World of the Infant: A View from Psychoanalysis and Developmental Psychology.")[0]
        'ZBK.016.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Winnicott, D. W. (1965). The Maturational Processes and the Facilitating Environment: Studies in the Theory of Emotional Development.")[0]
        'IPL.064.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Winnicott, D. W. (1971). Therapeutic Consultations in Child Psychiatry.")[0]
        'IPL.087.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Winnicott, D. W. (1971). Playing and Reality.")[0]
        'ZBK.017.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Winnicott, D. W. (1975). Through Paediatrics to Psycho-Analysis.")[0]
        'IPL.100.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Winnicott, D. W. (1980). The Piggle: An Account of the Psychoanalytic Treatment of a Little Girl: Edited by Ishak Ramzy.")[0]
        'IPL.107.0001A'
        >>> pepBInfo.getPEPBookCodeStr("Winnicott, D. W. (1986). Holding and Interpretation: Fragment of An Analysis.")[0]
        'IPL.115.0001A'
        >>> pepBInfo.getPEPBookCodeStr("Wallerstein, R. (1998): Lay Analysis")[0]
        'ZBK.056.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Wallerstein, R. (1986): 42 Lives in Treatment")[0]
        'ZBK.055.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Thoma, H., & Kachele, H. (1985), Psychoanalytic Practise. Berlin: Springer Verlag.")[0]
        'ZBK.061.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Thoma, H., & Kachele, H. (1992), Psychoanalytic Practice: Volume 2. Berlin: Springer Verlag.")[0]
        'ZBK.062.0000A'
        >>> pepBInfo.getPEPBookCodeStr("Thom&auml;, H., & K&auml;chele, H. (1992), Psychoanalytic Practice: Volume 2. Berlin: Springer Verlag.")[0]
        'ZBK.062.0000A'
        >>> pepBInfo.getPEPBookCodeStr('<be rxp = "PAQ.027.0253A" id = "B060" rxps = "81.12"><a><l>Zilboorg</l>, G.</a> (<y>1958</y>). <t>Review of The Life and Work of Sigmund Freud</t>. <i>Volume III. The Lasi Phase 1919&ndash;1939</i>. <j>Psychoanal. Q.</j>, <v>21</v>:<pp>253-262</pp>.</be>')
        (None, None, None)

    """

    keyList = list(gClassicBookTOCList.keys())
    specialKeyList = list(gSEIndex.keys()) + list(gGWIndex.keys())

    andersonR = "Anderson,\s+R\."
    anzieuD = "Anzieu,\s+D\."
    bionW = "Bion,\s+W\.(\s+R\.)?"
    boehlichW = "Boehlich,\s+W\."
    bowlbyJ = "Bowlby,\s+J\."
    britton = "Britton,?\s+R\."
    fairbairnW = "Fairbairn,\s+W\.(\s+D\.)?"
    falzeder = "Falzeder,?\s+E\."
    feldmanM = "Feldman,\s+M\."
    ferencziS = "Ferenczi,\s+S\."
    freudE = "Freud,\s+E\.(\s+L\.)?"
    groddeckG = "Groddeck,\s+G\."
    jonesE = "Jones,\s+E\."
    kingP = "King,\s+P\."
    kleinM = "Klein(,\s+M\.?)"
    kohutH = "Kohut"
    laplancheJ = "Laplanche,\s+J\."
    massonJ="Masson(\,?\s*J\.?\s*M\.?)?"
    matteblancoI = "Matte[ \-]Blanco,\s+I\."
    mengH = "Meng(,\s+H\.?)?"
    milnerM = "Milner(,?\s*M\.?)?"
    pfeifferE = "Pfeiffer(,?\s*E\.?)?"
    rackerH = "Racker(,?\s*H\.?)?"
    rickmanJ = "Rickman(,?\s*J\.?)?"
    rosenfeldH = "Rosenfeld(,?\s*H\.?)?"
    spenceD = "Spence(,\s+D\.(\s+P\.)?)?"
    wallerstein = "Wallerstein,?\s+R\.(\s+S\.?)?"
    winnicott = "Winnicott(,?\s+D\.?)?"

    dashSep = "(\s*([\-\s\x96]|to|&mdash;|&ndash;)\s*)"
    dashSepPlusComma = "(\s*([\-\s\x96,]|to|&mdash;)\s*)"
    patDash = "(\s*([\-\s\x96]|&mdash;|&ndash;)?\s*)"
    patOne = "(one|I|1)\.?"
    patTwo = "(two|II|2)\.?"
    patThree = "(three|III|3)\.?"
    patTen = "(ten|X|10)\.?"
    patVol = "(the\s+)?Vol(ume|\.)\s*"
    patSubSep = "\s*[:,\.\x96]?\s*"
    patPsychoanalysis = "(psycho-?)?analysis"
    patPsychoanalytic = "psycho-?analytic"
    patAacute = "(&aacute;|a|\xe1|&auml;)"
    patThe = "(\s*The )?"
    patAnd = "(\s*(and|\&|\&amp;|und|\,)\s*)"
    patPunc = "\s*[\.,;:]?\s*"
    patAndTo = "\s*(and|\&|\&amp;|to)\s*"
    patApos = "([']|&apos;)?"
    patTo = "(to|in)"
    patBetween = "\s*(Between|of|betwixt|among)\s*"
    patDashSlash = "\s*[\-\\/\x96]\s*"
    patOfThe = "(\s*of(\s+the)?\s*)"
    patAndThe = "(\s*and(\s+the)?\s*)"

    gSleep = 0  # delay after update
    gSleep2 = 0 # delay after  clear
    bookPatterns = {
        # minMatchLen, authPat, titlePat, yearPat, extraPat

        "ZBK.002.0000A": (  30,
                            bionW,
                            "Attention and Interpretation("+patPunc+" A Scientific Approach to Insight in "+patPsychoanalysis+" and Groups)?",
                            "(1970|1975)",
                            None
                            ),

        "ZBK.003.0000A": (  30,
                            bionW,
                            "Learning from Experience",             #checked
                            "(1962|1970)",
                            None
                            ),

        "ZBK.004.0000A": (  30,
                            bionW,
                            "Elements of "+patPsychoanalysis+"",           #checked
                            "(1963)",
                            None
                            ),

        "ZBK.005.0001A": (  30,
                            bionW,
                            "Transformations("+patPunc+" Change from Learning to Growth)?",
                            "(1965)",
                            None
                            ),

        "ZBK.006.0000A": (  30,
                            bionW,
                            "(Experiences in Groups( "+patAnd+" Other Papers)?)|(Experi&ecirc;ncias com grupos)",     # no hits in refcorrections; ok in fullbiblioxml
                            "(1959|1961|1962)",
                            None
                            ),

        "ZBK.007.0000A": (  30,
                            "fairbairn",
                            patPsychoanalytic+" Stud(y|ies) "+patOfThe+"Personality",
                            "(1952|19[34][0-9])",
                            None
                            ),

        "ZBK.015.0000A": (  30,
                            spenceD, #"Spence,  D. P.",
                            "Narrative  Truth"+patAnd+" Historical Truth(:? Meaning and Interpretation in "+patPsychoanalysis+")?",     #checked
                            "(1982|1984)",
                            None
                            ),

        "ZBK.016.0000A": (  30,
                            "Stern",
                            patThe+"Interpersonal World of  the Infant("+patSubSep+" (A )?View from "+patPsychoanalysis+" and Developmental Psychology)?",     #checked
                            "(1985|1986|1984)",
                            None
                            ),

        "ZBK.017.0000A": (  30,
                            winnicott,
                            "Playing and Reality",
                            "(1971|1974)",
                            None
                            ),

        "ZBK.020.0000A": (  30,
                            "Rodman(,?\s*F\.?)?",
                            patThe+"Spontaneous Gesture("+patSubSep+" Selected Letters of D. W. Winnicott)?",              #checked
                            "(1987)",
                            None
                            ),

        "ZBK.025.0000A": (  0,
                            "(Brabant|Freud|Ferenczi|Haynal)",
                            "The Correspondence of  Sigmund Freud "+patAndTo+" S"+patAacute+"ndor Ferenczi("+patPunc+" "+patVol+patOne+patPunc+"("+patPunc+" 1908"+dashSep+"(19)?14)?)?",
                            "199[0-5]|1908|1909|191[0-4]",
                            None
                            ),

        "ZBK.026.0000A": (  30,
                            "("+falzeder+"|Freud|Ferenczi|Hoffer)",
                            patThe+"Correspondence  of Sigmund Freud "+patAndTo+" S"+patAacute+"ndor Ferenczi("+patPunc+" "+patVol+patTwo+patPunc+"( 1914"+dashSep+"(19)?19)?)?",
                            "191[4-9]|199[6-7]",
                            patVol+patTwo   # must be vol2
                            ),

        "ZBK.027.0000A": (  30,
                            "("+falzeder+"|Freud|Ferenczi|Haynal)",
                            patThe+"Correspondence  of Sigmund Freud "+patAndTo+" S"+patAacute+"ndor Ferenczi("+patPunc+" "+patVol+patThree+patPunc+"( 1920"+dashSep+"(19)?33)?)?",
                            "19[23][0-9]|1998|1999|200[0-9]",
                            patVol+patThree  #  must be vol3
                            ),

        "ZBK.028.0000A": (  30,
                            "Paskauskas|Freud|Jones|Steiner",
                            patThe+"Complete Correspondence "+patBetween+"  Sigmund Freud "+patAndTo+" Ernest Jones("+patSubSep+" 1908"+dashSep+"(19)?39)?",     #checked
                            "1990|1993|1995|192[0-9]",
                            None
                            ),

        "ZBK.029.0000A": (  20,
                            boehlichW+"|freud|silberstein", #"Boehlich,? W\.?",
                            "The Letters of Sigmund Freud "+patAndTo+"  (Eduard|Edward) Silberstein("+patPunc+" 1871"+dashSep+"(18)?81)?",        #checked
                            "1990|(1989|18[0-9][0-9])",
                            None
                            ),

        "ZBK.033.0000A": (  10,
                            "Balint,? M\.?",
                            "The Basic  Fault("+patSubSep+" Therapeutic Aspects of Regression)?",               #checked and fixed instances in the refcorrections db
                            "1979|[12][0-9][0-9][0-9]",
                            None
                            ),

        "ZBK.034.0001A": (  30,             #checked
                            kohutH,
                            "How does "+patPsychoanalysis+" cure(\?)?",
                            "1984",
                            None
                            ),

        "ZBK.038.0000A": (  30,
                            "Sandler|Fonagy|Michels|Jacobs|Milrod|Rosenblatt|Compton|Schafer|Goldberg|Schlesinger|Viederman|Auchincloss|Person, E|Lester, E|Lester, O|Nersessian|Akhtar|Dalsimer|Vaillant|Luborsky|Gabbard|Paul,? R|Spillius|Shapiro|Canestri|Cavell|Mahoney|Stade|Peskin|Gay, P.|Tuckett||Makari",
                            "Changing Ideas In  A Changing World("+patSubSep+" The Revolution in "+patPsychoanalysis+")?",       #no hitts in either table
                            "2000",
                            None
                            ),

        "ZBK.041.0000A": (  30,
                            "McGuire|Freud|Jung",
                            patThe+"Freud"+patDashSlash+"Jung Letters("+patSubSep+patThe+"Correspondence "+patBetween+" Sigmund Freud "+patAndTo+"  (C\.?(\s*G\.?)?)?\s*Jung)?",
                            "1974|190[6-9]|191[0-4]",
                            None
                            ),

        "ZBK.042.0000A": (  30,
                            massonJ+"|Freud|Fliess",
                            patThe+"Complete Letters of Sigmund Freud "+patAndTo+"  Wilhelm Fliess("+patSubSep+" 1887"+dashSep+"(19)?04)?",
                            "1985|188[7-9]|189[0-9]|190[0-4]",
                            None
                            ),

        "ZBK.045.0000A": (  30,
                            jonesE,
                            "(Life  "+patAnd+" Work (of )?Sigmund Freud)|(Sigmund Freud"+patSubSep+" Life "+patAnd+" Work)"+patSubSep+" "+patVol+patOne+"("+patSubSep+" The Young Freud( 1856"+dashSep+"1900)?)?",
                            "1972|1954|1953",
                            None
                            ),

        "ZBK.046.0000A": (  30,
                            jonesE,
                            "(Life  "+patAnd+" Work (of )?Sigmund Freud)|(Sigmund Freud"+patSubSep+" Life "+patAnd+" Work)"+patSubSep+" "+patVol+patTwo+"("+patSubSep+" Years of Maturity( 1901"+dashSep+"1919)?)?",
                            "1955",
                            None
                            ),

        "ZBK.047.0000A": (  30,
                            jonesE,
                            "(Life  "+patAnd+" Work (of )?Sigmund Freud)|(Sigmund Freud"+patSubSep+" Life "+patAnd+" Work)"+patSubSep+" "+patVol+patThree+"("+patSubSep+" The Last Phase( 1919"+dashSep+"1939)?)?",
                            "1957|1980",
                            None
                            ),

        "ZBK.048.0000A": (  30,
                            "Meltzer|Money",
                            patThe+"Collected Papers of (R(oger)?)? Money"+dashSep+"Kyrle",
                            "1986|1978|1958|1977|1968",
                            None,
                            ),

        "ZBK.049.0001A": (  30,
                            kohutH,
                            patThe+"Analysis of the Self("+patSubSep+"  A Systematic Approach to( the)? "+patPsychoanalytic+" Treatment of Narcissistic Personality Disorders?)?",
                            "1971",
                            None
                            ),

        "ZBK.048.0001A": (  30,
                            "Money\-Kyrle",
                            "The Collected Papers of Roger Money\-Kyrle",
                            "1978",
                            None
                            ),

        "ZBK.050.0000A": (  30,
                            "Fichtner|Freud|Binswanger",
                            patThe+"Sigmund Freud"+dashSepPlusComma+"Ludwig Binswanger( Correspondence(\s1908"+dashSep+"1938)?)?",
                            "2003|1992",
                            None
                            ),
        "ZBK.051.0000A": (  30,
                            "Freud, E\.(\s+L\.)",
                            patThe+"Letters of  Sigmund Freud(\s+1873"+dashSep+"1939)?",  # This is too short, and too common, a title to make the date optional!    Trying again.
                            "1961|1960",
                            None
                            ),

        "ZBK.052.0000A": (  30,
                            falzeder+"|Freud|Abraham",
                            patThe+"(Complete Correspondence of|Letters of) Sigmund Freud "+patAndTo+"  Karl Abraham(\s+1907"+dashSep+"1925)?",
                            "2002|190[7-9]|191[0-9]|192[0-5]",
                            None
                            ),

        "ZBK.054.0000A": (  30,
                            britton+"|Feldman|O.Shaughnessy|Steiner",      #checked
                            patThe+"Oedipus Complex Today("+patSubSep+" Clinical Implications)?",
                            "1989|1994",
                            None
                            ),

        "ZBK.055.0000A": (  30,
                            wallerstein,
                            "((Forty"+dashSep+"two)|42) lives in treatment("+patSubSep+" A  study of "+patPsychoanalysis+" and psychotherapy)?",
                            "(1985|1986|2000)",
                            None
                            ),

        "ZBK.056.0000A": (  30,
                            wallerstein,
                            "Lay analysis("+patSubSep+" Life inside the controversy)?",
                            "1998",
                            None
                            ),


        "ZBK.061.0000A": (  10,
                            "Thom(a|\&auml;)",
                            "Psycho-?analytic Practi[cs]e"+patSubSep+"((Vol(ume|.)\s+(1|one))?("+patSubSep+"\s*Principles)?)?",
                            "198[57]",
                            None
                            ),

        "ZBK.062.0000A": (  10,
                            "Thom(a|\&auml;)",
                            "Psycho-?analytic Practi[cs]e"+patSubSep+"((Vol(ume|.)\s+(2|two))?("+"\s*Clinical\s+Studies)?)?",
                            "1992",
                            None
                            ),

        "ZBK.070.0000A": (  30,
                            "Deutsch",
                            "Selected Problems of Adolescence: With Special Emphasis on Group Formation",
                            "(1967)",
                            None
                            ),

        "ZBK.071.0000A": (  30,
                            "Nagera",
                            "Early Childhood Disturbances, the Infantile Neurosis, and the Adulthood Disturbances.e",
                            "(1966)",
                            None
                            ),

        "ZBK.072.0000A": (  30,
                            "Hartmann",
                            "Ego Psychology and the Problem of Adaptation",
                            "(1958)",
                            None
                            ),

        "ZBK.073.0000A": (  30,
                            "Levy",
                            "The Therapeutic Alliance",
                            "(2000)",
                            None
                            ),

        "ZBK.074.0000A": (  30,
                            "Dowling",
                            "Conflict and Compromise: Therapeutic Implications",
                            "(1991)",
                            None
                            ),

        "ZBK.075.0000A": (  30,
                            "Dowling",
                            "Child and Adolescent Analysis: its Significance for Clinical Work with Adults",
                            "(1990)",
                            None
                            ),

        "ZBK.076.0000A": (  30,
                            "Shur",
                            "The ID and the Regulatory Principles of Mental Functioning",
                            "(1967)",
                            None
                            ),

        "ZBK.077.0000A": (  30,
                            "Kaplan-Solms",
                            "Clinical Studies in Neuro-Psychoanalysis: Introduction to a Depth Neuropsychology",
                            "(2002)",
                            None
                            ),

        "ZBK.078.0000A": (  30,
                            "Rothstein",
                            "The Interpretation of Dreams in Clinical Work.",
                            "(1987)",
                            None
                            ),

        "ZBK.079.0000A": (  30,
                            "Dowling",
                            "The Psychology and Treatment of Addictive Behavior.",
                            "(1985)",
                            None
                            ),

        "ZBK.080.0000A": (  30,
                            "Rothstein",
                            "The Reconstruction of Trauma: its Significance in Clinical Work",
                            "(1986)",
                            None
                            ),

        "ZBK.081.0000A": (  30,
                            "Rothstein",
                            "Models of the Mind(\s|\-+)\s*Their Relationships to Clinical Work.",
                            "(1985)",
                            None
                            ),

        "ZBK.101.0001A": (  30,
                            spenceD, #"Spence,  D. P.",   # FUTURE <be rxp = "ZBK.030.0001A" id = "B058"> <a> <l>Spence</l>, D. P.</a> (<y>1987</y>), <t>The Freudian Metaphor</t>.  New York: <bp>Norton</bp>.</be>
                            patThe+"Freudian Metaphor",
                            "(1987)",
                            None
                            ),

        "ZBK.102.0001A": (  30,
                            kohutH,
                            patThe+"Restoration of  the Self",
                            "1977",
                            None
                            ),

        "ZBK.103.0001A": (  30,
                            "fairbairn",
                            "An Object"+patDash+"Relations  Theory "+patOfThe+"Personality",
                            "(1954|1952)",
                            None
                            ),

        #Feiner, A. 1979 Countertransference and the anxiety of influence In: Countertransference: The Therapist's Contribution to The Therapeutic Situation L. Epstein and A. Feiner, eds. Jason Aronson, Inc.
        "ZBK.104.0001A": (  30,
                            "feiner|Epstein",
                            "Countertransference",
                            "(1979)",
                            None
                            ),

        "ZBK.105.0001A": (  30,
                            "Spezzano",
                            "Affect in  Psychoanalysis",
                            "(1993)",
                            None
                            ),

        "ZBK.106.0001A": (  30,
                            "Spitz",
                            "The First  Year of Life",
                            "(1965)",
                            None
                            ),

        "ZBK.107.0001A": (  30,
                            "Spotnitz",
                            "Modern Psychoanalysis  "+patOfThe+" Schizophrenic Patient",
                            "(1969)",
                            None
                            ),

        "ZBK.108.0001A": (  30,
                            "Steiner",
                            "Psychic Retreats",
                            "(1993)",
                            None
                            ),

        "ZBK.109.0001A": (  30,
                            "Stern",
                            patThe+"First Relationship",
                            "(1977)",
                            None
                            ),

        "ZBK.110.0001A": (  30,
                            "Stern",
                            "Unformulated Experience("+patSubSep+"  From Dissociation to Imagination in Psychoanalysis)?",
                            "(1997)",
                            None
                            ),

        "ZBK.110.0001A": (  30,
                            "Stoller",
                            "Sex and Gender("+patSubSep+patVol+patOne+")?",
                            "(1968)",
                            None
                            ),

        "ZBK.111.0001A": (  30,
                            "Stoller",
                            "Sex and Gender("+patSubSep+patVol+patTwo+")",
                            "(1975)",
                            None
                            ),

        "ZBK.113.0001A": (  30,
                            "Stolorow",
                            "Contests of being("+patSubSep+" The intersubjective foundations of psychological life)?",
                            "(1992)",
                            None
                            ),

        "ZBK.131.0000A": (  30,
                            "Bodtker",
                            "Beyond Words",
                            "(1990)",
                            None
                            ),

        "ZBK.132.0000A": (  30,
                            "Glover",
                            "Psychoanalytic Aesthetics",
                            "(2008)",
                            None
                            ),

        "ZBK.133.0000A": (  30,
                            "Harris",
                            "The Tavistock Model",
                            "(1991)",
                            None
                            ),

        "ZBK.134.0000A": (  30,
                            "Harris",
                            "Emily Dickinson in Time",
                            "(1999)",
                            None
                            ),

        "ZBK.135.0000A": (  30,
                            "Harris",
                            "Thinking about lnfants and Young Children",
                            "(1975|1983)",
                            None
                            ),

        "ZBK.136.0000A": (  30,
                            "Harris",
                            "Your Teenager",
                            "(1969|2007)",
                            None
                            ),

        "ZBK.137.0000A": (  30,
                            "Jain",
                            "The Mind's Extensive View",
                            "(1991)",
                            None
                            ),

        "ZBK.138.0000A": (  30,
                            "Meltzer",
                            "The\s+Psycho[\s\-]?analytic(al)? Process",
                            "(1967)",
                            None
                            ),

        "ZBK.139.0000A": (  30,
                            "Meltzer",
                            "Sexual States of Mind",
                            "(1967|1968|1971|1972|1973|1979)",
                            None
                            ),

        "ZBK.140.0000A": (  30,
                            "Meltzer",
                            "The Kleinian Development",
                            "(1978)",
                            None
                            ),

        "ZBK.141.0000A": (  30,
                            "Meltzer",
                            "Explorations in Autism",
                            "(1975)",
                            None
                            ),

        "ZBK.142.0000A": (  30,
                            "Meltzer",
                            "Dream-?Life",
                            "(1983|1984)",
                            None
                            ),

        "ZBK.143.0000A": (  30,
                            "Meltzer",
                            "Studies in Extended Metapsychology",
                            "(1986)",
                            None
                            ),

        "ZBK.144.0000A": (  30,
                            "Meltzer",
                            "The\s+Claustrum",
                            "(1990|1992)",
                            None
                            ),

        "ZBK.145.0000A": (  30,
                            "Meltzer",
                            "Adolescence(: Talks and Papers)?",
                            "(2011)",
                            None
                            ),

        "ZBK.146.0000A": (  30,
                            "Meltzer",
                            "The Apprehension of Beauty",
                            "(1988|1995|2008)",
                            None
                            ),

        "ZBK.147.0000A": (  30,
                            "Negri",
                            "The Story of lnfant Development",
                            "(2007)",
                            None
                            ),

        "ZBK.148.0000A": (  30,
                            "Negri",
                            "The Newborn in the lntensive Care Unit",
                            "(1994)",
                            None
                            ),

        "ZBK.149.0000A": (  30,
                            "Piontelli",
                            "Backwards in Time",
                            "(1985)",
                            None
                            ),

        "ZBK.150.0000A": (  30,
                            "Sanders",
                            "A Matter of lnterest",
                            "(1986)",
                            None
                            ),
        "ZBK.151.0000A": (  30,
                            "Sanders",
                            "Nine Lives: the emotional experience",
                            "(1999)",
                            None
                            ),
        "ZBK.152.0000A": (  30,
                            "Williams",
                            "The Chamber of Maiden Thought",
                            "(1991)",
                            None
                            ),
        "ZBK.153.0000A": (  30,
                            "Williams",
                            "A Strange Way of Killing",
                            "(1987)",
                            None
                            ),
#        "ZBK.154.0001A": (  30,
#                            "Williams",
#                            "A Trial of Faith: Horatio's story",
#                            "(1997)",
#                            None
                            #),
        "ZBK.155.0000A": (  30,
                            "Williams",
                            "The Vale of Soulmaking",
                            "(2005)",
                            None
                            ),
        "ZBK.156.0000A": (  30,
                            "Williams",
                            "The Aesthetic Development: The poetic spirit",
                            "(2009)",
                            None
                            ),
        # IPL ************************************************************************************************
        "IPL.002.0000A": (  30,
                            ferencziS,  #"Ferenczi, S., Abraham, K., Simmel, E. and Jones, E.",
                            patPsychoanalysis+patAnd+"\s+(the\s+?)?War\s+Neuros(i|e)s",
                            "(1921)",
                            None
                            ),


        "IPL.022.0000A": (  30,
                            kleinM,
                            patThe+patPsychoanalysis+"  of Children",                                    #checked
                            "(1932|1937|1948|1963)",
                            None
                            ),

        "IPL.045.0000A": (  30,
                            ferencziS,
                            "First  Contributions? to "+patPsychoanalysis,
                            "(1952)",
                            None
                            ),

        "IPL.052.0000A": (  30,
                            rickmanJ, #"Rickman, J.",
                            "Selected Contributions "+patTo+" "+patPsychoanalysis,     #checked
                            "(1957|1951)",
                            None
                            ),

        "IPL.055.0000A": (  30,                                                             #checked
                            kleinM,
                            "Narrative  of a Child Analysis("+dashSep+" "+patThe+" Conduct of the "+patPsychoanalysis+" of Children (as seen)? in the Treatment of a "+patTen+" year[ \-]old Boy.)?",
                            "(196[0-1])",
                            None
                            ),

        "IPL.059.0000A": (  30,
                            mengH+"|freud|pfister", #"Meng, H.  and Freud, E. L.",
                            patPsychoanalysis+" "+patAnd+"  Faith("+patSubSep+" "+patThe+" (Letters of )?Sigmund Freud"+patAndTo+" O(\.?|skar) Pfister)?|"+patThe+" (Letters of )?Sigmund Freud"+patAndTo+" O(\.?|skar) Pfister|Briefe|Briefwechsel",   #checked
                            "(1963|192[0-9])",
                            None
                            ),

        "IPL.064.0000A": (  30,
                            winnicott,
                            patThe+"Maturational Process(es)? "+patAndThe+" Facilitating Environment("+patSubSep+"  Studies in the Theory of Emotional Development)?",
                            "(195[7-8]|196[0-9])[a-z]?",
                            None
                            ),

        "IPL.073.0000A": (  30,
                            rackerH, #"Racker,  H.",
                            "Transference "+patAndTo+"  Counter"+patDash+"transference",       #checked
                            "(1988|1968|1960|1985|1957|1958)",
                            None
                            ),

        "IPL.076.0000A": (  30,
                            milnerM+"|Kahn|khan",
                            patThe+"Hands?  of the Living Gods?("+patSubSep+" An Account of a "+patPsychoanalytic+" Treatment)?",    #Checked
                            "(1969)",
                            None
                            ),

        "IPL.079.0000A": (  30,
                            bowlbyJ,
                            "Attachment( and Loss)?("+patPunc+" "+patVol+patOne+"("+patPunc+" Attachment)?)?",
                            "(1969|1982|1959)",
                            None
                            ),


        "IPL.084.0000A": (  30,
                            "Freud|Zweig",
                            patThe+"Letters of  Sigmund Freud "+patAndTo+" Arnold Zweig",
                            "(1970|19[0-9][0-9])",
                            None
                            ),

        "IPL.087.0000A": (  30,
                            winnicott,
                            "Therapeutic Consultations in Child Psychiatry.",
                            "(1971)",
                            None
                            ),

        "IPL.089.0000A": (  30,
                            pfeifferE+"|Freud|Andreas"+dashSep+"Salom", #"Pfeiffer, E.",
                            "Sigmund Freud  "+patAndTo+" Lou Andreas"+dashSep+"Salom([\xef\bf\bde]|&eacute;)("+patSubSep+"Letters)?",    #checked
                            "(1963|1972|1966)",
                            None
                            ),

        "IPL.094.0000A": (  30,
                            laplancheJ, #"Laplanche, J. and Pontalis, J. B.",
                            patThe+"Language of "+patPsychoanalysis+"",
                            "(1973|1975|1967)",
                            None
                            ),

        "IPL.095.0000A": (  30,
                            bowlbyJ,
                            "(Attachment and Loss("+patPunc+" "+patVol+patTwo+"("+patPunc+" Separation"+patPunc+" Anxiety"+patAnd+" Anger)?)?)|(Separation"+patPunc+" Anxiety"+patAnd+" Anger)",   # should be ok because vols have diff dates
                            "(1973|1975|1999)",
                            patVol+patTwo
                            ),
        "IPL.100.0000A": (  30,
                            winnicott,
                            "(Collected[ ]+Papers:?[ ]+|In:?\s+)?" + "Through\s+P(ae|e)diatrics\s+to\s+"+patPsychoanalysis,
                            "(193[1-9]|194[0-9]|195[0-9]|1975)",
                            None
                            ),

        "IPL.104.0000A": (  30,
                            kleinM,
                            "Envy and Gratitude("+patAnd+"  Other Works( 1946"+dashSep+"(19)?63)?)?",     #checked
                            "(194[6-9]|1977|1964|195[0-9]|1975)",
                            None
                            ),

        "IPL.105.0000A": (  30,
                            groddeckG,
                            patThe+"Meaning of  Illness(:? Selected "+patPsychoanalytic+" Writings Including his Correspondence with Sigmund Freud)?",
                            "(1977)",
                            None
                            ),

        "IPL.107.0001A": (  30,
                            winnicott,
                            "The Piggle("+patSubSep+" An Account of the "+patPsychoanalytic+" Treatment of  a Little Girl: Edited by Ishak Ramzy)?",
                            "(1980)",
                            None
                            ),

        "IPL.109.0000A": (  30,
                            bowlbyJ,
                            "(Attachment and Loss("+patPunc+" "+patVol+patThree+"("+patPunc+" Loss"+patPunc+" Sadness"+patAnd+" Depression)?)?)|(Loss"+patPunc+" Sadness"+patAnd+"  Depression)",  # should be ok because vols have diff dates
                            "(1980)",
                            patVol+patThree
                            ),

        "IPL.115.0001A": (  30,
                            winnicott,
                            "Holding and Interpretation("+patSubSep+" Fragment  of An Analysis)?",
                            "(1986)",
                            None
                            ),

        "IPL.118.0000A": (  30,
                            anzieuD,
                            "(Freud"+patApos+"s Self"+dashSep+"Analys[ie]s)|(L"+patApos+"auto-analyse de freud)",          #checked
                            "1986|1959|1975|1988",
                            None
                            ),

        # NLP ************************************************************************************************
        "NLP.001.0000A": (  30,
                            rosenfeldH, #"Rosenfeld, H.",    #checked
                            "Impasse and Interpretation("+patSubSep+" Therapeutic and anti-therapeutic  factors in the "+patPsychoanalytic+" treatment of psychotic, borderline, and neurotic patients)?",
                            "(1987)",
                            None
                            ),

        "NLP.003.0000A": (  30,
                            milnerM,
                            patThe+"Suppressed  Madness of Sane Men",    #Checked
                            "(1987)",
                            None
                            ),

        "NLP.005.0000A": (  30,
                            matteblancoI+"|(Rayner|Tuckett)",
                            "Thinking\,? Feeling\,? (and)?  Being("+patSubSep+" Clinical Reflections on the Fundamental Antinomy of Human Beings and World)?",         #checked
                            "(1988|1989)",
                            None
                            ),

        "NLP.009.0001A": (  30,
                            "feldman|spillius|joseph",  #"Feldman, M. and Spillius, E. B.",
                            "Psychic Equill?ibrium  "+patAnd+" Psychic Change("+patPunc+" Selected Papers of Betty Joseph)?",
                            "(1975|198[0-9]|199[0-3])",
                            None
                            ),

        "NLP.011.0000A": (  30,
                            kingP+"|Steiner|Glover|Freud|Hoffer", #"King, P. and Steiner, R.",
                            patThe+"Freud"+patDashSlash+"Klein  Controversies("+patSubSep+" 1941"+dashSep+"(19)?45)?",
                            "(1991|1990|194[1-5])",
                            None
                            ),

        "NLP.014.0000A": (  10,
                            andersonR+"|britton|feldman|Spillius|steiner|malcom|O.?Shaughnessy|riesenberg",
                            "Clinical Lectures  on Klein"+patAnd+" Bion",              #checked
                            "1992|1991",
                            None
                            ),

        # SE ************************************************************************************************
        "SE.014.0000A": (   9,
                            "freud|Strachey|Tyson",
                            "(\bSE\b|\&SE\;|(S\.E\.)|(Std\.|((Stand(\.|ard)))\s+Ed(\.|ition|it\.)),?)",
                            "(1915|1957|1985|1986|2000)",
                            None
                            ),

        # Future <be id = "B004"> <a> <l>Fairbairn</l>, W.R.D.</a> (<y>1954</y>). <t>An Object Relations Theory of the Personality</t>.  New York: <bp>Basic Books</bp>.</be>
        # Future <be id = "B004"> <a> <l>Fairbairn</l>, W.R.D.</a> (<y>1954</y>). <t>An Object Relations Theory of the Personality</t>.  New York: <bp>Basic Books</bp>.</be>
        # Ferenczi, S., Abraham, K., Simmel, E. and Jones, E. (1921). Psychoanalysis and the War Neurosis. Int. Psycho-Anal. Lib. , The International Psycho-Analytical Press, London, Vienna, New York

    }

    #--------------------------------------------------------------------------------
    def __init__(self, biblioDB=None):
        """
        Initialize the PEPBooks class and load book patterns
        """
        # import libPEPBiblioDB

        self.refBookList = None

        # use the class to hold this initialized global data
        try:
            if self.__class__.initd == True:
                #"Already initd."
                pass
        except:
            self.__class__.initd = True
            self.__class__.bookRGXList = []
            #"Initializing Patterns..."
            for key, nTup in self.bookPatterns.items():
                minMatchLen, authPat, titlePat, yearPat, extraPat = nTup
                authPat = re.sub("\s+", r"\\s+", authPat)
                titlePat = re.sub("\s+", r"\\s+", titlePat)
                if 0:
                    print(80*"#")
                    print("Key: ", key)
                    print("TitlePattern: ", titlePat)
                    print("AuthorPattern: ", authPat)
                yearPat = re.sub("\s+", r"\\s+", yearPat)
                rgxAuth = re.compile(authPat, re.IGNORECASE)
                rgxTitle = re.compile(titlePat, re.IGNORECASE)
                rgxYear = re.compile(yearPat+"[a-d]?", re.IGNORECASE) # allow for when they add a suffix
                if extraPat != None:
                    rgxExtra = re.compile(extraPat, re.IGNORECASE)
                else:
                    rgxExtra = None
                self.__class__.bookRGXList.append((minMatchLen, key, rgxAuth, rgxTitle, rgxYear, rgxExtra))

            self.__class__.bookRGXList.sort()      # use the first argument of the tuple to order them
            self.__class__.bookRGXList.reverse()   # larger numbers first (use this to put shorter titles LAST!!! (can't use length because they are expressions, not titles.)
                                                                # this is the pattern length, and may not
                                                                # truly reflect the string len!

            # Take parameter at face value, init later when needed.
            #if isinstance(biblioDB, libPEPBiblioDB.BiblioDB):
                #self.__class__.biblioDB = biblioDB
            #else:
                #self.__class__.biblioDB = None

            #self.HTMLParser = html.parser.HTMLParser()

    #--------------------------------------------------------------------------------
    def __repr__(self):
        """
        Get the bibentry property (which is stored in the dict)
        """
        retVal = ""
        for (key, nTup) in self.bookPatterns.items(): # for each PEP Book
            retVal += repr(nTup[1]) + "\n"
        return retVal

    #--------------------------------------------------------------------------------
    def __len__(self):
        """
        Get the bibentry property (which is stored in the dict)
        """
        return len(self.bookRGXList)

    #--------------------------------------------------------------------------------
    def getPEPBookCodeXML(self, theReference, refText = None, sRatio = .87654321):
        """
        Identify the reference in the strBookReference XML and return the
            associated bookID if there is one

        This is used for XML based references (most accurate)

        """
        ## at this point, only XML falls through
        #bookMarkup = self.LastPYXRefTree.getElementTextSingleton(SUB, E("bst|bp|bsy|bpd"))
        #journal = self.LastPYXRefTree.getElementTextSingleton(SUB, E("j"))
        #if not opasgenlib.is_empty(bookMarkup) and not opasgenlib.is_empty(journal):
            ##print "This is probably a journal (skipped): ", journal
            #return retVal
        ##else:
        ## this could be one of the trillion mistagged references.  Try importing journal as the fallback for bst, sourcetitlecited and see if that works.

        ## see if it's already marked
        #rxVal = self.LastPYXRefTree.getCurrAttrVal("rx|rxp")
        #if gDbg1: print("Pyxtree Reference: ", repr(self.LastPYXRefTree))
        ##if refText == None: # so if it's already extracted, we don't need to do it again
            ##refText = sciPEPSupport.normalizeTextEntities(self.LastPYXRefTree.getCurrElementText(notIncludingTagRegex=("ftnref|ftnx|impx")), self.LastPYXRefTree.entityTrans)

        #refObj = self.parseXMLAuthorYearTitle(self.LastPYXRefTree)
        #authors = refObj.get(gConst.AUTHORS, refObj.get(gConst.BAUTHORS))
        #year = refObj.get(gConst.YEAR, refObj.get(gConst.BOOKYEAR))
        #articleTitle =  refObj[gConst.TITLE]
        #sourceTitle =  refObj.get(gConst.SOURCETITLECITED, refObj.get(gConst.SOURCETITLESERIES))
        #if gDbg1:
            #print("Title: ", articleTitle)
            #print("SourceTitle: ", sourceTitle)
            #print("Authors: ", authors)
            #print("SourceYear: ", year)
            #print("RX Val: ", rxVal)

        ## match the book info against the regular expressions. It either matches (100%), or not.  Returns matching ID or none
        #if not opasgenlib.is_empty(sourceTitle):
            #matchID = self.findBookCodeByTitleAuthorYear(strTitle=sourceTitle, strAuth=authors, strYear=year, strReference=refText)
        #else:
            ## there's no source title, so use title to compare
            #matchID = self.findBookCodeByTitleAuthorYear(strTitle=articleTitle, strAuth=authors, strYear=year, strReference=refText)

        ## matchID is now a tuple (9/2011) so deal with that
        #if matchID[0] != None:
            ## we found that the source is a book.  So look up the article to see if we can go directly to the page.
            #if not opasgenlib.is_empty(articleTitle):
                #if gDbg1:
                    #print(40*"%X")
                    #print("Found the book as a source.  Looking for the article/section: '%s'" % articleTitle)
                #matchPageID, sRatio2 = self.findCompilationBooks(self.biblioDB, articleTitle, targetArticleID = matchID[0])
                #if matchPageID != None:
                    ## use this instead.
                    #if gDbg1:
                        #print("Using page match instead.")
                    #matchID = matchPageID
                    #sRatio = sRatio2
                #else:
                    #if gDbg1: print("...article page not found.  Using book reference.")

            #retVal = matchID, sRatio, refObj

        #else:
            ## we didn't find a book source
            #if gDbg1: print("Not a PEP book source.  No matches...", sourceTitle)

        #return retVal
        pass
    
    #--------------------------------------------------------------------------------
    def getPEPBookCodeStr(self, theReference, sRatio = RX_CONFIDENCE_PROBABLE):
        """
        Identify the reference in the unstructured strBookReference and return the
            associated bookID if there is one

        This is used for nonXML based references (less accurate than using findBookCodeByTitleAuthorYear
            with the "separated" title, author, data.

        """
        # Check an untagged reference using a full regular expression to identify a PEP
        # Book reference
        retVal = None, None, None
        matchID = None
        
        # self.LastPYXRefTree = None # called with string, so reset tree.
        # fall through and process string

        if opasgenlib.is_empty(theReference):
            return retVal

        if gDbg1: logger.info("getPEPBookCodeStr matching: ", theReference)

        for dummy, bookID, rgxAuth, rgxTitle, rgxYear, rgxExtra in self.bookRGXList: # shows in Wing as undefined, but defined at class level
            match = False
            #"Book Pattern being searched: ", rgxTitle.pattern

            m = rgxTitle.search(theReference)
            if m != None:
                if gDbg1: logger.info("***%s Matched Title.  (Pattern: %s)" % (bookID, rgxTitle.pattern))
                match = True
            else:
                continue # keep looking

            m = rgxAuth.search(theReference)
            if m != None:
                if gDbg1: logger.info("**%s Matched Author.  (Pattern: %s)" % (bookID, rgxAuth.pattern))
            else:
                match = False
                if gDbg1: logger.info("Didn't match Author: ", bookID, rgxAuth.pattern)
                continue # (must keep looking)

            m = rgxYear.search(theReference)
            if m != None:
                if gDbg1: logger.info("*%s Matched Year.  (Pattern: %s)" % (bookID, rgxYear.pattern))
            else:
                match = False
                if gDbg1: logger.info("Didn't match Year: ", rgxYear.pattern)
                continue # (must keep looking)

            # Add an extra search of the entire reference; this can be used to "whittle down" false positives.
            if isinstance(rgxExtra, re.Pattern):
                m = rgxExtra.search(theReference)
                if m != None:
                    if gDbg1: logger.info("*%s Matched Extra Pattern: %s)" % (bookID, rgxExtra.pattern))
                else:
                    match = False
                    if gDbg1: logger.info("Didn't match Extra Pattern: ", rgxExtra.pattern)
                    continue # (must keep looking)

            if match == True:
                matchID = bookID
                break

        if matchID != None:
            retVal = matchID, sRatio, None
        else:
            retVal = None, None, None

        return retVal

    #--------------------------------------------------------------------------------
    def findBookCodeByTitleAuthorYear(self, strTitle, strAuth=None, strYear=None, strReference=None):
        """
        Identify the reference given by strTitle, strAuth and strYear using regular
            expressions defined in the instance.
        strReference is used to search the "Extra" regular exppression pattern.  This
            can be used to eliminate false positives.
        """
        # Check an untagged reference using a full regular expression to identify a PEP
        # Book reference

        retVal = None, None, None
        if gDbg1:
            print(80*"-")
            print("Searching for: ", strTitle)

        if opasgenlib.is_empty(strAuth) and opasgenlib.is_empty(strYear):
            if gDbg1: print("Neither an author nor a year, matching not allowed (too many false positives).")
            return retVal

        for dummy, bookID, rgxAuth, rgxTitle, rgxYear, rgxExtra in self.bookRGXList:
            #print "Book Pattern being searched: ", rgxTitle.pattern
            match = False
            matchCount = 0
            retVal = None, None, None
            m = rgxTitle.search(strTitle)
            if m != None:
                retVal =  bookID, .75, None
                if gDbg1: print("***%s Matched Title: %s.  (Pattern: %s)" % (bookID, strTitle, rgxTitle.pattern))
                match = True
                matchCount += 1
            else:
                continue # keep looking

            if not opasgenlib.is_empty(strAuth):
                m = rgxAuth.search(strAuth)
                if m != None:
                    if gDbg1: print("**%s Matched Author: %s.  (Pattern: %s)" % (bookID, strAuth, rgxAuth.pattern))
                    matchCount += 1
                    retVal =  bookID, .80, None
                else:
                    match = False
                    if gDbg1: print("Didn't match Author: ", bookID, strAuth, rgxAuth.pattern)
                    continue # (must keep looking)

            if not opasgenlib.is_empty(strYear):
                m = rgxYear.search(strYear)
                if m != None:
                    if gDbg1: print("*%s Matched Year: %s.  (Pattern: %s)" % (bookID, strYear, rgxYear.pattern))
                    retVal =  bookID, .85, None
                    matchCount += 1
                else:
                    match = False
                    if gDbg1: print("Didn't match Year: ", strYear, rgxYear.pattern)
                    continue # (must keep looking)

            # Add an extra search of the entire reference; this can be used to "whittle down" false positives.
            if not opasgenlib.is_empty(rgxExtra) and not opasgenlib.is_empty(strReference):
                m = rgxExtra.search(strReference)
                if m != None:
                    if gDbg1: print("*%s Matched Extra Pattern: %s)" % (bookID, rgxExtra.pattern))
                    retVal =  bookID, .875, None
                    matchCount += 1
                else:
                    match = False
                    if gDbg1: print("Didn't match Extra Pattern: ", rgxExtra.pattern)
                    continue # (must keep looking)

            # may want to change logic to use count...right now, it has to match everything supplied.
            if match == True:
                break

        # return book id or none
        return retVal

    #--------------------------------------------------------------------------------
    def getPEPBookCode(self, theReference, refText = None, sRatio = .87654321):
        """
        Identify the reference in the theReference XML and return the
            associated bookID if there is one

        This is used XML based references (most accurate
        """

        # self.LastPYXRefTree = None # reset saved tree.
        matchID, sRatio, refobj = self.getPEPBookCodeXML(theReference=theReference, refText=refText)

        return matchID, sRatio, refobj


#==================================================================================================
# Main Standalone (Test) Routines
#==================================================================================================
if __name__ == "__main__":

    import sys
    import doctest

    doctest.testmod()
    print ("All Tests Complete. Fini!")
    sys.exit()


