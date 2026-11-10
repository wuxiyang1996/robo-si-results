"""Scorer and plan consistency checks, explicitly not physics validation."""
import copy
import unittest
from .contracts import TASKS,contract,config,plan
from .runtime import ToolEvaluator
from tests.test_tabletop_hanoi import initial_states


class ContractTests(unittest.TestCase):
    def test_ten_scoped_tasks_and_reasoning_lengths(self):
        self.assertEqual(len(TASKS),10)
        for t in TASKS:
            c=contract(t);p=plan(t)
            moves=[x for x in p['high_level'] if x['id'].startswith('M')]
            self.assertEqual(len(moves),2**c['disks']-1)
            ids={x['id'] for x in p['high_level']}
            self.assertTrue(all(x['high'] in ids for x in p['low_level']))
            self.assertEqual(len({x['id'] for x in p['low_level']}),len(p['low_level']))

    def test_disclosure_pairs_share_physical_configuration(self):
        for a,b in [('Hanoi-01','Hanoi-03'),('Hanoi-02','Hanoi-04'),('Hanoi-09','Hanoi-10')]:
            self.assertEqual(config(a),config(b))
            self.assertEqual(contract(a)['embodiment'],contract(b)['embodiment'])
            self.assertNotEqual(contract(a)['disclosure'],contract(b)['disclosure'])

    def test_tool_chain_lifts_but_tool_contact_prevents_release(self):
        cfg=config('Hanoi-01');e=ToolEvaluator(cfg);states=initial_states(cfg)
        e.update(states,.02);name='disk_2';s=states[name]
        s.update(pos=(cfg.peg_x,cfg.peg_ys[0],cfg.rod_top+.025),support_forces={},
                 tool_chain_contact=True,any_tool_contact=True)
        self.assertFalse(e.update(states,.02)['failed'])
        s.update(pos=cfg.slot_position('C',0),support_forces={'pad_C':1.2},tool_chain_contact=False)
        for _ in range(40):e.update(states,.02)
        self.assertEqual(e.move_count,0)
        s['any_tool_contact']=False
        for _ in range(26):e.update(states,.02)
        self.assertEqual(e.move_count,1)

    def test_unheld_tool_is_not_manipulation_evidence(self):
        cfg=config('Hanoi-01');e=ToolEvaluator(cfg);states=initial_states(cfg);e.update(states,.02)
        states['disk_2'].update(pos=(cfg.peg_x,cfg.peg_ys[0],cfg.rod_top+.025),support_forces={},
                                tool_chain_contact=False,any_tool_contact=True)
        e.update(states,.02)
        self.assertFalse(e._hand_seen)
        states['disk_2'].update(pos=cfg.slot_position('C',0),support_forces={'pad_C':1.2},any_tool_contact=False)
        for _ in range(26):e.update(states,.02)
        self.assertTrue(e.failed)
        self.assertEqual(e.reason,'no_hand_contact')

    def test_adapter_does_not_relabel_raw_hand_contact(self):
        cfg=config('Hanoi-01');e=ToolEvaluator(cfg);states=initial_states(cfg)
        states['disk_2']['tool_chain_contact']=True;original=copy.deepcopy(states)
        e._read_states(states);self.assertEqual(states,original)


if __name__=='__main__':unittest.main()
