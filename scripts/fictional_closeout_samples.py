"""Authored fictional feedback corpora; no collected submissions or downloads."""
import pandas as pd

# Each topic has five authored concerns. Combinations intentionally repeat wording;
# these are software-development fixtures, not independent real-world evidence.
TOPICS = {
    'community_center': {
        'classes': ('Community center classes and workshops', [
            'The painting class runs during school pickup, so families cannot attend the whole workshop.',
            'I enjoyed the beginner music lessons and would like an evening group for people who work during the day.',
            'The cooking workshop was cancelled without arranging a replacement teacher or a refund for materials.',
            'Will the center publish a complete class timetable before registration opens for the next term?',
            'The exercise instructor explains each movement clearly and gives beginners time to practice safely.']),
        'building': ('Community center building maintenance', [
            'The ceiling leaks whenever it rains and the wet floor outside the craft room is dangerously slippery.',
            'The newly repaired heating system keeps the activity rooms comfortable during evening sessions.',
            'Several bathroom taps are broken and the cleaning checklist has not been updated for weeks.',
            'When will the center repair the leaking roof and replace the broken bathroom fixtures?',
            'The lights in the main hall flicker and the staff keep moving classes into smaller rooms.']),
        'volunteers': ('Community center volunteer support', [
            'New volunteers are asked to lead activities without an orientation or a clear contact for urgent questions.',
            'The volunteer coordinator listened carefully and arranged a helpful training session for our team.',
            'The volunteer rota changes at the last minute and nobody confirms who will cover the front desk.',
            'Who will provide training and written role descriptions before the next group of volunteers starts?',
            'I was grateful that another volunteer helped me prepare the materials and stayed to clean the room.']),
        'access': ('Community center disability access', [
            'The entrance door is too heavy to open from a wheelchair and the accessible side entrance is locked.',
            'The new captions made the online community workshop easier for me to follow without missing details.',
            'The booking form has buttons without labels and cannot be completed using only a keyboard.',
            'How can visitors request captions, step-free access or a quiet space before attending an activity?',
            'The signs point toward stairs but do not explain where visitors can find the working lift.']),
        'fees': ('Community center membership and activity fees', [
            'The membership renewal notice included an extra charge that was not listed when I first registered.',
            'The reduced activity fee meant my family could join the holiday workshop without borrowing money.',
            'I cancelled within the stated deadline but have waited several weeks for the promised refund.',
            'Will the center explain the refund rules and publish all activity charges before accepting bookings?',
            'The fee waiver application asks for several documents but does not explain how decisions are made.']),
        'notices': ('Community center notices and communication', [
            'The activity reminder arrived after the session ended and the website still displayed the old time.',
            'The weekly newsletter clearly explains upcoming activities and gives a useful contact for each one.',
            'My messages about a cancelled session received automated replies but no explanation from the staff.',
            'Where will the center publish schedule changes so that members can check them before travelling?',
            'The printed notice and the online calendar give different opening hours for the same weekend.']),
    },
    'tenant_association': {
        'repairs': ('Tenant association discussion of home repairs', [
            'The kitchen tap has leaked for weeks and repeated repair requests have not produced an appointment.',
            'The repair team arrived at the agreed time and explained how they had fixed the damaged window.',
            'The bedroom heater stopped working again and I am worried about another cold night indoors.',
            'When will residents receive a repair schedule for the leaking pipes and broken heating systems?',
            'A maintenance visit was marked complete even though nobody entered the flat or repaired the fault.']),
        'noise': ('Tenant association discussion of building noise', [
            'Loud construction begins before the announced time and makes it difficult to sleep after night shifts.',
            'The new quiet-hours notice helped neighbours discuss noise without blaming each other personally.',
            'The lift machinery rattles through the night and the sound carries into nearby bedrooms.',
            'Who should residents contact about repeated overnight noise and how will complaints be followed up?',
            'I would like noisy building work scheduled with advance notice so families can plan around it.']),
        'entry': ('Tenant association discussion of entrance security', [
            'The shared entrance lock does not catch properly and the building door stays open after visitors leave.',
            'The repaired intercom makes it much easier to check who is at the entrance before opening the door.',
            'Packages have disappeared from the lobby and residents are anxious about leaving deliveries unattended.',
            'Will residents receive an update about repairs to the entrance lock and the faulty intercom?',
            'The rear entrance light is broken and I cannot clearly see the steps when returning home at night.']),
        'shared_spaces': ('Tenant association discussion of shared spaces', [
            'The shared laundry room is often left dirty and two washing machines have been unusable for weeks.',
            'The garden clean-up brought neighbours together and made the shared seating area pleasant again.',
            'Overflowing bins block the walkway and attract pests near the shared storage rooms.',
            'When will the broken laundry machines be repaired and the communal cleaning schedule be published?',
            'The bicycle storage area is crowded and residents need a fair way to label and arrange their bikes.']),
        'meetings': ('Tenant association discussion of meeting access', [
            'The association meeting takes place upstairs without a lift, preventing some neighbours from attending.',
            'The remote meeting option allowed me to contribute while caring for a family member at home.',
            'The meeting papers were sent as unreadable photographs rather than accessible text documents.',
            'How can residents request an accessible meeting location or interpretation before the next discussion?',
            'Only one meeting time is offered and residents who work evening shifts cannot join the discussion.']),
        'accounts': ('Tenant association discussion of shared service charges', [
            'The service-charge statement lists a large adjustment without explaining what work the payment covers.',
            'The itemised account helped me understand the cleaning costs and compare them with the previous year.',
            'I reported a duplicated charge but the next statement still included the same amount twice.',
            'Will residents receive an itemised explanation of shared charges before the payment deadline?',
            'The payment notice and the account statement show different totals and I cannot tell which is correct.']),
    },
}

CONTEXT = [
    'I am pleased that people can raise this issue and I hope the practical details will be taken seriously.',
    'I feel frustrated after describing the same problem several times without receiving a clear explanation.',
    'The situation worries me because I cannot tell whether the promised arrangements will actually be available.',
    'I appreciate the effort made so far and the improvement has made a noticeable difference to my routine.',
    'I am disappointed that the problem continues even though several people have offered reasonable suggestions.',
    'Please record this feedback and explain the next steps in language that everyone can understand.',
    'The change surprised me because it was very different from the information given at the previous discussion.',
    'I am angry about the repeated failures and want those responsible to acknowledge the effect on people.',
    'The experience left me feeling sad because something that used to bring neighbours together is now difficult.',
    'I have described the situation as I experienced it and would welcome a clear account of the available options.',
]


def make_sample(name):
    rows = []
    for topic, (context, statements) in TOPICS[name].items():
        for index, statement in enumerate(statements):
            for variant, closing in enumerate(CONTEXT):
                # Longer examples remain about the same topic. Do not invent human labels.
                extra = ' '.join(statements[(index + n + 1) % len(statements)]
                                 for n in range(variant % 4))
                rows.append({'comment_text': f'{context}. {statement} {extra} {closing}'.strip(),
                             'respondent_id': f'{name}-{len(rows)+1:04d}',
                             'hearing_date': ['2026-08-03', '2026-08-10', '2026-08-17'][variant % 3],
                             'role': ['Member', 'Volunteer', 'Visitor'][variant % 3],
                             'validation_theme': topic})
    return pd.DataFrame(rows)
