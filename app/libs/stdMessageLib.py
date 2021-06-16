"""
This file contains standard messages and pages to be used by the server
"""
# Note fpdf does not support type in lists, or much styling!
COPYRIGHT_PAGE_HTML = """
<html>
<body>
  <section>
  <font color=#000000>
    <h2 style="color:black;">Authorized Users</h2>
    <p>For use only by [[username]]. Reproduction prohibited. Usage subject to PEP terms &amp; conditions
(see <a href='https://terms.pep-web.org'>terms.pep-web.org</a>).</p>
  </section>
  <section>
    <h2>PEP-Web Copyright</h2>
    <p><strong>Copyright.</strong> The PEP-Web Archive is protected by
United States copyright laws and international treaty provisions.</p>
    <ol>
     <li>All copyright (electronic and other) of the text, images, and photographs of the
publications appearing on PEP-Web is retained by the original
publishers of the Journals, Books, and Videos. Saving the
exceptions noted below, no portion of any of the text, images,
photographs, or videos may be reproduced or stored in any form
without prior permission of the Copyright owners.</li>
     <li>Authorized Uses.
Authorized Users may make all use of the Licensed Materials
as is consistent with the Fair Use Provisions of United States and
international law. Nothing in this Agreement is intended to limit
in any way whatsoever any Authorized User's rights under the
Fair Use provisions of United States or international law to use
the Licensed Materials.</li>
     <li>During the term of any subscription the Licensed Materials may be used for
    purposes of research, education or other non-commercial use as follows:
       <ol style="list-style-type:lower-alpha">
        <li>Digitally Copy. Authorized Users may download and digitally copy a reasonable
portion of the Licensed Materials for their own use only.
        </li>
        <li>Print Copy. Authorized Users may print (one copy per user) reasonable potions
of the Licensed Materials for their own use only.
        </li>
       </ol>
    </ol>
</section>
</body>
</html>
"""

OLD_COPYRIGHT_PAGE_HTML = """
                    <div class="copyrightpage">
                        <h1 class="main_title">PEP-Web Copyright</h1>
                        <!--UserInfoHere-->
                        <div class="entry-content">
                        <p><strong>Copyright.</strong> The PEP-Web Archive is protected by
                        United States copyright laws and international treaty
                        provisions.</p>
                        <p style="padding-left: 28px; text-indent: -28px;">
                        <b>(1)</b> All copyright
                        (electronic and other) of the text, images, and photographs of the
                        publications appearing on PEP-Web is retained by the original
                        publishers of the Journals, Books, and Videos. Saving the
                        exceptions noted below, no portion of any of the text, images,
                        photographs, or videos may be reproduced or stored in any form
                        without prior permission of the Copyright owners.</p>
                        <p style="padding-left: 28px; text-indent: -28px;">
                        <b>(2)</b> Authorized
                        Uses. Authorized Users may make all use of the Licensed Materials
                        as is consistent with the Fair Use Provisions of United States and
                        international law. Nothing in this Agreement is intended to limit
                        in any way whatsoever any Authorized User&rsquo;s rights under the
                        Fair Use provisions of United States or international law to use
                        the Licensed Materials.</p>
                        <p style="padding-left: 28px; text-indent: -28px;">
                        <b>(3)</b> During the
                        term of any subscription the Licensed Materials may be used for
                        purposes of research, education or other non-commercial use as
                        follows:</p>
                        <p style="padding-left: 52px; text-indent: -38px;">a. Digitally
                        Copy. Authorized Users may download and digitally copy a reasonable
                        portion of the Licensed Materials for their own use only.</p>
                        <p style="padding-left: 52px; text-indent: -38px;">b. Print Copy.
                        Authorized Users may print (one copy per user) reasonable potions
                        of the Licensed Materials for their own use only.</p>
                        
                        <p style="margin:inherit"><strong>Copyright Warranty.</strong>
                        Licensor warrants that it has the right to license the rights
                        granted under this Agreement to use Licensed Materials, that it has
                        obtained any and all necessary permissions from third parties to
                        license the Licensed Materials, and that use of the Licensed
                        Materials by Authorized Users in accordance with the terms of this
                        Agreement shall not infringe the copyright of any third party. The
                        Licensor shall indemnify and hold Licensee and Authorized Users
                        harmless for any losses, claims, damages, awards, penalties, or
                        injuries incurred, including reasonable attorney's fees, which
                        arise from any claim by any third party of an alleged infringement
                        of copyright or any other property right arising out of the use of
                        the Licensed Materials by the Licensee or any Authorized User in
                        accordance with the terms of this Agreement. This indemnity shall
                        survive the termination of this agreement. NO LIMITATION OF
                        LIABILITY SET FORTH ELSEWHERE IN THIS AGREEMENT IS APPLICABLE TO
                        THIS INDEMNIFICATION.</p>
                        
                        <p style="margin:inherit"><strong>Commercial reproduction.</strong>
                        No purchaser or user shall use any portion of the contents of
                        PEP-Web in any form of commercial exploitation, including, but not
                        limited to, commercial print or broadcast media, and no purchaser
                        or user shall reproduce it as its own any material contained
                        herein.</p>
                        </div> <!-- .entry-content -->
                        </div>
"""
