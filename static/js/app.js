document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('[data-confirm]').forEach(el=>el.addEventListener('click',e=>{if(!confirm(el.dataset.confirm))e.preventDefault()}));
  document.querySelectorAll('.message').forEach(m=>{setTimeout(()=>{m.style.opacity='0';m.style.transition='opacity .5s'},6000)});
});
