"""Preserve unknown and overlapping operation order."""
import json
import sequences as seq

def lane_view(call):
    activities = [o['activity'] for o in call['operations'] if o['activity'] != 'OTHER']
    unknown = any(a not in 'ABC' or len(a) != 1 for a in activities)
    held = bool(call['structure_hold'] and len(set(activities)) > 1)
    tokens = seq.compress(activities)
    if unknown:
        label = 'Unknown activity {' + ','.join(sorted(set(activities))) + '}'
    elif held:
        label = 'Unresolved order {' + ','.join(sorted(set(activities))) + '}'
    else:
        label = '→'.join(tokens)
    return {'call_key': call['key'], 'tokens': tokens, 'activities': sorted(set(activities)),
            'activity_unknown': unknown, 'internal_order_hold': held,
            'complete': not unknown and not held, 'label': label,
            'interval': [call['use_event_index'], call['result_event_index']]}

def intersects(a, b):
    return max(a[0], b[0]) <= min(a[1], b[1])

def make_blocks(calls):
    """Retain connected interval groups and lane orders, not invented serial orders."""
    assert len({c['key'] for c in calls}) == len(calls)
    assert all(isinstance(c['use_event_index'], int) and isinstance(c['result_event_index'], int)
               and c['use_event_index'] <= c['result_event_index'] for c in calls)
    assert all(a['use_event_index'] < b['use_event_index'] for a, b in zip(calls, calls[1:]))
    groups, nodes = [], []

    def append(node):
        if nodes and node['kind'] == nodes[-1]['kind'] == 'activity' and node['label'] == nodes[-1]['label']:
            nodes[-1]['group_ids'] = list(dict.fromkeys(nodes[-1]['group_ids'] + node['group_ids']))
        else:
            nodes.append(node)

    for index, members in enumerate(seq.order_groups(calls), 1):
        lanes = [lane_view(c) for c in members]
        active = [lane for lane in lanes if lane['tokens']]
        pairs, precedes = [], []
        for i, a in enumerate(lanes):
            for b in lanes[i+1:]:
                if intersects(a['interval'], b['interval']):
                    pairs.append([a['call_key'], b['call_key']])
                elif a['interval'][1] < b['interval'][0]:
                    precedes.append([a['call_key'], b['call_key']])
        acts = set(a for lane in active for a in lane['activities'])
        complete = all(lane['complete'] for lane in active)
        mixed_overlap = len(active) > 1 and len(acts) > 1
        group = {'id': index, 'call_keys': [c['key'] for c in members], 'lanes': lanes,
                 'overlap_pairs': pairs, 'known_precedence': precedes,
                 'mixed_overlap': mixed_overlap, 'complete': complete,
                 'activity_unknown': any(lane['activity_unknown'] for lane in active),
                 'internal_order_hold': any(lane['internal_order_hold'] for lane in active)}
        groups.append(group)
        if mixed_overlap:
            label = '[' + ' ∥ '.join('(' + a['label'] + ')' if len(a['tokens']) > 1 else a['label'] for a in active) + ']'
            append({'kind': 'overlap', 'label': label, 'group_ids': [index],
                    'signature': ['overlap', sorted(a['label'] for a in active)], 'complete': complete})
        elif not complete:
            label = ' / '.join(a['label'] for a in active)
            append({'kind': 'unresolved', 'label': label, 'group_ids': [index],
                    'signature': ['unresolved', label], 'complete': False})
        else:
            for token in seq.compress([t for a in active for t in a['tokens']]):
                append({'kind': 'activity', 'label': token, 'group_ids': [index],
                        'signature': ['activity', token], 'complete': True})
    return {'groups': groups, 'nodes': nodes, 'complete': all(n['complete'] for n in nodes),
            'trace': ' → '.join(n['label'] for n in nodes),
            'signature': [n['signature'] for n in nodes],
            'serial_projection': ''.join(seq.compress([n['label'] if n['kind'] == 'activity' else '?' for n in nodes]))}

def compare(items):
    known = [json.dumps(sig, sort_keys=True) for complete, sig in items if complete]
    return 'different' if len(set(known)) > 1 else 'same' if len(known) == 3 else 'unknown'
