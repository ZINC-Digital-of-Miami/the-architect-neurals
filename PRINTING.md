# Print / Save PDF

The existing Print button calls the browser's standard print command on the current
page. Choose a printer or Save as PDF in the browser's print sheet. It is separate
from Share and does not fetch a stored PDF or a print catalog.

The existing `site/print/` PDFs remain as historical exports. They are not used by
the print button or regenerated for routine changes. The local guard still checks
their recorded bytes and hashes; the live release receipt verifies the current
pages and assets without downloading those archived PDF binaries.

An embedded browser may not offer a native print sheet. Open the live URL in a full
browser to use its standard print command. Preserve the authored report and map when
checking print layout.
