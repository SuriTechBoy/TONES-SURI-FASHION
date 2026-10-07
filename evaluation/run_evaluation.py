from __future__ import annotations
import sys, json
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
from pathlib import Path
from scripts.tones_engine import retrieve
from scripts.answer_generator import generate
TESTS=Path(__file__).with_name('test_questions.json'); OUT=Path(__file__).with_name('evaluation_report.json')

def main():
 tests=json.loads(TESTS.read_text(encoding='utf-8')); rows=[]
 for t in tests:
  r=retrieve(t['question']); g=generate(r); expected=t['expected_intent']; actual=r['intent']
  intent_ok=actual==expected
  if t['category']=='out_of_scope': behavior=r['route']=='OUT_OF_SCOPE'
  elif t['category']=='reviews': behavior=len(r.get('reviews',[]))>0 or "couldn't match that product" in g.get('answer','')
  elif t['category']=='product_attribute': behavior=r.get('needs_clarification',False) or bool(r.get('product'))
  elif t['category']=='product_search':
   answer_text=g.get('answer','').lower()
   behavior=bool(r.get('products')) or actual in {'CHEAPEST_PRODUCT','MOST_EXPENSIVE_PRODUCT','PRODUCT_OFFERS'} or 'couldn' in answer_text or 'no verified' in answer_text
  elif expected in {'SHIPPING','RETURN_EXCHANGE','ORDER_TRACKING','PAYMENTS','CONTACT','BRAND_BUSINESS'}: behavior=bool(r.get('business'))
  else: behavior=bool(g.get('answer'))
  rows.append({**t,'actual_intent':actual,'route':r['route'],'response_type':g.get('response_type'),'intent_pass':intent_ok,'behavior_pass':behavior,'pass':intent_ok and behavior,'products':len(r.get('products',[])),'reviews':len(r.get('reviews',[]))})
 total=len(rows); passed=sum(x['pass'] for x in rows)
 report={'total':total,'passed':passed,'failed':total-passed,'accuracy':round(passed/total,4),'results':rows}
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['total','passed','failed','accuracy']},indent=2))
 for x in rows:
  if not x['pass']: print('FAIL',x['id'],x['question'],'expected=',x['expected_intent'],'actual=',x['actual_intent'],'behavior=',x['behavior_pass'])
if __name__=='__main__': main()
