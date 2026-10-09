#!/usr/bin/env python3
"""Reclassify recorded Bash requests using the study's deterministic ABC rules."""
import json
from pathlib import Path
from common import data, require, equivalent
import abc_rules_only_v5 as rules


class Context(rules.Context):
    def __init__(self, record):
        self.queries = record['queries']
        super().__init__(Path(record['repository_path']), record['bfc'], record['source_bfc'])

    def git(self, *args):
        # These are frozen answers to read-only Git probes, not category labels.
        # No command taken from a transcript is executed.
        key = json.dumps(args)
        require(key in self.queries, 'Missing frozen Git query: ' + key)
        return self.queries[key]


def classify():
    contexts = {sid: Context(r) for sid,r in data('classifier-context').items()}
    expected = {r['slot_id']:r for r in data('machine')['runs']}
    runs = []
    for raw in data('evidence')['runs']:
        engine = rules.Engine(contexts[raw['sample_id']])
        calls = []
        for call in raw['calls']:
            item = engine.classify(call['command'], call['output'], call['use_event_index'],
                                   call['result_event_index'], call['tool_error'])
            key = f"{raw['slot_id']}#{call['index']}"
            item.update(key=key, call_index=call['index'], command=call['command'],
                        use_event_index=call['use_event_index'], result_event_index=call['result_event_index'],
                        tool_use_id=call['tool_use_id'])
            for i,op in enumerate(item['operations'],1):
                op['id'] = f'{key}/rule{i}'
            calls.append(item)
        equivalent(calls, expected[raw['slot_id']]['calls'], 'classifier/'+raw['slot_id'])
        runs.append(dict(slot_id=raw['slot_id'],calls=calls))
    require(len(runs)==237 and sum(len(r['calls']) for r in runs)==1612,'Incomplete classifier input')
    return runs


if __name__=='__main__':
    runs=classify()
    print(f"Verified {len(runs)} runs / 1612 Bash calls; no model or shell calls.")
