'use strict';
let catalogPages=[],catalogNext=null,catalogRequest=null;
let state, dictionary, lang='ru', customLocation=null, lastResult=null, busy=false;
let locationHint='';
let geoStatus='geoHelp', geoAccuracy=0, locationVersion=0;
const $=id=>document.getElementById(id);
function displayText(text){return typeof text==='string'?text.replace(/\s*—\s*/g,' ').trim():text;}
const locales={ru:'ru-RU',kk:'kk-KZ',en:'en-GB'};
function t(key,params={}){let text=dictionary?.ui[lang]?.[key]??key;for(const [k,v] of Object.entries(params))text=text.replaceAll('{'+k+'}',v);return displayText(text);}
function msg(text){return displayText(dictionary.messages[text]?.[lang]??text);}
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=displayText(text);if(cls)n.className=cls;return n;}
function link(text,url){const a=el('a',text);a.href=url;a.target='_blank';a.rel='noreferrer';return a;}
function showGeo(){ updateSearchSettings();$('geo-note').textContent=t(geoStatus,{n:geoAccuracy});if(customLocation&&geoAccuracy>1000)$('geo-note').textContent+=' '+t('geoCoarse');$('geo').classList.toggle('located',Boolean(customLocation)); }
function showEmpty(){const n=el('div',undefined,'empty');n.append(el('div','↗','compass'),el('h3',t('emptyTitle')),el('p',t('emptyBody')));$('cards').replaceChildren(n);}
function applyLanguage(next){
 const previous=lang;const previousQuery=$('query').value;
 lang=next;document.documentElement.lang=lang;document.title=t('brand');
 try{localStorage.setItem('astana-language',lang);}catch{}
 $('query').placeholder=t('queryPlaceholder');updateSearchSettings();
 document.querySelectorAll('[data-t]').forEach(n=>n.textContent=t(n.dataset.t));
 document.querySelectorAll('[data-lang]').forEach(n=>{n.classList.toggle('active',n.dataset.lang===lang);n.setAttribute('aria-pressed',String(n.dataset.lang===lang));n.disabled=busy;});
 if(!previousQuery||['qWalk','qWork','qFamily'].some(k=>previousQuery===dictionary.ui[previous][k])){
  const key=['qWalk','qWork','qFamily'].find(k=>previousQuery===dictionary.ui[previous][k])||'qWalk';$('query').value=t(key);
 }
 if(state){$('connection').textContent=t(state.key_connected?'connected':'offline');const options=$('location').options;for(let i=1;i<options.length;i++)options[i].textContent=t('locations')[i-1];$('data-status').textContent=t('dataStatus',{n:state.count,date:state.collected_at?new Date(state.collected_at).toLocaleDateString(locales[lang]):'—'});}
 if(state?.digis_connected)$('connect-status').textContent=t('connectSuccess');
 showGeo();if(lastResult)render(lastResult);else showEmpty();if(catalogPages.length)renderCatalog();
}
async function init(){
 try{const resources=await Promise.all([fetch('/api/status'),fetch('/i18n.json')]);if(resources.some(r=>!r.ok))throw Error();[state,dictionary]=await Promise.all(resources.map(r=>r.json()));try{const saved=localStorage.getItem('astana-language');if(['ru','kk','en'].includes(saved))lang=saved;}catch{}
 for(const [i] of state.locations.entries()){const o=el('option');o.value=String(i);$('location').append(o);}
 $('use-ai').checked=state.key_connected;$('web-search').checked=state.key_connected||state.digis_connected;applyLanguage(lang);$('submit').disabled=false;if(!state.code_revision||state.restart_required){$('notice').textContent=t('restartRequired');$('submit').disabled=true;}if(state.digis_connected)$('connect-status').textContent=t('lazyCollection');
 }catch{$('notice').textContent='Нет связи с сервером / Сервермен байланыс жоқ / Cannot reach server. Перезапустите приложение / Restart the app.';}
}
document.querySelectorAll('[data-lang]').forEach(b=>b.addEventListener('click',()=>{if(dictionary&&!busy)applyLanguage(b.dataset.lang);}));
$('query').addEventListener('input',()=>{locationHint='';$('intent').value='auto';});
$('location').addEventListener('change',()=>{resetCatalog();locationVersion++;customLocation=null;geoStatus=$('location').value===''?'geoHelp':'manualLocation';showGeo();});
$('geo').addEventListener('click',()=>{
 if(!navigator.geolocation){geoStatus='geoUnavailable';showGeo();return;}
 const version=++locationVersion;customLocation=null;geoStatus='geoWaiting';showGeo();$('geo').disabled=true;
 navigator.geolocation.getCurrentPosition(p=>{
  $('geo').disabled=false;if(version!==locationVersion)return;
  const lat=p.coords.latitude,lon=p.coords.longitude;
  if(!(lat>=50.85&&lat<=51.36&&lon>=71.21&&lon<=71.79)){geoStatus='geoOutside';showGeo();return;}
  resetCatalog();customLocation={lat,lon};$('location').value='';geoAccuracy=Math.ceil(p.coords.accuracy);geoStatus='geoSuccess';showGeo();
 },error=>{$('geo').disabled=false;if(version!==locationVersion)return;geoStatus=error.code===1?'geoDenied':error.code===3?'geoTimeout':'geoUnavailable';showGeo();},{enableHighAccuracy:true,timeout:15000,maximumAge:60000});
});
const scenarios={walk:{q:'qWalk',minutes:'60'},work:{q:'qWork',minutes:'60'},family:{q:'qFamily',minutes:'120'}};
document.querySelectorAll('[data-scenario]').forEach(b=>b.addEventListener('click',()=>{if(!dictionary)return;const k=b.dataset.scenario,s=scenarios[k];$('query').value=t(s.q);$('intent').value=k;}));
function render(data){
 if(data.needs_clarification){
  $('cards').replaceChildren();$('understanding').replaceChildren();$('notice').textContent=t('clarificationTitle');
  const card=el('article',undefined,'card'),form=el('form'),input=el('input'),button=el('button',t('clarificationSend'),'primary');
  input.type='text';input.maxLength=300;input.required=true;input.setAttribute('aria-label',data.question);button.type='submit';
  card.append(el('h3',data.question));form.append(input,button);card.append(form);$('cards').append(card);
  form.addEventListener('submit',event=>{event.preventDefault();if(busy||!input.value.trim())return;
   if(data.origin?.status==='resolved'){customLocation=data.origin;$('location').value='';}
   $('query').value=(data.request_context+'\nУточнение: '+input.value.trim()).slice(0,700);$('intent').value='auto';$('form').requestSubmit();});
  return;
 }
 if(data.needs_location){
  $('cards').replaceChildren();$('understanding').replaceChildren();$('notice').textContent=t('clarificationTitle');
  const card=el('article',undefined,'card'),form=el('form'),input=el('input'),button=el('button',t('clarificationSend'),'primary');
  const question=data.origin?.question||t(data.origin?.status==='not_found'?'locationNotFoundQuestion':'locationQuestion');
  input.type='text';input.maxLength=150;input.required=true;input.placeholder=t('locationExample');input.setAttribute('aria-label',question);button.type='submit';
  card.append(el('h3',question));form.append(input,button);card.append(form);
  if(['no_key','unavailable'].includes(data.origin?.status))card.append(el('p',t('locationProviderIssue'),'tiny'));
  if(data.origin?.status==='ambiguous'){
   card.append(el('p',t('chooseOrigin')));
   for(const choice of data.origin.choices||[]){const b=el('button',choice.name+' · '+choice.address,'primary');b.type='button';b.addEventListener('click',()=>{customLocation=choice;locationHint='';$('location').value='';resetCatalog();$('form').requestSubmit();});card.append(b);}
  }
  form.addEventListener('submit',event=>{event.preventDefault();if(busy||!input.value.trim())return;locationHint=input.value.trim();customLocation=null;$('location').value='';$('form').requestSubmit();});
  $('cards').append(card);return;
 }
 $('cards').replaceChildren();$('result-title').textContent=t(data.items.length?'resultReady':'changePlans');$('count').textContent=t('count',{n:data.items.length});$('notice').textContent=msg(data.note);
 // Translate static response text using its original-language-independent source values.
 if(data.lang&&data.lang!==lang){const reverse={};for(const [ru,values] of Object.entries(dictionary.messages))reverse[values[data.lang]]=values[lang];var translated=text=>reverse[text]??msg(text);}else{var translated=text=>msg(text);}
 $('notice').textContent=translated(data.note);
 $('understanding').replaceChildren();
 if(data.group){$('understanding').append(el('p',t('groupSummary',{n:data.group.size})),el('p',t('groupCompromise')));for(const member of data.group.members)if(member.request)$('understanding').append(el('p',t('groupMember',{n:member.number})+': '+member.request));}
 if(data.origin)$('understanding').append(el('p',t('originResolved')+' '+data.origin.name+' · '+data.origin.address));
 if(data.understanding&&data.lang===lang){$('understanding').append(el('p',t('understood')+data.understanding));}
 else if(data.understanding_mode==='local'){$('understanding').append(el('p',t(data.understanding_error|| (state.key_connected&&$('use-ai').checked?'localWithAi':'localUnderstanding'))));}
 if(data.filters){const f=data.filters;const categories=data.items.length?[...new Set(data.items.map(p=>t(p.kind)))]:[];if(categories.length)$('understanding').append(el('p',t(f.radius_unlimited?(f.minutes===null?'appliedAnywhereNoTime':'appliedAnywhere'):(f.minutes===null?'appliedNoTime':'applied'),{categories:categories.join(', '),minutes:f.minutes,radius:f.radius})));if(f.max_walk_minutes)$('understanding').append(el('p',t('walkLimit',{n:f.max_walk_minutes})));}
 if(data.clarification&&data.lang===lang)$('understanding').append(el('p',data.clarification));

 if(!data.items.length){const n=el('div',undefined,'empty');n.append(el('h3',t('noMatches')),el('p',translated(data.empty)));$('cards').append(n);}
 data.items.forEach((p,i)=>{
  const card=el('article',undefined,'card compact-card'),head=el('div',undefined,'card-head'),title=el('div');
  title.append(el('div',t(p.kind),'category'),el('h3',p.names?.[lang]||p.name));head.append(el('div',String(i+1).padStart(2,'0'),'number'),title);card.append(head);
  const metrics=el('div',undefined,'metrics compact-metrics');
  for(const [key,value] of [['distance',p.distance_m],['walkTime',p.walk_minutes]])metrics.append(el('span',t(key,{n:value})));
  card.append(metrics,el('p',t('whyLabel')+' '+translated(p.why),'card-why'));
  if(p.group_match){const g=p.group_match;card.append(el('p',g.specified?t('groupMatch',{n:g.count,total:g.specified}):t('groupCommonOnly'),'compact-group'));}
  const rating=(p.external_sources||[]).find(source=>Number.isFinite(source.rating));
  const ratingLine=el('p',undefined,'compact-rating');
  if(rating){ratingLine.append(link('★ '+rating.rating.toLocaleString(locales[lang],{minimumFractionDigits:1,maximumFractionDigits:2})+'/5',rating.url));if(Number.isInteger(rating.review_count))ratingLine.append(el('span',' · '+t('reviewsCount',{n:rating.review_count})));}
  else ratingLine.textContent=t('compactNoRating');
  card.append(ratingLine);
  if(p.address)card.append(el('p',p.address,'compact-address'));
  const links=el('div',undefined,'card-links');links.append(link(p.source_provider?`${p.source_provider} ↗`:t('source'),p.source),link(t('map'),p.source));card.append(links);
  card.append(el('p',t('compactCaution'),'compact-caution'));

  const more=el('details',undefined,'card-more'),content=el('div',undefined,'card-more-content');more.append(el('summary',t('cardMore')));
  if(p.group_match&&p.group_match.specified){const g=p.group_match,box=el('div',undefined,'group-match');
   const members=list=>list.map(n=>t('groupMember',{n})).join(', ');
   if(g.matched.length)box.append(el('p',t('groupMatched')+' '+members(g.matched)));
   if(g.unmatched.length)box.append(el('p',t('groupUnmatched')+' '+members(g.unmatched)));
   if(g.uncertain.length)box.append(el('p',t('groupUncertain')+' '+members(g.uncertain)));
   if(g.unspecified.length)box.append(el('p',t('groupUnspecified')+' '+members(g.unspecified)));
   content.append(box);
  }
  const extraMetrics=el('div',undefined,'metrics');
  for(const [key,value] of [['visitTime',p.visit_minutes],['roundTrip',p.total_minutes]])extraMetrics.append(el('span',t(key,{n:value})));
  content.append(extraMetrics);
  const plan=el('div',undefined,'plan');plan.append(el('strong',t('planLabel')),el('p',t('humanPlan',{walk:p.walk_minutes,visit:p.visit_minutes,action:p.generated?p.action:translated(p.action)})));
  plan.append(el('small',t(p.generated?(data.lang===lang?'generated':'generatedOther'):'fallback')));content.append(plan);
  const hours=el('section',undefined,'hours'),day=p.hours_day;
  if(day?.date){
   const date=new Date(day.date+'T12:00:00+05:00').toLocaleDateString(locales[lang],{timeZone:'Asia/Almaty',weekday:'long',day:'numeric',month:'long'});
   const intervals=(day.intervals||[]).map(interval=>interval.from+'–'+interval.to).join(', ');
   hours.append(el('p',t('hoursForDay',{date,hours:day.status==='listed'?intervals:t(day.status==='day_off'?'scheduleDayOff':'scheduleDayUnknown')}),'day-hours'));
  }else hours.append(el('p',t('scheduleDayUnknown'),'day-hours'));
  hours.append(el('p',t('openingUnconfirmed'),'opening-status'));content.append(hours);
  if(p.building_name)content.append(el('p',t('insideBuilding',{name:p.building_name})+(p.location_comment?' · '+p.location_comment:'')));
  else if(p.location_comment)content.append(el('p',p.location_comment));
  if(p.verification_label)content.append(el('p',translated(p.verification_label),'verification-note'));
  const sources=el('section',undefined,'review-sources');sources.append(el('h4',t('reviewSources')));
  if(!p.external_sources?.length)sources.append(el('p',t('noReviews')));
  for(const source of p.external_sources||[]){
   const row=el('div',undefined,'review-source');
   const score=Number.isFinite(source.rating)?` ★ ${source.rating.toLocaleString(locales[lang],{minimumFractionDigits:1,maximumFractionDigits:2})}/5`:'';
   row.append(link(source.provider+score+' ↗',source.url));if(!score)row.append(el('p',t('sourceNoRating')));
   if(Number.isInteger(source.rating_count))row.append(el('span',t('ratingsCount',{n:source.rating_count})));
   if(Number.isInteger(source.review_count))row.append(el('span',t('reviewsCount',{n:source.review_count})));
   if(score)row.append(link(t('readReviews'),source.url));
   row.append(el('p',t(source.mode==='api'?'liveData':'snapshot',{date:source.checked_at?new Date(source.checked_at).toLocaleDateString(locales[lang]):'—'}),'tiny'));sources.append(row);
  }
  content.append(sources);
  const details=el('details',undefined,'card-data');details.append(el('summary',t('usedData')),el('p',`ID: ${p.id}`));
  if(p.description&&!p.description.startsWith('Описание отсутствует'))details.append(el('p',`${t('sourceText')}: ${p.description}`));
  details.append(el('p',`${t('internet')}: ${p.internet||t('unknown')}.`));content.append(details);
  more.append(content);card.append(more);$('cards').append(card);
 });
 $('warnings').replaceChildren(...data.warnings.map(s=>el('p','• '+translated(s))));
 $('public-search').replaceChildren();
 if(data.public_search?.status!=='off'){
  const section=el('details',undefined,'web-report');section.append(el('summary',t('publicSearch')));
  if(data.provider_status==='not_connected')section.append(el('p',t('digisNotConnected')));
  if(data.public_search?.status==='searched'){
   section.append(el('p',t('webUnverified'),'notice'),el('pre',data.public_search.text));
   for(const url of data.public_search.links||[])section.append(link(url,url));
  }else section.append(el('p',t('webUnavailable')));
  $('public-search').append(section);
 }
}
$('form').addEventListener('submit',async e=>{
 e.preventDefault();if(!state||busy)return;
 const selected=$('location').value,loc=customLocation||(selected!==''?state.locations[Number(selected)]:null);
 if(!loc&&!$('query').value.trim()){$('notice').textContent=t('textLocationHelp');return;}
 busy=true;$('submit').disabled=true;$('submit').textContent=t('loading');document.querySelectorAll('[data-lang]').forEach(b=>b.disabled=true);document.querySelector('.results').setAttribute('aria-busy','true');$('notice').textContent=t('loadingNotice');
 const body={...(loc?{lat:loc.lat,lon:loc.lon}:locationHint?{location_hint:locationHint}:{}),lang,...($('minutes').value?{minutes:Number($('minutes').value)}:{}),...($('radius').value?{radius:Number($('radius').value)}:{}),query:$('query').value,intent:$('intent').value,weather:$('weather').value,use_ai:$('use-ai').checked,web_search:$('web-search').checked};
 try{const r=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':state.token},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw Error();lastResult=data;render(data);if(innerWidth<740)$('result-title').scrollIntoView({behavior:'smooth'});}
 catch{$('notice').textContent=t('requestError');}
 finally{busy=false;$('submit').disabled=false;$('submit').textContent=t('submit');document.querySelectorAll('[data-lang]').forEach(b=>b.disabled=false);document.querySelector('.results').setAttribute('aria-busy','false');}
});
init();


function resetCatalog(){catalogPages=[];catalogNext=null;catalogRequest=null;$('catalog-items').replaceChildren();$('catalog-more').hidden=true;$('catalog-status').textContent='';}
function chosenLocation(){const selected=$('location').value;return customLocation||(selected!==''?state.locations[Number(selected)]:null);}
function catalogCategory(place){
 if(dictionary.ui[lang][place.kind])return t(place.kind);
 const key=place.osm_category?.key;
 return key==='shop'?t('catalogShop'):key==='office'?t('catalogOffice'):key==='craft'?t('catalogCraft'):t('catalogOther');
}
function renderCatalog(){
 $('catalog-items').replaceChildren();
 for(const place of catalogPages){
  const card=el('article',undefined,'catalog-item');card.append(el('h3',place.names?.[lang]||place.name),el('p',catalogCategory(place)+' · '+t('distance',{n:place.distance_m})));
  if(place.address)card.append(el('p',place.address));if(place.building_name)card.append(el('p',t('insideBuilding',{name:place.building_name})+(place.location_comment?' · '+place.location_comment:'')));
  if(place.description)card.append(el('p',place.description));
  card.append(el('p',`${place.lat.toFixed(5)}, ${place.lon.toFixed(5)}`));
  if(place.hours)card.append(el('p',place.hours));
  for(const c of place.contacts||[])if(c.value)card.append(el('p',`${c.type||''}: ${c.value}`));
  for(const source of place.external_sources||[]){const rating=Number.isFinite(source.rating)?` ★ ${source.rating}/5`:'';card.append(link(source.provider+rating,source.url));}
  card.append(link(t('source'),place.source));$('catalog-items').append(card);
 }
 $('catalog-more').hidden=catalogNext===null;
}
async function browseCatalog(append){
 if(!state)return;const location=chosenLocation();if(!location){$('catalog-status').textContent=t('locationRequired');return;}
 if(!$('radius').value&&!lastResult?.filters?.radius){$('catalog-status').textContent=t('catalogRadiusRequired');return;}
 if(!append){catalogPages=[];catalogNext=0;catalogRequest={lat:location.lat,lon:location.lon,radius:Number($('radius').value)||lastResult.filters.radius,query:$('catalog-query').value,lang};}
 if(catalogNext===null)return;$('catalog-browse').disabled=true;$('catalog-more').disabled=true;$('catalog-status').textContent=t('catalogLoading');
 try{
  const response=await fetch('/api/catalog',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':state.token},body:JSON.stringify({...catalogRequest,lang,offset:catalogNext})});
  const result=await response.json();if(!response.ok)throw Error();catalogPages.push(...result.items);catalogNext=result.next_offset;
  $('catalog-status').textContent=t('catalogTotal',{n:result.total});renderCatalog();
 }catch{$('catalog-status').textContent=t('requestError');}
 finally{$('catalog-browse').disabled=false;$('catalog-more').disabled=false;}
}
$('catalog-browse').addEventListener('click',()=>browseCatalog(false));
$('catalog-more').addEventListener('click',()=>browseCatalog(true));

async function pollCollection(){
 try{
  const r=await fetch('/api/status');if(!r.ok)return;const fresh=await r.json();
  state={...state,...fresh};const c=fresh.collection;
  if(!c)return;
  if(c.status==='collecting'||c.status==='idle'){
   $('connect-status').textContent=t('collectionLoading',{n:c.count});
   setTimeout(pollCollection,2000);
  }else if(c.status==='ready'){
   $('connect-status').textContent=t('collectionReady',{n:c.count});
   $('data-status').textContent=t('dataStatus',{n:fresh.count,date:fresh.collected_at?new Date(fresh.collected_at).toLocaleDateString(locales[lang]):'—'});
  }else if(c.status==='failed')$('connect-status').textContent=t('collectionFailed');
 }catch{$('connect-status').textContent=t('requestError');}
}



function updateSearchSettings(){
 if(!dictionary)return;
 const count=['location','minutes','radius'].filter(id=>$(id).value!=='').length+Number($('weather').value!=='any')+Number($('intent').value!=='auto');
 $('active-settings').textContent=count?t('settingsCount',{n:count}):'';
}
for(const id of ['location','minutes','radius','weather','intent'])$(id).addEventListener('change',updateSearchSettings);
