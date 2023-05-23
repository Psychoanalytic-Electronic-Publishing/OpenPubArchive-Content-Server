# !/usr/bin/python
# Adding a watermark to a multi-page PDF
import sys
import os

import logging
logger = logging.getLogger(__name__)

from pdfrw import PdfReader, PdfWriter, PageMerge
from fpdf import FPDF, HTMLMixin
#from xhtml2pdf import pisa             # for HTML 2 PDF conversion
# import opasXMLHelper as opasxmllib
import stdMessageLib
import opasConfig
import localsecrets

COPYRIGHT_PAGE = "pepwebcopyrightpage.pdf"
# copyright_usage = f"For use only by {username}. Reproduction prohibited. Usage subject to PEP terms & conditions (see <a href='https://terms.pep-web.org'>terms.pep-web.org</a>)."

import tempfile
import ntpath

class PDF(FPDF, HTMLMixin):
    def header(self):
        # Logo
        # Arial bold 15
        pass # skip for now
        #try:
            #header_copyright = f"Copyrighted Material. For use only by {self.username_to_set}. Reproduction prohibited. Usage subject to PEP terms & conditions (see terms.pep-web.org)."
            #self.set_font('Helvetica', 'B', 4) # font size 6, B for bold
            #self.set_y(2) # self.set_y(22)
            #self.set_x(18)
            #self.cell(w=0, h=10, txt=header_copyright, border=0, ln=0, link="http://terms.pep-web.org")
            ##self.set_y(25)
            ##self.image('peplogosmall.jpg', x=10, y=25, w=4) # position, 10, 8, size 9
            ## Line break
            #self.ln(20)
        #except Exception as e:
            #logger.error(f"Cannot add Copyright Header: {e}")

    # Page footer
    def footer(self):
        try:
            # Position at 1.5 cm from bottom
            self.set_y(-11)
            self.set_x(10)
            # Arial italic 8
            self.set_font('Helvetica', 'B', 6) # font size 5, B for bold
            header_copyright = f"Copyrighted Material. For use only by {self.username_to_set}. Reproduction prohibited. Usage subject to PEP terms & conditions (see terms.pep-web.org)."
            # use same header text as footer, depending on page size, more reliable in footer
            self.cell(w=0, h=10, txt=header_copyright, border=0, ln=0, link="http://terms.pep-web.org", align="C")
            # self.cell(0, 10, f'Original Journal Reprint -- Downloaded from PEP-Web by {self.username_to_set}', 0, 0, 'C')
        except Exception as e:
            logger.error(f"Cannot add Copyright Footer: {e}")                      

def get_append_page(new_page_filename):
    fpdf = FPDF()
    fpdf.add_page()
    new_page = PdfReader(new_page_filename)
    return new_page.pages[0]

def write_copyright_page(username="PEP"):
    """
    This is very limited styling using fpdf2
    Should try to replace fpdf2 here with weasyprint to properly print the HTML
    
    NOT YET USED.
    
    >>> filename = write_copyright_page(username="Neil Shapiro")
    >>> print (filename)
    
    """
    try:
        file_base = next(tempfile._get_candidate_names()) + ".pdf"
        copyright_file = os.path.join(tempfile.gettempdir(), file_base)
        pdf = PDF()
        pdf.username_to_set = username
        pdf.add_page()
        pdf.set_font("Times", size=12)
        pdf.set_text_color(0,0,0)
        #pdf.write_html(COPYRIGHT_PAGE_HTML)
        copypage = stdMessageLib.COPYRIGHT_PAGE_HTML.replace("[[username]]", username)
        pdf.write_html(copypage)
        pdf.output(copyright_file, 'F')
    except Exception as e:
        logger.error(f"Error writing PDF Copyright File: {e}")
    else:
        logger.debug(f"Wrote PDF Copyright File: {copyright_file}")
    
    return copyright_file

