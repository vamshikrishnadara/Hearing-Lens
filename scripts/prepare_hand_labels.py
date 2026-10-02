"""Create a blind, redacted human-label sheet for 20 comments per corpus.

Missing corpora get explicit pending rows, never invented comments or labels.
Write outside Git. Prediction outputs are deliberately absent from the sheet.
"""
import argparse
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from pipeline.redact import build_safe_display_frame
from scripts.validate_cfpb_themes import load_sample
from scripts.validate_core import load_federal


def make_sheet(corpora):
    rows=[]
    for name in ['synthetic','cfpb','federal']:
        frame=corpora.get(name)
        if frame is None:
            rows.extend({'review_id':f'{name}-{i+1:02d}','corpus':name,'status':'pending_corpus',
                         'row_position':'','text_sha256':'','comment_text':'',
                         'human_sentiment':'','human_emotion':'','reviewer':'','notes':''} for i in range(20))
            continue
        eligible=np.flatnonzero(frame.comment_text.fillna('').astype(str).str.strip().ne('').to_numpy())
        if len(eligible)<20:raise ValueError('Each corpus needs at least 20 nonempty comments.')
        selected=np.random.default_rng(20261001).choice(eligible,size=20,replace=False)
        safe=build_safe_display_frame(frame[['comment_text']].iloc[selected].reset_index(drop=True)).frame.comment_text.tolist()
        for i,(position,text) in enumerate(zip(selected,safe)):
            rows.append({'review_id':f'{name}-{i+1:02d}','corpus':name,'status':'ready_for_human',
                'row_position':int(position),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
                'comment_text':text,'human_sentiment':'','human_emotion':'','reviewer':'','notes':''})
    return pd.DataFrame(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfpb-dir',type=Path,required=True)
    parser.add_argument('--federal-dir',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--synthetic',type=Path,default=Path('data/samples/synthetic_chicago_hearing.csv'))
    args=parser.parse_args()
    if args.output.exists():parser.error('Output exists; choose another path to preserve human work.')
    root=Path(__file__).resolve().parents[1]
    corpora={'synthetic':pd.read_csv(args.synthetic),
             'cfpb':load_sample(args.cfpb_dir)[0]}
    if args.federal_dir:corpora['federal']=load_federal(args.federal_dir)[0]
    sheet=make_sheet(corpora);args.output.parent.mkdir(parents=True,exist_ok=True);sheet.to_csv(args.output,index=False)
    print(sheet.status.value_counts().to_dict())


if __name__=='__main__':main()
