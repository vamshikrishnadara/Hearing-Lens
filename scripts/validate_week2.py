"""Reproduce the Week 2 benchmark; source text stays in explicitly local reports."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import adjusted_rand_score
from pipeline.themes import analyze_themes, _analysis_text
from pipeline.redact import build_safe_display_frame
from pipeline.quotes import valid_source_quote, nearly_identical
from scripts.validate_core import load_federal, comment_fingerprint
from scripts.validate_cfpb_themes import load_sample


def run(frame, name, output):
    start=perf_counter()
    result=analyze_themes(frame, theme_count='auto', backend='auto', keyword_method='keybert',
                          merge_small_themes=True, quote_pool_size=6, quote_mode='sentences')
    elapsed=perf_counter()-start
    safe=build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    by_row={a['row_position']:a['theme_id'] for a in result['assignments']}
    themes=result['themes']
    all_quotes=[(t['theme_id'],q) for t in themes for q in t['quotes']]
    quote_check=all(by_row[q['row_position']]==tid and valid_source_quote(q,safe[q['row_position']])
                    for tid,q in all_quotes)
    distinct=all(len({q['row_position'] for q in t['quotes']})==len(t['quotes']) and not any(
        nearly_identical(_analysis_text(a['text']),_analysis_text(b['text']))
        for i,a in enumerate(t['quotes']) for b in t['quotes'][i+1:]) for t in themes)
    review=[]
    for theme in themes[:3]:
        members=[i for i,t in by_row.items() if t==theme['theme_id']]
        # Fixed systematic sample, plus all displayed quotes. No selection by a review score.
        chosen=list(dict.fromkeys([q['row_position'] for q in theme['quotes']]+[
            members[i] for i in np.linspace(0,len(members)-1,min(9,len(members)),dtype=int)]))
        review.append({'theme_id':theme['theme_id'],'label':theme['label'],
                       'members':[{'row_position':i,'text':safe[i]} for i in chosen]})
    summary={'rows':len(frame),'analyzed_comments':result['analyzed_comments'],
             'backend':result['backend'],'seconds':elapsed,'theme_count':len(themes),
             'outlier_share':result['outlier_share'],'group_sizes':[t['count'] for t in themes],
             'quote_counts':[len(t['quotes']) for t in themes],
             'excerpt_count':sum(bool(q.get('is_excerpt')) for _,q in all_quotes),
             'comment_sha256':comment_fingerprint(frame),
             'checks':{'five_to_fifteen_themes':5<=len(themes)<=15,
                       'outliers_under_twenty_percent':result['outlier_share']<.2,
                       'runtime_under_two_minutes':elapsed<120,
                       'three_quotes_each':bool(themes) and all(len(t['quotes'])==3 for t in themes),
                       'valid_source_quotes':quote_check,'distinct_quotes':distinct,
                       'all_assignments_preserved':len(by_row)==len(result['assignments'])==result['analyzed_comments'],
                       'membership_totals':sum(t['count'] for t in themes)+result['outlier_count']==len(by_row)}}
    if 'validation_theme' in frame:
        summary['development_ari']=float(adjusted_rand_score(
            [frame.iloc[a['row_position']].validation_theme for a in result['assignments']],
            [a['theme_id'] for a in result['assignments']]))
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/f'{name}-review.json').write_text(json.dumps({'summary':summary,'result':result,'theme_review_packet':review},indent=2))
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfpb-dir',type=Path,default=Path('data/public_samples/cfpb_2017_300'))
    parser.add_argument('--federal-dir',type=Path,default=Path('data/public_samples/federal_mirror_300'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();torch.set_num_threads(2)
    root=Path(__file__).resolve().parents[1]
    corpora={'synthetic':pd.read_csv(root/'data/samples/synthetic_theme_benchmark.csv'),
             'cfpb':load_sample(args.cfpb_dir)[0], 'federal':load_federal(args.federal_dir)[0],
             'synthetic_legacy_stress':pd.read_csv(root/'data/samples/synthetic_chicago_hearing.csv')}
    summary={}
    for name,frame in corpora.items():
        summary[name]=run(frame,name,args.output_dir)
        print(name,json.dumps(summary[name]),flush=True)
        (args.output_dir/'week2-summary.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__':main()
