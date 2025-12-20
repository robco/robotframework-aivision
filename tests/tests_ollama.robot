*** Settings ***

Library  AIVision  model=qwen3-vl:8b

*** Variables ***

${ACTUAL}       ${CURDIR}${/}res${/}main.png
${REFERENCE}    ${CURDIR}${/}res${/}ref_main.png

*** Test Cases ***

Check Wikipedia logo
   Verify That  ${ACTUAL}  Shows clear Wikipedia logo on top in the middle, logo text is clearly visible.

Check screenshots are from Wikipedia
   @{screenshots}  Create List  ${ACTUAL}  ${REFERENCE}
   Verify That  ${screenshots}  Provided screenshots are from Wikipedia main page.

Check Wikipedia main page corresponds to the template
   Verify Screenshot Matches Look And Feel Template  ${ACTUAL}  ${REFERENCE}
