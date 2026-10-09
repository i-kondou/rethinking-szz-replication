"""Consecutive-label compression and logged interval grouping."""
import itertools

def compress(tokens):
    return [token for token, _ in itertools.groupby(tokens)]

def order_groups(calls):
    """Group overlapping use/result intervals; do not impose a runtime order."""
    groups = []
    for call in calls:
        start, end = call['use_event_index'], call['result_event_index']
        assert isinstance(start, int) and isinstance(end, int) and start < end
        if groups and start <= max(c['result_event_index'] for c in groups[-1]):
            groups[-1].append(call)
        else:
            groups.append([call])
    return groups
