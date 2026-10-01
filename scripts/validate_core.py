"""Run local development corpora and save local review output plus aggregate checks.

Only explicitly supplied development samples are written; the pipeline itself
never writes uploads. Public narratives/review reports must stay outside Git.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from time import perf_counter

import pandas as pd
import torch
from sklearn.metrics import adjusted_rand_score
from pipeline.core import analyze_core
from pipeline.redact import build_safe_display_frame
from pipeline.timeline import timeline_figures
from scripts.validate_cfpb_themes import load_sample


def load_federal(directory):
    directory=Path(directory)
    path=directory/'federal_sample.csv'
    manifest=json.loads((directory/'federal_manifest.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['sample_sha256']:
        raise ValueError('Federal sample checksum mismatch.')
    frame=pd.read_csv(path,keep_default_na=False,dtype=str)
    if len(frame)!=manifest['sample_rows'] or frame.source_id.tolist()!=manifest['source_ids'] or frame.source_id.duplicated().any() or frame.comment_text.str.strip().eq('').any():
        raise ValueError('Federal sample does not match its manifest.')
    return frame,manifest


def comment_fingerprint(frame):
    payload=json.dumps(frame.comment_text.fillna('').astype(str).tolist(),ensure_ascii=False,separators=(',',':'))
    return hashlib.sha256(payload.encode()).hexdigest()


def run_corpus(frame, name, destination):
    start=perf_counter(); result=analyze_core(frame); cold=perf_counter()-start
    start=perf_counter(); repeated=analyze_core(frame); warm=perf_counter()-start
    themes=result['themes']; assignments=themes['assignments']
    by_position={a['row_position']:a['theme_id'] for a in assignments}
    safe=build_safe_display_frame(frame[['comment_text']]).frame.comment_text.tolist()
    quotes=[(theme['theme_id'],q) for theme in themes['themes'] for q in theme['quotes']]
    review=[]
    for theme in themes['themes'][:3]:
        positions=[i for i,t in by_position.items() if t==theme['theme_id']][:5]
        review.append({'theme_id':theme['theme_id'],'label':theme['label'],
                       'members':[{'row_position':i,'text':safe[i]} for i in positions]})
    # This packet is for human review; generating it is not review approval.
    (destination/f'{name}-review.json').write_text(json.dumps({'comment_sha256':comment_fingerprint(frame),'result':result,'theme_review_packet':review},indent=2))
    figures=timeline_figures(result['timeline'])
    for kind,figure in figures.items():
        figure.write_html(destination/f'{name}-{kind}.html',include_plotlyjs=True)
    summary={
        'input_rows':len(frame),'analyzed_comments':themes['analyzed_comments'],
        'first_run_seconds':cold,'warm_run_seconds':warm,
        'repeated_results_identical':result==repeated,
        'backend':themes['backend'],'themes':len(themes['themes']),
        'group_sizes':[t['count'] for t in themes['themes']],
        'quote_counts':[len(t['quotes']) for t in themes['themes']],
        'outlier_share':themes['outlier_share'],
        'scored_comments':result['affect']['scored_count'],
        'excluded_language_count':result['affect']['excluded_language_count'],
        'truncated_count':result['affect']['truncated_count'],
        'periods':len(result['timeline']['periods']),
        'checks':{
            'unique_assignments':len(by_position)==len(assignments)==themes['analyzed_comments'],
            'membership_totals':sum(t['count'] for t in themes['themes'])+themes['outlier_count']==themes['analyzed_comments'],
            'valid_quotes':all(by_position[q['row_position']]==tid and q['text']==safe[q['row_position']] and 12<=len(q['text'].split())<=60 for tid,q in quotes),
            'five_to_fifteen_themes':5<=len(themes['themes'])<=15,
            'outliers_under_twenty_percent':themes['outlier_share']<.2,
            'three_quotes_each':bool(themes['themes']) and all(len(t['quotes'])==3 for t in themes['themes']),
            'first_run_under_two_minutes':cold<120,'warm_run_under_thirty_seconds':warm<30},
        'human_theme_review':'pending','human_affect_agreement':'pending',
    }
    if 'validation_theme' in frame:
        summary['development_ari']=float(adjusted_rand_score(
            [frame.iloc[a['row_position']].validation_theme for a in assignments],[a['theme_id'] for a in assignments]))
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfpb-dir',type=Path,required=True)
    parser.add_argument('--federal-dir',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(2)
    root=Path(__file__).resolve().parents[1]
    public,manifest=load_sample(args.cfpb_dir)
    public=public.rename(columns={'date_received':'hearing_date'})
    corpora={'synthetic':pd.read_csv(root/'data/samples/synthetic_chicago_hearing.csv'),'cfpb':public}
    sources={'cfpb_sha256':manifest['sample_sha256']}
    if args.federal_dir:
        federal,manifest=load_federal(args.federal_dir);corpora['federal']=federal
        sources['federal_sha256']=manifest['sample_sha256']
    summary={'notice':'Development checks; human agreement and theme review remain pending. First-run timings include model/JIT loading only for the first corpus in this process; imports and setup downloads are excluded.',
             'versions':{p:importlib.metadata.version(p) for p in ['bertopic','keybert','langid','transformers','torch','scikit-learn']},
             'sources':sources,'corpora':{},'federal_status':'provided' if args.federal_dir else 'pending sample'}
    for name,frame in corpora.items():
        summary['corpora'][name]=run_corpus(frame,name,args.output_dir)
        (args.output_dir/'core-validation.json').write_text(json.dumps(summary,indent=2))
        print(name,json.dumps(summary['corpora'][name]),flush=True)


if __name__=='__main__':main()
