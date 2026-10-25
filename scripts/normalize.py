"""Normalize 래퍼 정 JSON into the site schema; no remote URL fetch."""
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
KST=timezone(timedelta(hours=9))
def url(v):
    if not isinstance(v,str): return None
    p=urlparse(v)
    return v if p.scheme in ('http','https') and p.netloc else None
def normalize(raw):
    if not isinstance(raw,dict): raise ValueError('JSON object required')
    date=raw.get('briefing_date') or raw.get('date')
    if not isinstance(date,str): raise ValueError('Missing briefing_date')
    try: d=datetime.fromisoformat(date.replace('Z','+00:00'))
    except ValueError as e: raise ValueError('Invalid briefing_date') from e
    if d.tzinfo is None:
        if len(date)!=10: raise ValueError('Timezone required')
        d=d.replace(tzinfo=KST)
    if d.astimezone(KST).date()>datetime.now(KST).date(): raise ValueError('Future briefing date')
    topic=raw.get('topic') or raw.get('theme')
    if not isinstance(topic,str) or not topic.strip(): raise ValueError('Missing topic')
    refs=raw.get('references')
    if not isinstance(refs,list) or not 12<=len(refs)<=15: raise ValueError('12–15 references required')
    result=[]
    for i,r in enumerate(refs,1):
        if not isinstance(r,dict) or not isinstance(r.get('title'),str) or not r['title'].strip(): raise ValueError(f'Reference {i}: missing title')
        v=r.get('verification') or {}
        if not isinstance(v,dict): raise ValueError(f'Reference {i}: invalid verification')
        source=url(r.get('original_page_url') or r.get('source_url'))
        if not source or v.get('source_match') in (False, None, ''): raise ValueError(f'Reference {i}: source matching evidence required')
        image=url(r.get('image_url')) if v.get('image_access') in (True, 'verified_accessible') else None
        result.append({'title':r['title'].strip(),'creator':r.get('creator'),'year':r.get('creation_year',r.get('year')),'image_url':image,'source_url':source,'reason':r.get('recommendation') or r.get('reason'),'visual_features':r.get('visual_features'),'verification_reason':None if image else '이미지 접근 검증 미완료 · 원본 출처에서 확인','verification':v,'usage_rights_status':r.get('usage_rights_status')})
    trends=raw.get('trends') if raw.get('trends') is not None else raw.get('signals')
    if not isinstance(trends,list) or not 3<=len(trends)<=5: raise ValueError('3–5 trends required')
    signals=[]
    for i,t in enumerate(trends,1):
        if not isinstance(t,dict) or not all(isinstance(t.get(k),str) and t[k].strip() for k in ('title','summary')): raise ValueError(f'Trend {i}: missing title/summary')
        checked=t.get('checked_date') or t.get('checked_at')
        if not isinstance(checked,str) or not checked.strip(): raise ValueError(f'Trend {i}: missing verification date')
        urls=t.get('source_urls') or []
        if not isinstance(urls,list): raise ValueError(f'Trend {i}: invalid source_urls')
        source=url(t.get('source_url')) or next((u for u in urls if url(u)),None)
        if not source: raise ValueError(f'Trend {i}: source required')
        signals.append({'title':t['title'],'summary':t['summary'],'checked_at':checked,'source_url':source})
    return {'date':d.astimezone(KST).date().isoformat()+'T12:00:00+09:00','theme':topic.strip(),'references':result,'signals':signals,'schema_version':'1.0','week_id':raw.get('week_id'),'target_count':raw.get('target_count',15),'actual_count':len(result),'shortfall_reason':raw.get('shortfall_reason')}
