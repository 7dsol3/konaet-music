"use strict";
(() => {
  const body=document.body;
  const menu=document.querySelector('.studio-more');
  if(menu){
    document.addEventListener('click',event=>{if(menu.open&&!menu.contains(event.target))menu.open=false;});
    document.addEventListener('keydown',event=>{if(event.key==='Escape'&&menu.open){menu.open=false;menu.querySelector('summary').focus();}});
    menu.querySelectorAll('button,a').forEach(control=>control.addEventListener('click',()=>{menu.open=false;}));
  }
  let waiting=false;
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
  document.querySelectorAll('.prisma-rim').forEach(surface=>{
    surface.addEventListener('pointermove',event=>{
      if(body.dataset.roomStyle!=='prisma'||body.dataset.prismaLight!=='follow'||reduced||body.classList.contains('glass-reduce-motion')||event.pointerType==='touch'||waiting)return;
      const x=event.clientX,y=event.clientY;waiting=true;
      requestAnimationFrame(()=>{
        const r=surface.getBoundingClientRect();
        body.style.setProperty('--prisma-angle',(Math.atan2(y-r.top-r.height/2,x-r.left-r.width/2)*180/Math.PI+90)+'deg');
        surface.style.setProperty('--instrument-tilt',Math.max(-3,Math.min(3,(x-r.left-r.width/2)/r.width*6))+'deg');
        waiting=false;
      });
    });
    surface.addEventListener('pointerleave',()=>surface.style.removeProperty('--instrument-tilt'));
  });
})();
