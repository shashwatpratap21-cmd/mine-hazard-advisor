# Mine Hazard Advisor

Type the job you are about to do in a mine (a full sentence or just a word like "truck", "wire", "blasting", "chhat") and the site shows:

- **Most likely hazard**: one of 8 DGMS cause groups, from a TF-IDF + Logistic Regression classifier
- **Most important preventive measures**: grouped from the DGMS "the accident could have been averted had…" findings of the closest past accidents
- **Closest past accidents**: brief summaries of the 6 most similar DGMS fatal accidents, with the full record on click

Everything runs in the browser. There is no server and no data leaves the page.

## Data
DGMS SANKET reports on fatal accidents in coal and non-coal mines, 2016–2022: 621 narratives for the classifier and 610 records in the search index.

## Model
- Classifier: `TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True, stop_words="english")` + `LogisticRegression(class_weight="balanced", C=0.5)`
- Time-split test (train 2016–2020, test 2021–2022): 70.5% accuracy, macro-F1 0.62, against a 23% majority baseline
- Retrieval: TF-IDF cosine similarity with a +0.1 boost for the predicted hazard group, plus Place and Mine type filters
- A plain-word and Hindi dictionary expands short inputs into DGMS vocabulary

## Files
- `index.html`: the complete site (model weights and knowledge base embedded)
- `template.html`: page source before the model JSON is embedded
- `build_model.py`: trains the model from `accidents.csv` and exports `model.json`

To rebuild: run `python build_model.py` next to `accidents.csv`, then replace `__DATA__` in `template.html` with the contents of `model.json` (escape `</` as `<\/`) and wrap the result with the head/body tags used in `index.html`.

## Disclaimer
Decision support only. This does not replace the mine's Safety Management Plan, SOPs, statutory permissions or the judgement of a competent person.