def stampcopyright(username, input_file, top=True, bottom=True, suffix=""):
    def new_page():
        fpdf = FPDF()
        fpdf.add_page()
        fpdf.set_font("helvetica", size=36)
        fpdf.text(50, 50, "Hello!")
        reader = PdfReader(fdata=bytes(fpdf.output()))
        return reader.pages[0]    
    # generate 'watermark' merge file
    try:
        headerfooterfile_base = next(tempfile._get_candidate_names()) + ".pdf"
        headerfooterfile = os.path.join(tempfile.gettempdir(), headerfooterfile_base)
        pdf = PDF()
        #pdf.font_size_pt = 24
        #pdf.font_family = "helvetica"
        pdf.username_to_set = username
        pdf.alias_nb_pages("{nb}")
        pdf.add_page()
        pdf.output(headerfooterfile, 'F')
    except Exception as e:
        logger.error(f"Error writing PDF HeaderFooter File: {e}")
    else:
        logger.debug(f"Wrote PDF HeaderFooter File: {headerfooterfile}")
        if opasConfig.LOCAL_TRACE: print (f"Wrote PDF HeaderFooter File: {headerfooterfile}")
        
    # now merge with download file
    #pisa.showLogging() # debug only
    input_file_basename = ntpath.basename(input_file)
    try:
        input_file_basename = os.path.splitext(input_file_basename)[0]
    except Exception as e:
        logger.info(f"Error removing extension: {e}")
        
    output_file = None
    if suffix != "":
        sep = "-"
    else:
        sep = ""
        
    try:
        output_file = os.path.join(tempfile.gettempdir(), input_file_basename + f"{sep}{suffix}.pdf")
        logger.debug(f"Writing Stamped Copyright Output File: {output_file}")
        if opasConfig.LOCAL_TRACE:
            print(f"Writing Stamped Copyright Output File: {output_file}")
        watermark_file = headerfooterfile
        

        # define the reader and writer objects
        reader_input = PdfReader(input_file)
        writer_output = PdfWriter()
        watermark_input = PdfReader(watermark_file)
        watermark = watermark_input.pages[0]
        
        # go through the pages one after the next
        for current_page in range(len(reader_input.pages)):
            merger = PageMerge(reader_input.pages[current_page])
            merger.add(watermark).render()

        if 0: # doesn't work
            append_page_path = localsecrets.PDF_ORIGINALS_PATH + localsecrets.PATH_SEPARATOR + COPYRIGHT_PAGE
            append_page = get_append_page(append_page_path) # append at end
            reader_input.pages.append(append_page)
        
        # write the modified content to disk
        writer_output.write(output_file, reader_input)
        
        if 0: # doesn't work...work on this later
            #  add final copyright page
            writer = PdfWriter(trailer=PdfReader(output_file))
            try:
                append_page_path = localsecrets.PDF_ORIGINALS_PATH + localsecrets.PATH_SEPARATOR + COPYRIGHT_PAGE
                append_page = get_append_page(append_page_path) # append at end
                writer.pagearray.append(append_page)
                writer.pagearray.append(new_page())
            except Exception as e:
                logger.error(f"Could not access copyright page in {append_page_path} (error:{e})")
            else:
                print ("Success writing new page")
    
            # final write
            writer.write(output_file)
        
    except Exception as e:
        logger.error(f"Could not add copyright page for user {username} to {suffix} PDF; returning without marks (error:{e})")
        output_file = input_file
    else:
        logger.debug(f"Copyright info added for user {username} to Original PDF")
        
    return output_file
    
if __name__ == "__main__":
    print (40*"*", "opasCentralDBLib Tests", 40*"*")
    print (f"Running in Python {sys.version_info[0]}.{sys.version_info[1]}")
   
    logger = logging.getLogger(__name__)
    # extra logging for standalong mode 
    # logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s %(name)s %(lineno)d - %(levelname)s %(message)s')    
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    
    # doctest.testmod()    
    # stampcopyright("Neil Shapiro", input_file="../IJP.077.0217A.pdf")
    print ("Fini. Tests complete.")
    
    