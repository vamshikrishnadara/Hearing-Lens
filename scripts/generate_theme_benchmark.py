"""Add a richer fictional benchmark; preserve the original short-comment stress file.

Templates were authored as fictional development material, not resident evidence.
No classifier predictions or ground-truth labels are used to select output rows.
"""
import argparse
from pathlib import Path
import random
import re
from scripts.generate_synthetic_sample import generate_rows, write_csv

COMMENTS = {
'classroom_resources': [
 'Our classroom has thirty five children sharing twenty textbooks, so several pupils cannot take a reading book home to practice their lessons.',
 'Teachers are buying pencils and exercise books with their own money because the classroom supply budget runs out before the winter term.',
 'Please protect teaching positions and reduce oversized classes so that each child receives individual help with reading and mathematics during the school day.',
 'Science lessons cannot include experiments when the classroom has no working equipment, and replacing broken laboratory supplies should be a budget priority.',
 'The school library needs current books at several reading levels because the same worn classroom texts do not meet every student learning need.',
 'Will the district publish a classroom staffing plan showing how many teachers and teaching assistants will be available for each grade next year?',
 'Students who need extra practice are losing after school tutoring hours while their teachers are already responsible for more children than they can support.',
 'I support spending more of the education budget on textbooks and teaching staff rather than asking families to pay for essential classroom supplies.',
],
'school_safety': [
 'Cars speed through the school crossing at dismissal, and trained crossing guards are needed to help children reach the pavement safely every afternoon.',
 'The entrance gate is routinely left open during lessons, so visitors can walk onto school grounds without checking in with the security team.',
 'Broken lights near the school playground make the walking route unsafe after evening activities, and the district should repair them before winter.',
 'Families need a clear emergency evacuation procedure explaining where children will assemble and how school staff will contact parents after an incident.',
 'Please provide safety training for staff who supervise arrival and dismissal, including how to respond when a child is separated from their caregiver.',
 'There have been repeated fights outside the school entrance, and supervised dismissal with trained adults could reduce the risk of injuries to students.',
 'Will the school publish the results of its building safety inspection and explain when broken locks and unsafe playground equipment will be repaired?',
 'I support a safer visitor check in process, but security measures should not make children feel threatened when they enter their school each morning.',
],
'mental_health': [
 'Children experiencing anxiety wait several weeks to see a school counselor because one mental health professional is assigned to too many campuses.',
 'Our school needs a full time social worker who can support students dealing with grief and help families find appropriate mental health care.',
 'Please preserve confidential counseling appointments so that young people can discuss depression with a qualified clinician without feeling judged by their classmates.',
 'Teachers need training to recognize signs of emotional distress and refer students to mental health specialists instead of treating every crisis as misconduct.',
 'Students recovering from traumatic events need consistent therapeutic support throughout the school year, rather than a single visit from a temporary counselor.',
 'How many licensed psychologists will the district hire to reduce the waiting list for student mental health assessments and ongoing individual therapy?',
 'The budget should fund mental health counseling during school holidays because anxiety and emotional crises do not stop when the classroom closes.',
 'I welcome the proposed counseling service, but students need a private room and a reliable appointment system before they will feel comfortable seeking help.',
],
'transportation': [
 'Our school bus arrives late several mornings each week, leaving children at the stop and causing them to miss breakfast and their first lesson.',
 'Families need accurate bus arrival notifications because the transport office often announces a cancelled route only after children have already left home.',
 'The journey to school now takes more than an hour because the bus route crosses several neighborhoods before reaching its final destination.',
 'Please provide an accessible school bus with working wheelchair restraints so children with mobility needs can travel safely with the other students.',
 'Bus driver shortages have forced families to arrange expensive alternative transport, and the district should explain how it will recruit and retain drivers.',
 'Will the transportation department publish missed pickup records and on time arrival figures for every school bus route so families can track reliability?',
 'After school clubs are inaccessible to children whose only bus leaves immediately after lessons, so an additional late route would improve participation.',
 'I support reviewing school bus routes, but parents need advance notice and safe replacement stops before any existing transportation service is removed.',
],
'accessibility': [
 'The hearing room entrance has steps and no usable ramp, preventing wheelchair users from entering independently to give their public comments.',
 'Please provide live captions and sign language interpretation during public meetings so deaf residents can follow the discussion and participate on equal terms.',
 'The online comment form cannot be completed with a keyboard, which excludes residents who use assistive technology instead of a computer mouse.',
 'People using screen readers need accessible documents with clear headings and meaningful link labels instead of scanned images of the hearing materials.',
 'Residents who speak languages other than English need qualified interpreters and translated hearing documents before they can respond to the proposed changes.',
 'Will the district publish an accessibility contact and a simple way to request disability accommodations before each public hearing takes place?',
 'The meeting recording needs accurate captions because automatic transcription repeatedly omits important details and makes it difficult for deaf families to review decisions.',
 'I appreciate the new accessible entrance, but the hearing room also needs space for wheelchairs and a working sound system for people with hearing loss.',
],
'communication': [
 'Families received the hearing notice only one day before the meeting, leaving too little time to read the proposal and prepare meaningful questions.',
 'Please publish meeting dates and decision deadlines in a single public calendar so residents do not have to search several different district websites.',
 'Questions submitted at the previous hearing have received no written response, and the district should identify who is responsible for answering them.',
 'The public summary says residents supported the proposal but does not explain which concerns were raised or how those comments changed the final decision.',
 'Regular progress updates should explain what has changed since the last meeting and provide direct links to the supporting reports and budget documents.',
 'Will the district publish a response log showing each recurring public question, the department handling it, and the date an answer is expected?',
 'People who cannot attend an evening hearing need a recording and written minutes so they can understand the discussion and submit informed follow up comments.',
 'I welcome the new public newsletter, but it should clearly distinguish confirmed decisions from proposals that are still open for community discussion.',
]}


def generate_benchmark(count=1000, seed=20261001):
    rows = generate_rows(count, seed)
    rng = random.Random(seed)
    for row in rows:
        old = row['comment_text']
        suffix = re.search(r' (?:Contact |I live at ).*$', old)
        text = rng.choice(COMMENTS[row['validation_theme']])
        if old.startswith('After attending'):
            text = 'After attending multiple hearings, I am increasingly concerned. ' + text
        row['comment_text'] = text + (suffix.group() if suffix else '')
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/samples/synthetic_theme_benchmark.csv'))
    args=parser.parse_args()
    write_csv(args.output, generate_benchmark())
    print(f'Wrote 1,000 fictional benchmark comments to {args.output}')

if __name__=='__main__': main()
