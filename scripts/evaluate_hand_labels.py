"""Compare explicit human labels with saved model outputs; never invent labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import pandas as pd
from pipeline.affect import SENTIMENTS, EMOTIONS
from pipeline.redact import build_safe_display_frame
from scripts.validate_cfpb_themes import load_sample
from scripts.validate_core import load_federal, comment_fingerprint


def evaluate(sheet, predictions, reference_texts):
    if sheet.review_id.duplicated().any():raise ValueError('Review IDs must be unique.')
    records=[]; seen=set()
    for row in sheet.fillna('').to_dict('records'):
        supplied=bool(str(row['human_sentiment']).strip() or str(row['human_emotion']).strip())
        if not supplied:continue
        corpus=row['corpus']
        if row['status']!='ready_for_human' or corpus not in reference_texts:raise ValueError('Labels require a prepared corpus row.')
        if row['human_sentiment'] not in SENTIMENTS or row['human_emotion'] not in EMOTIONS or not str(row['reviewer']).strip():
            raise ValueError('Every labeled row needs valid sentiment, emotion, and a human reviewer.')
        position=int(row['row_position']); key=(corpus,position)
        if key in seen:raise ValueError('A corpus row cannot be counted twice.')
        seen.add(key)
        if not 0<=position<len(reference_texts[corpus]):raise ValueError('Invalid source row.')
        text=reference_texts[corpus][position]
        if hashlib.sha256(text.encode()).hexdigest()!=row['text_sha256'] or row['comment_text']!=text:
            raise ValueError('Review text differs from the prepared redacted source.')
        prediction=next((r for r in predictions.get(corpus,[]) if r['row_position']==position),None)
        records.append((row,prediction))
    summary={'human_labeled_rows':len(records),'required_rows':60,'corpora':{},
             'complete':False,'notice':'Agreement uses only rows with both human labels and model scores; exclusions and coverage are reported separately. Human labels must be entered by a person.'}
    for corpus in ['synthetic','cfpb','federal']:
        labeled=[pair for pair in records if pair[0]['corpus']==corpus]
        scored=[pair for pair in labeled if pair[1] and pair[1]['status']=='scored']
        item={'human_labeled':len(labeled),'model_scored':len(scored),'excluded_or_missing_predictions':len(labeled)-len(scored)}
        for kind,labels in [('sentiment',SENTIMENTS),('emotion',EMOTIONS)]:
            pairs=Counter((row['human_'+kind],pred[kind]) for row,pred in scored)
            agreement=sum(pairs[label,label] for label in labels)/len(scored) if scored else None
            item[kind]={'agreement':agreement,'confusion':{truth:{pred:pairs[truth,pred] for pred in labels} for truth in labels},
                        'remediation_required':agreement is not None and agreement<.7}
        summary['corpora'][corpus]=item
    summary['complete']=all(item['human_labeled']==20 and item['model_scored']==20 for item in summary['corpora'].values())
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labels',type=Path,required=True)
    parser.add_argument('--predictions-dir',type=Path,required=True)
    parser.add_argument('--cfpb-dir',type=Path,required=True)
    parser.add_argument('--federal-dir',type=Path)
    parser.add_argument('--synthetic',type=Path,default=Path('data/samples/synthetic_chicago_hearing.csv'))
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    frames={'synthetic':pd.read_csv(args.synthetic),'cfpb':load_sample(args.cfpb_dir)[0]}
    if args.federal_dir:frames['federal']=load_federal(args.federal_dir)[0]
    safe={name:build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist() for name,frame in frames.items()}
    predictions={}
    for name,frame in frames.items():
        packet=json.loads((args.predictions_dir/f'{name}-review.json').read_text())
        if packet.get('comment_sha256')!=comment_fingerprint(frame):
            raise ValueError('Prediction source differs from the review corpus; rerun validation.')
        predictions[name]=packet['result']['affect']['rows']
    print(json.dumps(evaluate(pd.read_csv(args.labels,keep_default_na=False),predictions,safe),indent=2))


if __name__=='__main__':main()
