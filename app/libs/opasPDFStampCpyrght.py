# !/usr/bin/python
# Adding a watermark to a multi-page PDF
import sys
import os
import logging
logger = logging.getLogger(__name__)

from pdfrw import PdfReader, PdfWriter, PageMerge
from fpdf import FPDF
#from xhtml2pdf import pisa             # for HTML 2 PDF conversion
import opasXMLHelper as opasxmllib
from stdMessageLib import COPYRIGHT_PAGE_HTML
COPYRIGHT_PAGE = "pepwebcopyrightpage.pdf"
import tempfile
import ntpath

class PDF(FPDF):
    def header(self):
        # Logo
        # Arial bold 15
        try:
            header_copyright = f"Copyrighted Material. For use only by {self.username_to_set}. Reproduction prohibited. Usage subject to PEP terms & conditions (see terms.pep-web.org)."
            self.set_font('Helvetica', 'B', 6) # font size 6, B for bold
            self.set_y(22)
            self.set_x(18)
            self.cell(w=0, h=10, txt=header_copyright, border=0, ln=0, link="http://terms.pep-web.org")
            self.set_y(25)
            self.image('peplogosmall.jpg', x=10, y=25, w=4) # position, 10, 8, size 9
            # Line break
            self.ln(20)
        except Exception as e:
            logger.error(f"Cannot add Copyright Header: {e}")

    # Page footer
    def footer(self):
        try:
            # Position at 1.5 cm from bottom
            self.set_y(-15)
            # Arial italic 8
            self.set_font('Helvetica', 'I', 4)
            # Page number
            self.cell(0, 10, f'Original Journal Reprint -- Downloaded from PEP-Web by {self.username_to_set}', 0, 0, 'C')
        except Exception as e:
            logger.error(f"Cannot add Copyright Footer: {e}")                      

def get_append_page(new_page_filename):
    fpdf = FPDF()
    fpdf.add_page()
    new_page = PdfReader(new_page_filename)
    return new_page.pages[0]

def stampcopyright(username, input_file):
    # generate 'watermark' merge file
    try:
        headerfooterfile = next(tempfile._get_candidate_names()) + ".pdf"
        pdf = PDF()
        pdf.username_to_set = username
        pdf.alias_nb_pages("{nb}")
        pdf.add_page()
        pdf.output(headerfooterfile, 'F')
    except Exception as e:
        logger.error(f"Error writing PDF HeaderFooter File: {e}")
    else:
        logger.info(f"Wrote PDF HeaderFooter File: {headerfooterfile}")
        
    # now merge with download file
    #pisa.showLogging() # debug only
    input_file_basename = ntpath.basename(input_file)
    try:
        input_file_basename = os.path.splitext(input_file_basename)[0]
    except Exception as e:
        logger.info(f"Error removing extension: {e}")
        
    output_file = None
    try:
        output_file = os.path.join(tempfile.gettempdir(), input_file_basename + "-pepweb.pdf")
        logger.info(output_file)
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
    
        # write the modified content to disk
        writer_output.write(output_file, reader_input)
        # add final copyright page
        #writer = PdfWriter(trailer=PdfReader(output_file))
        #writer.pagearray.append(get_append_page(COPYRIGHT_PAGE)) # append at end
        # final write
        #writer.write(output_file)
    except Exception as e:
        logger.error(f"Could not add copyright info for user {username} to Original PDF")
    else:
        logger.info(f"Copyright info added for user {username} to Original PDF")
        
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
    
    #import doctest
    #doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
    #doctest.testmod()    
    stampcopyright("Neil Shapiro", input_file="../IJP.077.0217A.pdf")
    print ("Fini. Tests complete.")
    
    