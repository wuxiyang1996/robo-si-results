/* Progressive enhancement: the complete gallery and links also work without JS. */
(()=>{
  'use strict';
  const params=new URLSearchParams(location.search);
  let lang=params.get('lang')==='en'?'en':'zh';
  const text=(zh,en)=>lang==='en'?en:zh;
  const toggle=document.getElementById('language-toggle');
  function translate(){
    document.documentElement.lang=lang==='en'?'en':'zh-CN';
    document.querySelectorAll('[data-zh][data-en]').forEach(el=>{el.textContent=el.dataset[lang]});
    document.querySelectorAll('[data-placeholder-zh]').forEach(el=>{el.placeholder=el.dataset[lang==='en'?'placeholderEn':'placeholderZh']});
    document.querySelectorAll('[data-label-zh]').forEach(el=>{el.setAttribute('aria-label',el.dataset[lang==='en'?'labelEn':'labelZh'])});
    if(toggle){toggle.textContent=text('English','中文');toggle.lang=lang==='en'?'zh-CN':'en';toggle.setAttribute('aria-label',text('Switch to English','切换到中文'))}
    const title=document.querySelector('title');if(title?.dataset[lang])title.textContent=title.dataset[lang];
    document.querySelectorAll('a[data-local]').forEach(a=>{const u=new URL(a.href,location.href);lang==='en'?u.searchParams.set('lang','en'):u.searchParams.delete('lang');a.href=u.pathname+u.search+u.hash});
    document.querySelectorAll('input[name=lang]').forEach(el=>{el.value=lang});
  }
  toggle?.addEventListener('click',()=>{lang=lang==='en'?'zh':'en';const u=new URL(location.href);lang==='en'?u.searchParams.set('lang','en'):u.searchParams.delete('lang');history.replaceState(null,'',u);translate()});
  translate();
  document.querySelectorAll('[data-family-gallery]').forEach(gallery=>{
    const buttons=[...gallery.querySelectorAll('[data-family-filter]')];
    const tiles=[...gallery.querySelectorAll('[data-family-card]')];
    const allowed=new Set(buttons.map(b=>b.dataset.familyFilter));
    const count=gallery.querySelector('[data-family-count]');
    function selectCategory(value,write=false){
      const chosen=allowed.has(value)?value:gallery.dataset.defaultCategory;
      let total=0;
      tiles.forEach(tile=>{tile.hidden=chosen!=='all'&&tile.dataset.familyCategory!==chosen;if(!tile.hidden)total++});
      buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.familyFilter===chosen)));
      gallery.querySelectorAll('[data-category-caption]').forEach(el=>{el.hidden=el.dataset.categoryCaption!==chosen});
      gallery.querySelectorAll('[data-paused-family]').forEach(el=>{el.hidden=chosen!=='all'&&el.dataset.familyCategory!==chosen});
      count.dataset.zh=total+' 个任务族';count.dataset.en=total+(total===1?' family':' families');count.textContent=text(count.dataset.zh,count.dataset.en);
      if(write){const u=new URL(location.href);u.searchParams.set('category',chosen);history.replaceState(null,'',u)}
    }
    buttons.forEach(button=>button.addEventListener('click',()=>selectCategory(button.dataset.familyFilter,true)));
    function fromURL(){
      let hash='';try{hash=decodeURIComponent(location.hash.slice(1))}catch{}
      selectCategory(new URLSearchParams(location.search).get('category')||(allowed.has(hash)?hash:gallery.dataset.defaultCategory));
    }
    window.addEventListener('popstate',fromURL);
    window.addEventListener('hashchange',fromURL);
    fromURL();
  });
  function pauseOthers(active){document.querySelectorAll('video').forEach(v=>{if(v!==active)v.pause()})}
  const playback=new WeakMap();
  function loadingStatus(player){
    let status=player.querySelector('.video-loading');
    if(!status){
      status=document.createElement('div');status.className='video-loading';status.hidden=true;
      status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.setAttribute('aria-atomic','true');
      const label=document.createElement('span');label.dataset.zh='正在加载视频…';label.dataset.en='Loading video…';label.textContent=text(label.dataset.zh,label.dataset.en);
      status.append(label);player.append(status);
    }
    return status;
  }
  function returnPlayFocus(state){
    if(state.focusOnReady&&(document.activeElement===state.button||document.activeElement===document.body))state.button.focus({preventScroll:true});
  }
  function revealVideo(video){
    const state=playback.get(video);if(!state||video.readyState<2||state.player.dataset.state!=='loading')return;
    const moveFocus=state.focusOnReady&&(document.activeElement===state.button||document.activeElement===document.body);
    state.player.dataset.state='ready';state.button.hidden=true;state.button.disabled=false;state.button.removeAttribute('aria-busy');
    loadingStatus(state.player).hidden=true;const error=state.player.querySelector('.video-status');if(error)error.hidden=true;
    video.tabIndex=0;video.removeAttribute('aria-hidden');
    if(moveFocus)video.focus({preventScroll:true});
    state.focusOnReady=false;
  }
  document.querySelectorAll('video').forEach(video=>{
    const player=video.closest('.player'),button=player?.querySelector('[data-play-video]');if(!player||!button)return;
    const state={player,button,focusOnReady:false};playback.set(video,state);video.tabIndex=-1;video.setAttribute('aria-hidden','true');
    video.addEventListener('loadeddata',()=>revealVideo(video));video.addEventListener('playing',()=>revealVideo(video));
    video.addEventListener('error',()=>{
      const restoreFocus=document.activeElement===video||(state.focusOnReady&&(document.activeElement===button||document.activeElement===document.body));
      button.hidden=false;button.disabled=false;button.removeAttribute('aria-busy');player.dataset.state='error';
      loadingStatus(player).hidden=true;const error=player.querySelector('.video-status');if(error)error.hidden=false;
      video.tabIndex=-1;video.setAttribute('aria-hidden','true');if(restoreFocus)button.focus({preventScroll:true});
    });
  });
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-play-video]');if(!button)return;
    const player=button.closest('.player'),video=player.querySelector('video');
    const state=playback.get(video);if(!state)return;
    const retry=player.dataset.state==='error'||Boolean(video.error);state.focusOnReady=document.activeElement===button;
    const error=player.querySelector('.video-status');if(error)error.hidden=true;
    pauseOthers(video);button.setAttribute('aria-busy','true');button.disabled=true;player.dataset.state='loading';
    loadingStatus(player).hidden=false;
    if(retry||!video.getAttribute('src')){video.src=video.dataset.videoSrc;video.load()}
    video.play().catch(()=>{
      if(player.dataset.state!=='loading')return;
      if(video.readyState>=2){revealVideo(video);return}
      if(video.error)return;
      player.dataset.state='idle';button.disabled=false;button.removeAttribute('aria-busy');loadingStatus(player).hidden=true;
      returnPlayFocus(state);state.focusOnReady=false;
    });
    if(video.readyState>=2)revealVideo(video);
  });
  document.addEventListener('play',e=>{if(e.target.tagName==='VIDEO')pauseOthers(e.target)},true);
  if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(!e.isIntersecting)e.target.querySelector('video')?.pause()}),{threshold:.05});document.querySelectorAll('.player').forEach(p=>observer.observe(p))}
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseOthers(null)});
  const search=document.getElementById('task-search'),robot=document.getElementById('robot-filter'),tag=document.getElementById('tag-filter'),outcome=document.getElementById('outcome-filter');
  const cards=[...document.querySelectorAll('[data-filter-card]')];
  let clearFilters=null;
  function revealHashTarget(){
    const raw=location.hash.slice(1);if(!raw)return;
    let id=raw;try{id=decodeURIComponent(raw)}catch{}
    const selected=document.getElementById(id);if(!selected)return;
    const card=selected.closest('[data-filter-card]');
    if(card?.hidden)clearFilters?.();
    selected.scrollIntoView({block:'start'});
  }
  if(search&&cards.length){
    const normalize=s=>s.toLocaleLowerCase().normalize('NFKC');
    const filters={q:search,robot,tag,outcome};
    for(const [name,el] of Object.entries(filters)){if(el)el.value=params.get(name)||''}
    function filter(write=true){
      const terms=normalize(search.value).trim().split(/\s+/).filter(Boolean);let n=0;
      cards.forEach(card=>{
        const searchable=normalize(card.dataset.search||'');
        const match=terms.every(t=>searchable.includes(t))&&(!robot?.value||(card.dataset.robots||'').split('|').includes(robot.value))&&(!tag?.value||(card.dataset.tags||'').split('|').includes(tag.value))&&(!outcome?.value||card.dataset.outcome===outcome.value);
        card.hidden=!match;if(match)n++;else card.querySelector('video')?.pause();
      });
      document.getElementById('filter-count').textContent=n+' / '+cards.length;
      document.getElementById('empty-results').hidden=n>0;
      if(write){const u=new URL(location.href);for(const[name,el]of Object.entries(filters)){if(!el)continue;el.value?u.searchParams.set(name,el.value):u.searchParams.delete(name)}history.replaceState(null,'',u)}
    }
    search.addEventListener('input',()=>filter());[robot,tag,outcome].forEach(el=>el?.addEventListener('change',()=>filter()));
    clearFilters=()=>{Object.values(filters).forEach(el=>{if(el)el.value=''});filter()};
    document.querySelectorAll('[data-reset-filter]').forEach(b=>b.addEventListener('click',()=>{clearFilters();search.focus()}));
    window.addEventListener('popstate',()=>{const p=new URLSearchParams(location.search);for(const[name,el]of Object.entries(filters)){if(el)el.value=p.get(name)||''}filter(false);revealHashTarget()});
    filter(false);
  }
  window.addEventListener('hashchange',revealHashTarget);
  revealHashTarget();
  const archive=document.getElementById('archive-selected');
  if(archive){const path=params.get('document');if(path&&/^[\w\-./]+$/.test(path)&&!path.split('/').includes('..')){
    const p=document.createElement('p');p.className='task-id';p.textContent=path;
    const a=document.createElement('a');a.className='text-link';a.href=archive.dataset.archiveBase+path.split('/').map(encodeURIComponent).join('/');a.dataset.zh='打开归档文件';a.dataset.en='Open archived file';a.textContent=text(a.dataset.zh,a.dataset.en);
    archive.append(p,a);archive.hidden=false;
  }}
})();
