# Hearing Lens Dashboard Wireframe

The first-use path should move from upload to understandable results without requiring separate instructions.

## Screen 1 Upload and mapping

```text
+------------------------------------------------------------------+
| Hearing Lens                                                     |
| Upload comments and map the columns used in your file            |
+------------------------------------------------------------------+
| [ Choose CSV or XLSX ]                                           |
| Workbook sheet      [ Sheet 1 v ]                                |
| Comment text        [ response_text v ]   required               |
| Date or hearing     [ submitted_at v ]    optional               |
| Respondent ID       [ response_id v ]     optional               |
| Subgroup fields     [ ward ] [ role ]      optional               |
|                                                                  |
| Privacy: uploads are processed for this session and not saved.   |
|                                      [ Validate and analyze ]     |
+------------------------------------------------------------------+
```

## Screen 2 Results

```text
+------------------------------------------------------------------+
| File summary: 1,000 comments | 3 hearings | 4 subgroup fields    |
+------------------------------------------------------------------+
| Themes | Sentiment and Emotion | Timeline | Who Was Missing | ?   |
+------------------------------------------------------------------+
| Active panel                                                     |
|                                                                  |
| Clear chart or table                                             |
| Plain-language explanation                                      |
| Representative, redacted quotes when relevant                   |
|                                                                  |
+------------------------------------------------------------------+
| Downloads: [ Community brief DOCX ] [ PDF ] [ Labeled CSV ]      |
+------------------------------------------------------------------+
```

## Panel behavior

1. **Themes** shows 5 to 15 clusters, their share of comments, top keywords, and three redacted representative quotes.
2. **Sentiment and Emotion** shows distributions by theme and avoids implying more precision than the validation supports.
3. **Timeline** shows theme volume and sentiment by date or hearing. Without a mapped period field, it explains how to enable the panel.
4. **Who Was Missing** compares participation share with a user-supplied reference. Without subgroup or reference data, it explains what is needed.
5. **Open Questions** groups similar questions and highlights the three highest-ranked unanswered questions.

## Error and empty states

- Missing comment mapping: ask the user to select the column containing written responses.
- No usable rows: explain that the chosen column is empty after whitespace is removed.
- No date field: keep all non-timeline analysis available.
- No subgroup fields: keep all non-representation analysis available.
- File above the row cap: state exactly how many rows are analyzed and that the remainder is omitted.
- Non-English text: show the detected share and do not silently apply English-only affect models.
