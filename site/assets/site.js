/* Progressive enhancement: the complete gallery and links also work without JS. */
(()=>{
  'use strict';
  const params=new URLSearchParams(location.search);
  let lang=params.get('lang')==='en'?'en':'zh';
  const text=(zh,en)=>lang==='en'?en:zh;
  const facetNames=['embodiment','tools','task','difficulty'];
  const playback=new WeakMap();
  function writeURL(url,push=false){
    if(url.href!==location.href)history[push?'pushState':'replaceState'](null,'',url);
  }
  function restoreSelect(select,value){
    if(select)select.value=[...select.options].some(option=>option.value===value)?value:'';
  }
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
  window.addEventListener('popstate',()=>{lang=new URLSearchParams(location.search).get('lang')==='en'?'en':'zh';translate()});
  translate();
  document.querySelectorAll('[data-copy-code]').forEach(button=>button.addEventListener('click',async()=>{
    const example=button.closest('.code-example'),status=example.querySelector('.copy-status');
    try{await navigator.clipboard.writeText(example.querySelector('code').textContent);status.textContent=text('命令已复制','Commands copied')}
    catch{status.textContent=text('请选中代码后复制','Select the code to copy it')}
  }));
  document.querySelectorAll('[data-family-gallery]').forEach(gallery=>{
    const buttons=[...gallery.querySelectorAll('[data-family-filter]')];
    const tiles=[...gallery.querySelectorAll('[data-family-card]')];
    const allowed=new Set(buttons.map(b=>b.dataset.familyFilter));
    const count=gallery.querySelector('[data-family-count]');
    const facets=Object.fromEntries(facetNames.map(name=>[name,gallery.querySelector(`[data-facet-filter="${name}"]`)]));
    let records=[];
    try{records=JSON.parse(gallery.querySelector('[data-facet-records]')?.textContent||'[]')}catch{}
    const recordsByFamily=new Map();
    records.forEach(record=>{if(!recordsByFamily.has(record.family))recordsByFamily.set(record.family,[]);recordsByFamily.get(record.family).push(record)});
    let chosen=gallery.dataset.defaultCategory||'all';
    function selectCategory(value,write=false){
      chosen=allowed.has(value)?value:gallery.dataset.defaultCategory||'all';
      const active=Object.entries(facets).filter(([,select])=>select?.value);
      let total=0,totalTasks=0;
      tiles.forEach(tile=>{
        // Every selected facet must belong to one task, not different tasks in a family.
        const matches=(recordsByFamily.get(tile.dataset.familyCard)||[]).filter(record=>active.every(([name,select])=>(record[name]||[]).includes(select.value)));
        tile.hidden=(chosen!=='all'&&tile.dataset.familyCategory!==chosen)||(active.length>0&&matches.length===0);
        if(!tile.hidden){total++;totalTasks+=matches.length}
        else tile.querySelectorAll('video').forEach(stopPlayback);
        const familyLinks=[...tile.querySelectorAll('[data-family-link]')];
        if(!familyLinks.length&&tile.matches('a'))familyLinks.push(tile);
        familyLinks.forEach(familyLink=>{
          const url=new URL(familyLink.href,location.href);
          for(const [name,select] of Object.entries(facets))select?.value?url.searchParams.set(name,select.value):url.searchParams.delete(name);
          familyLink.href=url.pathname+url.search+url.hash;
        });
      });
      buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.familyFilter===chosen)));
      gallery.querySelectorAll('[data-category-caption]').forEach(el=>{el.hidden=el.dataset.categoryCaption!==chosen});
      gallery.querySelectorAll('[data-paused-family]').forEach(el=>{el.hidden=active.length>0||(chosen!=='all'&&el.dataset.familyCategory!==chosen)});
      count.dataset.zh=total+' 个任务族 · '+totalTasks+' 个任务';count.dataset.en=total+(total===1?' family':' families')+' · '+totalTasks+(totalTasks===1?' task':' tasks');count.textContent=text(count.dataset.zh,count.dataset.en);
      const empty=gallery.querySelector('[data-family-empty]');if(empty)empty.hidden=total>0;
      if(write){
        const url=new URL(location.href);url.searchParams.set('category',chosen);
        for(const [name,select] of Object.entries(facets))select?.value?url.searchParams.set(name,select.value):url.searchParams.delete(name);
        writeURL(url,true);
      }
    }
    buttons.forEach(button=>button.addEventListener('click',()=>selectCategory(button.dataset.familyFilter,true)));
    Object.values(facets).forEach(select=>select?.addEventListener('change',()=>selectCategory(chosen,true)));
    gallery.querySelectorAll('[data-reset-facets]').forEach(button=>button.addEventListener('click',()=>{
      Object.values(facets).forEach(select=>{if(select)select.value=''});
      selectCategory(chosen,true);
    }));
    function fromURL(){
      let hash='';try{hash=decodeURIComponent(location.hash.slice(1))}catch{}
      const query=new URLSearchParams(location.search);
      Object.entries(facets).forEach(([name,select])=>restoreSelect(select,query.get(name)||''));
      selectCategory(query.get('category')||(allowed.has(hash)?hash:gallery.dataset.defaultCategory));
    }
    window.addEventListener('popstate',fromURL);
    window.addEventListener('hashchange',fromURL);
    fromURL();
  });
  function pauseOthers(active){document.querySelectorAll('video').forEach(v=>{if(v!==active)stopPlayback(v)})}
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
  function clearVideoTimer(state){clearTimeout(state.timer);state.timer=null}
  function videoNotice(state,zh,en){
    let notice=state.player.querySelector('.video-status');
    if(!notice){notice=document.createElement('p');notice.className='video-status';notice.setAttribute('role','status');state.player.append(notice)}
    const messageContainer=notice.querySelector('[data-video-error-message], [data-video-message]');
    let message=messageContainer?.querySelector('[data-zh][data-en]')||messageContainer||notice.querySelector(':scope > [data-zh]');
    if(!message){message=document.createElement('span');notice.prepend(message)}
    message.dataset.videoMessage='';message.dataset.zh=zh;message.dataset.en=en;message.textContent=text(zh,en);notice.hidden=false;
  }
  function showVideoControls(state){
    const {video}=state;
    const moveFocus=state.focusOnReady&&(document.activeElement===state.focusOrigin||document.activeElement===document.body);
    state.player.dataset.state='ready';state.button.hidden=true;state.button.disabled=false;state.button.removeAttribute('aria-busy');
    loadingStatus(state.player).hidden=true;const error=state.player.querySelector('.video-status');if(error)error.hidden=true;
    video.controls=true;video.tabIndex=0;video.removeAttribute('aria-hidden');
    if(moveFocus)video.focus({preventScroll:true});
    state.focusOnReady=false;
  }
  function stopPlayback(video){
    const state=playback.get(video);
    if(state){
      state.wantsPlay=false;state.attempt++;state.focusOnReady=false;clearVideoTimer(state);
      state.button.disabled=false;state.button.removeAttribute('aria-busy');const loading=state.player.querySelector('.video-loading');if(loading)loading.hidden=true;
      if(state.player.dataset.state==='loading'){
        if(video.readyState>=1)showVideoControls(state);
        else{state.player.dataset.state='idle';state.button.hidden=false}
      }
    }
    video.pause();
  }
  function showVideoRetry(state,reason){
    const {video,button,player}=state;
    const restoreFocus=document.activeElement===video||(state.focusOnReady&&document.activeElement===state.focusOrigin);
    state.seekTo=video.currentTime||state.seekTo||0;state.wantsPlay=false;state.retryNeeded=true;state.attempt++;clearVideoTimer(state);video.pause();
    player.dataset.state='error';button.hidden=false;button.disabled=false;button.removeAttribute('aria-busy');loadingStatus(player).hidden=true;
    video.tabIndex=-1;video.setAttribute('aria-hidden','true');
    button.dataset.labelZh='重试播放：'+(video.dataset.labelZh||'视频');button.dataset.labelEn='Retry playback: '+(video.dataset.labelEn||'video');
    button.setAttribute('aria-label',text(button.dataset.labelZh,button.dataset.labelEn));
    if(reason==='timeout')videoNotice(state,'加载时间较长，点击画面重试。','Loading is taking longer than expected. Select the video to retry.');
    else videoNotice(state,'视频暂时无法播放，点击画面重试。','The video could not play. Select it to retry.');
    if(restoreFocus)button.focus({preventScroll:true});state.focusOnReady=false;
  }
  function nextVideoSource(state,reason){
    if(state.wantsPlay&&state.sourceIndex+1<state.sources.length){
      state.seekTo=state.video.currentTime||state.seekTo||0;loadVideoSource(state,state.sourceIndex+1);
    }else showVideoRetry(state,reason);
  }
  function armVideoTimer(state){
    clearVideoTimer(state);const attempt=state.attempt,from=state.video.currentTime;state.waitFrom=from;
    state.timer=setTimeout(()=>{
      if(state.attempt!==attempt||!state.wantsPlay)return;
      const video=state.video;
      if(video.readyState<2||(!video.paused&&video.currentTime<=from+.05))nextVideoSource(state,'timeout');
    },15000);
  }
  function loadVideoSource(state,index,reload=true){
    const {video,button,player}=state;
    if(!state.sources[index]){showVideoRetry(state,'source');return}
    clearVideoTimer(state);state.sourceIndex=index;state.wantsPlay=true;state.retryNeeded=false;
    const attempt=++state.attempt;
    player.dataset.state='loading';button.hidden=false;button.disabled=true;button.setAttribute('aria-busy','true');
    button.dataset.labelZh=state.playLabelZh;button.dataset.labelEn=state.playLabelEn;button.setAttribute('aria-label',text(state.playLabelZh,state.playLabelEn));
    const notice=player.querySelector('.video-status');if(notice)notice.hidden=true;loadingStatus(player).hidden=false;
    if(reload||!video.getAttribute('src')||video.error){video.src=state.sources[index];video.load()}
    armVideoTimer(state);
    function rejected(error){
      if(state.attempt!==attempt||!state.wantsPlay)return;
      if(error?.name==='NotAllowedError'){
        state.wantsPlay=false;clearVideoTimer(state);showVideoControls(state);
      }else if(error?.name==='AbortError'){
        // Pausing or changing source can reject play(); neither means the resource failed.
        stopPlayback(video);
      }else if(['NotSupportedError','NetworkError','SecurityError'].includes(error?.name))nextVideoSource(state,'source');
      else showVideoRetry(state,'play');
    }
    try{const promise=video.play();if(promise?.catch)promise.catch(rejected)}catch(error){rejected(error)}
    if(video.readyState>=1)showVideoControls(state);
  }
  function userPlay(state,origin){
    state.focusOrigin=origin;state.focusOnReady=document.activeElement===origin;pauseOthers(state.video);
    const retry=state.retryNeeded||Boolean(state.video.error);
    loadVideoSource(state,retry?0:state.sourceIndex,retry||!state.video.getAttribute('src'));
  }
  document.querySelectorAll('video').forEach(video=>{
    const player=video.closest('.player'),button=player?.querySelector('[data-play-video]');if(!player||!button)return;
    let fallback=[];try{const value=JSON.parse(video.dataset.videoFallbacks||'[]');if(Array.isArray(value))fallback=value}catch{}
    const sources=[...new Set([video.dataset.videoSrc,...fallback].filter(source=>typeof source==='string'&&source.trim()))];
    const state={video,player,button,sources,sourceIndex:0,attempt:0,timer:null,wantsPlay:false,retryNeeded:false,focusOnReady:false,seekTo:0,playLabelZh:button.dataset.labelZh||'播放视频',playLabelEn:button.dataset.labelEn||'Play video'};
    playback.set(video,state);video.tabIndex=-1;video.setAttribute('aria-hidden','true');
    video.addEventListener('loadedmetadata',()=>{
      if(!video.error)state.retryNeeded=false;
      if(state.seekTo>0){try{video.currentTime=Number.isFinite(video.duration)?Math.min(state.seekTo,Math.max(0,video.duration-.1)):state.seekTo;state.seekTo=0}catch{}}
      if(video.readyState>=1)showVideoControls(state);
    });
    ['loadeddata','canplay','playing'].forEach(name=>video.addEventListener(name,()=>{clearVideoTimer(state);if(video.readyState>=1)showVideoControls(state)}));
    video.addEventListener('play',()=>{if(!video.paused){state.wantsPlay=true;if(video.readyState<2)armVideoTimer(state)}});
    video.addEventListener('pause',()=>{if(video.paused&&!video.error)stopPlayback(video)});
    video.addEventListener('waiting',()=>{if(state.wantsPlay&&!video.paused)armVideoTimer(state)});
    video.addEventListener('timeupdate',()=>{if(state.timer&&video.currentTime>state.waitFrom+.05)clearVideoTimer(state)});
    video.addEventListener('error',()=>{
      if(!video.error||!video.getAttribute('src'))return;
      if(video.error.code===1)stopPlayback(video);
      else nextVideoSource(state,'source');
    });
    const fullscreen=player.querySelector('[data-fullscreen-video]');
    if(fullscreen&&!video.requestFullscreen&&!video.webkitEnterFullscreen)fullscreen.hidden=true;
  });
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-play-video], [data-retry-video], [data-fullscreen-video]');if(!button)return;
    const player=button.closest('.player'),video=player.querySelector('video');
    const state=playback.get(video);if(!state)return;
    if(button.hasAttribute('data-retry-video'))state.retryNeeded=true;
    if(button.hasAttribute('data-fullscreen-video')){
      if(video.paused||!video.getAttribute('src')||video.error)userPlay(state,button);
      showVideoControls(state);
      try{
        if(video.requestFullscreen){const request=video.requestFullscreen();if(request?.catch)request.catch(()=>{})}
        else if(video.webkitEnterFullscreen)video.webkitEnterFullscreen();
      }catch{}
    }else userPlay(state,button);
  });
  document.addEventListener('play',e=>{if(e.target.tagName==='VIDEO'&&!e.target.paused)pauseOthers(e.target)},true);
  if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>entries.forEach(e=>{const video=e.target.querySelector('video');if(!e.isIntersecting&&video&&document.fullscreenElement!==video&&!video.webkitDisplayingFullscreen)stopPlayback(video)}),{threshold:.05});document.querySelectorAll('.player').forEach(p=>observer.observe(p))}
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseOthers(null)});
  const search=document.getElementById('task-search'),outcome=document.getElementById('outcome-filter');
  const taskFacets=Object.fromEntries(facetNames.map(name=>[name,document.getElementById(name+'-filter')]));
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
    const filters={q:search,...taskFacets,outcome};
    function readFilters(){
      const query=new URLSearchParams(location.search);search.value=query.get('q')||'';
      for(const [name,select] of Object.entries({...taskFacets,outcome}))restoreSelect(select,query.get(name)||'');
    }
    readFilters();
    function filter(write=true,push=false){
      const terms=normalize(search.value).trim().split(/\s+/).filter(Boolean);let n=0;
      cards.forEach(card=>{
        const searchable=normalize(card.dataset.search||'');
        const match=terms.every(t=>searchable.includes(t))&&Object.entries(taskFacets).every(([name,select])=>!select?.value||(card.dataset[name]||'').split('|').includes(select.value))&&(!outcome?.value||card.dataset.outcome===outcome.value);
        card.hidden=!match;if(match)n++;else card.querySelectorAll('video').forEach(stopPlayback);
      });
      document.getElementById('filter-count').textContent=n+' / '+cards.length;
      document.getElementById('empty-results').hidden=n>0;
      document.querySelectorAll('[data-set-facet]').forEach(button=>button.setAttribute('aria-pressed',String(taskFacets[button.dataset.setFacet]?.value===button.dataset.facetValue)));
      if(write){
        const u=new URL(location.href);
        for(const[name,el]of Object.entries(filters)){if(!el)continue;el.value?u.searchParams.set(name,el.value):u.searchParams.delete(name)}
        let target='';try{target=decodeURIComponent(u.hash.slice(1))}catch{}
        if(target&&document.getElementById(target)?.closest('[data-filter-card]')?.hidden)u.hash='';
        writeURL(u,push);
      }
    }
    search.addEventListener('input',()=>filter());[...Object.values(taskFacets),outcome].forEach(el=>el?.addEventListener('change',()=>filter(true,true)));
    clearFilters=(push=false)=>{Object.values(filters).forEach(el=>{if(el)el.value=''});filter(true,push)};
    document.querySelectorAll('[data-reset-filter]').forEach(b=>b.addEventListener('click',()=>{clearFilters(true);search.focus()}));
    document.querySelectorAll('[data-set-facet]').forEach(button=>button.addEventListener('click',()=>{
      const select=taskFacets[button.dataset.setFacet];if(!select)return;
      select.value=select.value===button.dataset.facetValue?'':button.dataset.facetValue;
      filter(true,true);select.focus({preventScroll:true});select.closest('.toolbar')?.scrollIntoView({block:'start'});
    }));
    window.addEventListener('popstate',()=>{readFilters();filter(false);revealHashTarget()});
    filter(false);
  }
  // Research explorers are optional: their full content stays visible without JS.
  document.querySelectorAll('[data-track-explorer]').forEach(explorer=>{
    const tabs=[...explorer.querySelectorAll('[data-track-tab]')];
    const panels=[...explorer.querySelectorAll('[data-track-panel]')];
    const paired=tabs.map(tab=>panels.find(panel=>panel.id===tab.getAttribute('aria-controls')));
    const tablist=explorer.querySelector('[data-track-tablist]')||tabs[0]?.parentElement;
    if(tabs.length<2||paired.some(panel=>!panel)||!tablist||panels.some(panel=>tablist.contains(panel)))return;
    tablist.setAttribute('role','tablist');
    const verticalTabs=window.matchMedia('(max-width: 760px)');
    const updateTabOrientation=()=>tablist.setAttribute('aria-orientation',verticalTabs.matches?'vertical':'horizontal');
    updateTabOrientation();verticalTabs.addEventListener('change',updateTabOrientation);
    if(!tablist.hasAttribute('aria-label')&&!tablist.hasAttribute('aria-labelledby')){
      tablist.dataset.labelZh='评测设置';tablist.dataset.labelEn='Evaluation tracks';
      tablist.setAttribute('aria-label',text(tablist.dataset.labelZh,tablist.dataset.labelEn));
    }
    tabs.forEach((tab,index)=>{
      tab.setAttribute('role','tab');
      const panel=paired[index];panel.setAttribute('role','tabpanel');
      panel.setAttribute('aria-labelledby',tab.id);panel.tabIndex=0;
    });
    function select(index,focus=false){
      tabs.forEach((tab,i)=>{
        const active=i===index;tab.setAttribute('aria-selected',String(active));
        tab.tabIndex=active?0:-1;tab.classList.toggle('is-active',active);paired[i].hidden=!active;
      });
      if(focus)tabs[index].focus();
    }
    tabs.forEach((tab,index)=>{
      tab.addEventListener('click',()=>select(index));
      tab.addEventListener('keydown',event=>{
        let next=index;
        if(event.key==='ArrowRight'||(verticalTabs.matches&&event.key==='ArrowDown'))next=(index+1)%tabs.length;
        else if(event.key==='ArrowLeft'||(verticalTabs.matches&&event.key==='ArrowUp'))next=(index+tabs.length-1)%tabs.length;
        else if(event.key==='Home')next=0;
        else if(event.key==='End')next=tabs.length-1;
        else return;
        event.preventDefault();select(next,true);
      });
    });
    explorer.classList.add('is-enhanced');
    select(Math.max(0,tabs.findIndex(tab=>tab.getAttribute('aria-selected')==='true')));
  });

  document.querySelectorAll('[data-sandbox-explorer]').forEach((explorer,explorerIndex)=>{
    const parts=[...explorer.querySelectorAll('[data-sandbox-part]')];
    const panels=[...explorer.querySelectorAll('[data-sandbox-panel]')];
    const panelByPart=new Map(panels.map(panel=>[panel.dataset.sandboxPanel,panel]));
    if(!parts.length||parts.some(part=>!panelByPart.has(part.dataset.sandboxPart)))return;
    const steps=[...explorer.querySelectorAll('[data-sandbox-walkthrough] [data-sandbox-step]')]
      .sort((a,b)=>Number(a.dataset.sandboxStep)-Number(b.dataset.sandboxStep));
    const previous=explorer.querySelector('[data-sandbox-prev]'),next=explorer.querySelector('[data-sandbox-next]');
    const count=explorer.querySelector('[data-sandbox-step-count]');
    let currentStep=-1;
    parts.forEach(part=>{
      const component=part.dataset.sandboxPart,panel=panelByPart.get(component);
      if(!part.id)part.id=`sandbox-explorer-${explorerIndex+1}-${component}`;
      panel.setAttribute('role','region');panel.setAttribute('aria-labelledby',part.id);
      panel.tabIndex=0;
    });
    steps.forEach(step=>{
      const panel=panelByPart.get(step.dataset.component);
      if(panel?.id)step.setAttribute('aria-controls',panel.id);
    });
    if(count){count.setAttribute('role','status');count.setAttribute('aria-live','polite');count.setAttribute('aria-atomic','true')}
    function select(component,stepIndex){
      if(!panelByPart.has(component))return;
      currentStep=stepIndex===undefined?steps.findIndex(step=>step.dataset.component===component):stepIndex;
      explorer.dataset.activePart=component;
      parts.forEach(part=>{
        const active=part.dataset.sandboxPart===component;
        part.classList.toggle('is-active',active);part.setAttribute('aria-pressed',String(active));
      });
      panels.forEach(panel=>{panel.hidden=panel.dataset.sandboxPanel!==component});
      steps.forEach((step,index)=>{
        const active=index===currentStep;step.classList.toggle('is-active',active);
        if(active)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');
        step.setAttribute('aria-expanded',String(active));
        const copy=step.parentElement.querySelector('.walkthrough-copy');
        if(copy)copy.hidden=!active;
      });
      if(previous)previous.disabled=currentStep<=0;
      if(next)next.disabled=currentStep<0||currentStep>=steps.length-1;
      if(count){
        const position=currentStep<0?'—':String(currentStep+1);
        count.dataset.zh=position+' / '+steps.length;count.dataset.en=count.dataset.zh;
        count.textContent=text(count.dataset.zh,count.dataset.en);
        count.dataset.labelZh=currentStep<0?'未选择步骤':`第 ${position} 步，共 ${steps.length} 步`;
        count.dataset.labelEn=currentStep<0?'No step selected':`Step ${position} of ${steps.length}`;
        count.setAttribute('aria-label',text(count.dataset.labelZh,count.dataset.labelEn));
      }
    }
    parts.forEach(part=>part.addEventListener('click',()=>{
      const component=part.dataset.sandboxPart;select(component);
      if(window.matchMedia('(max-width: 760px)').matches){
        panelByPart.get(component).scrollIntoView({
          block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'
        });
      }
    }));
    steps.forEach((step,index)=>step.addEventListener('click',()=>select(step.dataset.component,index)));
    previous?.addEventListener('click',()=>{
      if(currentStep>0){
        const index=currentStep-1;select(steps[index].dataset.component,index);
        if(previous.disabled&&document.activeElement===previous)steps[index].focus({preventScroll:true});
      }
    });
    next?.addEventListener('click',()=>{
      if(currentStep>=0&&currentStep<steps.length-1){
        const index=currentStep+1;select(steps[index].dataset.component,index);
        if(next.disabled&&document.activeElement===next)steps[index].focus({preventScroll:true});
      }
    });
    explorer.classList.add('is-enhanced');
    select(steps[0]?.dataset.component||parts[0].dataset.sandboxPart);
  });

  const researchSections=[...document.querySelectorAll('.research-toc a[href^="#"]')].map(link=>{
    let id='';try{id=decodeURIComponent(link.getAttribute('href').slice(1))}catch{}
    return {link,section:document.getElementById(id)};
  }).filter(item=>item.section);
  if(researchSections.length){
    let scheduled=false;
    function updateResearchLocation(){
      scheduled=false;
      const nav=document.querySelector('.site-nav');
      const navCutoff=(nav&&getComputedStyle(nav).position==='sticky'?nav.getBoundingClientRect().bottom:0)+35;
      const scrollPadding=parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop)||0;
      let current=researchSections[0],currentTop=null,hashID='';
      try{hashID=decodeURIComponent(location.hash.slice(1))}catch{}
      researchSections.forEach(item=>{
        const margin=parseFloat(getComputedStyle(item.section).scrollMarginTop)||0;
        // Anchor positioning uses both the scroller's padding and the target's margin.
        const cutoff=Math.max(navCutoff,scrollPadding+margin+3);
        const top=item.section.getBoundingClientRect().top;
        if(top<=cutoff){
          if(currentTop===null||Math.abs(top-currentTop)>1){current=item;currentTop=top}
          else if(item.section.id===hashID)current=item;
        }
      });
      if(window.innerHeight+window.scrollY>=document.documentElement.scrollHeight-3)current=researchSections.at(-1);
      researchSections.forEach(item=>{
        if(item===current)item.link.setAttribute('aria-current','location');else item.link.removeAttribute('aria-current');
      });
    }
    function scheduleResearchLocation(){if(!scheduled){scheduled=true;requestAnimationFrame(updateResearchLocation)}}
    window.addEventListener('scroll',scheduleResearchLocation,{passive:true});
    window.addEventListener('resize',scheduleResearchLocation,{passive:true});
    window.addEventListener('hashchange',scheduleResearchLocation);
    updateResearchLocation();
  }
  window.addEventListener('hashchange',revealHashTarget);
  revealHashTarget();
})();
