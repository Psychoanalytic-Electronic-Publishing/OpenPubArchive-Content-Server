#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
opasConverters

Converter conveniece functions.

Added 2020-02-22 when debugging problem with converting html to pdf. But didn't use these from server.  Saved for later.

"""
from xhtml2pdf import pisa             # import python module
import base64

# Utility function
def convert_html_to_pdf(source_html, output_filename):
    """
    Convenience function to convert HTML to PDF.
    """
    # open output file for writing (truncated binary)
    result_file = open(output_filename, "w+b")

    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
                                source_html,                # the HTML to convert
                                dest=result_file)           # file handle to recieve result

    # close output file
    result_file.close()                 # close output file

    # return True on success and False on errors
    return pisa_status.err

def convert_image_to_data_image(image_filename):
    """
    To embed an image in the HTML, use retval as the
    source.
    """
    with open(image_filename, 'r+b') as content_file:
        image_data = content_file.read()        

    encoded = base64.b64encode(image_data).decode("utf8")
    ret_val = f'data:image/png;base64,{encoded}'
    
# Main program
if __name__ == "__main__":
    # Define your data
    source_html = "<html><body><p>To PDF or not to PDF</p></body></html>"
    output_filename = "test.pdf"
    pisa.showLogging()
    #source_file = "testpdf.html"
    #output_filename = "testpdf.pdf"
    #with open(source_file, 'r') as content_file:
        #content = content_file.read()    
    convert_html_to_pdf(content, output_filename)