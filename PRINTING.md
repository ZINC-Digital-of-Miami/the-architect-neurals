# Print artifacts

Print remains separate from Share. Supported browsers open their native print dialog. If the host does not start printing, the standalone print panel supplies a downloadable PDF and an option to open it. Native printing inside the Codex embedded browser is not provided by this website.

Rebuild the site and all printable documents before publishing a content or layout change:

```sh
node src/build_neural_map.js
python3 src/build_site3.py
node scripts/build_print_pdfs.cjs
bash check.sh
```

The PDF builder uses the configured local Codex Playwright runtime and installed Google Chrome. It starts its own temporary localhost server and closes it on completion. It derives pages, entity records, topic maps, and synthesis views from the current rendered site. Entity PDFs include all incident relationships and their attached evidence; secondary filters do not narrow the full entity document.

The manifest records rendering-input hashes, builder hash, PDF hashes, sizes, pages and route coverage. The release guard rejects stale inputs, missing routes, changed PDFs and unlisted files. PDF metadata is not deterministic, so validated print artifacts are checked separately from the deterministic HTML rebuild. Partial `--only` builds are for local inspection; the complete route catalog must pass before release.

Preserve the authored report. Print-only layout changes may reflow it, but must not remove content. Verify generated PDFs for readable text, complete report blocks, source links, selected-view identity and map evidence. A mocked `window.print()` call or a successful PDF export alone does not prove that a host opens its native print dialog.
