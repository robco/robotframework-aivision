*** Settings ***

Library  AIVision  platform=Manual  api_key=%{GEMINI_API}  base_url=https://generativelanguage.googleapis.com/v1beta/openai/  model=gemini-2.5-flash

*** Variables ***

${MERCK}     ${CURDIR}${/}res${/}merck.png
${MENU}      ${CURDIR}${/}res${/}menu.png
${TEMPLATE}  ${CURDIR}${/}res${/}ref_merck_app.png
${VIEW}      ${CURDIR}${/}res${/}act_merck_app.png

*** Test Cases ***

Check merck logo
   Verify That  ${MERCK}  Shows merck logo in black and green color in top left

Check merck logo ref
   @{screenshots}  Create List  ${MENU}  ${MERCK}
   Verify That  ${screenshots}  Describe both images are from the same page

Check merck menu template
   Verify Screenshot Matches Look And Feel Template  ${VIEW}  ${TEMPLATE}

Describe image
   Verify That  ${VIEW}  Describe content of the image
