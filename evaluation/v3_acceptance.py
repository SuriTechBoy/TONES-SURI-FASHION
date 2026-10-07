from pathlib import Path
import json, sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.tones_engine import retrieve, product_matches
from scripts.answer_generator import generate

PRODUCT_CASES = [
    "Show me T-shirts",
    "Show me red T-shirts",
    "Show me T-shirts under ₹1000",
    "Show me green T-shirts under ₹900",
    "Show me black oversized T-shirts under ₹1200",
    "Show me shirts between ₹500 and ₹1500",
    "Show me blue shirts under ₹2000",
    "Show me T-shirts under ₹1000 in XL",
    "Show me black oversized T-shirts under ₹1200 in XL",
    "Show me products under ₹1000",
    "Show me T-shirts between ₹500 and ₹1000",
    "Show me red T-shirts under ₹999",
    "Show me T-shirts below ₹1000 with ratings above 4",
    "Show me green oversized T-shirts under ₹500",
    "Show me men's t-shirts",
    "Show me women's dresses",
    "Show me red men's t-shirts under ₹1000",
    "Show me XL t-shirts that are in stock",
]
BUSINESS_CASES = [
    ("Is TONES Fashion based in Hyderabad?", "BRAND_BUSINESS"),
    ("Who owns TONES Fashion?", "BRAND_BUSINESS"),
    ("What is the customer support email?", "CONTACT"),
    ("Do you deliver across India?", "SHIPPING"),
    ("What is the return policy?", "RETURN_EXCHANGE"),
    ("Can I pay using COD?", "PAYMENTS"),
]
SCOPE_CASES = ["Show me Nike products", "Show me smartphones", "Who won the cricket match?", "Tell me a joke"]

def main():
    rows=[]
    for q in PRODUCT_CASES:
        r=retrieve(q); g=generate(r); ok=True; reason=''
        if r['intent']!='PRODUCT_SEARCH': ok=False; reason=f"intent={r['intent']}"
        else:
            for p in r['products']:
                good,_=product_matches(p,r['filters'],q)
                if not good: ok=False; reason=f"invalid result={p['name']}"; break
            if not r['products'] and 'couldn' not in g['answer'].lower() and 'no verified' not in g['answer'].lower(): ok=False; reason='zero-result response not safe'
        rows.append((q,ok,reason))
    # Exact product + reviews.
    for q, expected_reviews, expected_detail in [
        ("Tell me everything about Tones Original Black", True, True),
        ("What did customers say about the quality of Tones Original Black?", True, False),
        ("Is Tones Original Black available in size M?", False, False),
        ("Is XXL available for Tones Original Black?", False, False),
    ]:
        r=retrieve(q); g=generate(r); ok=bool(r.get('product'))
        if expected_reviews: ok = ok and len(r.get('reviews',[]))>0
        if 'size M' in q: ok = ok and 'not currently recorded as in stock' in g['answer']
        if 'XXL' in q: ok = ok and 'currently recorded in stock' in g['answer']
        rows.append((q,ok,'' if ok else f"intent={r['intent']} product={bool(r.get('product'))} reviews={len(r.get('reviews',[]))}"))
    for q, expected in BUSINESS_CASES:
        r=retrieve(q); g=generate(r); ok=r['intent']==expected and r['route']=='TONES' and bool(g.get('answer'))
        if 'owner' in q.lower(): ok = ok and 'verified information' in g['answer'].lower()
        if 'hyderabad' in q.lower(): ok = ok and 'hyderabad' in g['answer'].lower()
        rows.append((q,ok,'' if ok else f"intent={r['intent']} route={r['route']} answer={g['answer']}"))
    for q in SCOPE_CASES:
        r=retrieve(q); g=generate(r); ok=r['route']=='OUT_OF_SCOPE' and g['response_type']=='text'
        rows.append((q,ok,'' if ok else f"route={r['route']} intent={r['intent']}"))
    # Follow-up context.
    r1=retrieve('Show me T-shirts under ₹1500')
    ctx={'filters':r1['filters'],'product_ids':[p['product_id'] for p in r1['products']]}
    r2=retrieve('Only black ones',context=ctx)
    ok=r2['intent']=='PRODUCT_SEARCH' and r2['filters'].get('product_type')=='t-shirt' and r2['filters'].get('color')=='Black' and all(product_matches(p,r2['filters']) [0] for p in r2['products'])
    rows.append(('FOLLOW-UP: Only black ones',ok,'' if ok else str(r2)))
    passed=sum(x[1] for x in rows)
    report={'total':len(rows),'passed':passed,'failed':len(rows)-passed,'accuracy':round(passed/len(rows),4),'results':[{'question':q,'pass':ok,'reason':reason} for q,ok,reason in rows]}
    Path(__file__).with_name('v3_acceptance_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps({k:report[k] for k in ['total','passed','failed','accuracy']},indent=2))
    for q,ok,reason in rows:
        if not ok: print('FAIL',q,reason)

if __name__=='__main__': main()
