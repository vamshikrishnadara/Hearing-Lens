# Accessibility and readable results

The default light theme uses dark text on pale surfaces and dark teal action
buttons with white text. The configured body, link and button color pairs are
checked against the 4.5:1 normal-text contrast threshold. This is a bounded
check of configured colors, not a claim that the whole application conforms
to every WCAG criterion or every user-selected theme.

The app uses labeled upload, mapping and optional-input controls. Keyboard users
can open selectors with arrow keys, select with Enter, dismiss an open menu with
Escape, activate buttons with Enter and move between result tabs with arrow
keys. Leave a multiselect's popup with Escape before moving to the next control.

Charts have adjacent numeric tables. Statuses, missing fields, suppressed values
and model warnings are described in words, so meaning does not depend only on
color. Use the labeled CSV for a separate spreadsheet view, and the Word/PDF
brief for the concise narrative. Interactive table and screen-reader behavior
can vary by browser and Streamlit version; check the actual setup with the
people who will use it.

## Before presenting

- Check the upload, mapping, analysis, result tabs and downloads using only the
  keyboard. Confirm visible focus and readable labels.
- Inspect narrow and desktop layouts and enlarge the text. Use tables when a
  chart is difficult to read; do not remove the accompanying denominators.
- Check that alert text and links remain readable after any theme customization.
- Open the brief in the intended reader. A one-page layout and selectable text
  do not establish that a PDF has complete accessibility tagging.
- Ask participants which format they need. Offer the Word document or an
  explained text summary when that is more usable than the visual dashboard.

Reference: [W3C contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum).
