// Execute every graph/stage/color/filter mode against a minimal DOM. This checks
// control semantics and emitted SVG counts, not browser layout or visual quality.
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const source = [...html.matchAll(/<script(?: [^>]*)?>([\s\S]*?)<\/script>/g)].map(match => match[1]);
if (source.length !== 2) throw Error('Unexpected inline script count');
class Element {
  constructor(tag='div') { this.tag=tag; this.children=[]; this.style={}; this.attributes={}; this.listeners={}; this.value=''; this.checked=false; this.textContent=''; this.innerHTML=''; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=[...nodes]; }
  setAttribute(key,value) { this.attributes[key]=String(value); }
  addEventListener(name,listener) { this.listeners[name]=listener; }
  querySelector(selector) { return this.queries[selector]; }
}
const elements={};
for(const id of ['fixtureData','round','color','next','shortcuts','labels','tooltip','roundLabel','legend','save'])elements[id]=new Element();
elements.fixtureData.textContent=source[0];
elements.round.value='0';elements.color.value='backbone';elements.next.checked=true;elements.shortcuts.checked=true;
for(const id of ['left','right']) {
  const panel=elements[id]=new Element();panel.queries={};
  for(const selector of ['select','h2','.description','.stats','svg.graph','.detail','.history'])panel.queries[selector]=new Element(selector==='svg.graph'?'svg':'div');
}
const context={console,JSON,Map,Set,Math,Number,String,Array,Error,innerWidth:1200,innerHeight:900,
  document:{getElementById:id=>elements[id],createElementNS:(_,tag)=>new Element(tag),createElement:tag=>new Element(tag)},
  setTimeout,URL,Blob};
const checks=`
let checked=0;
for(const fixture of data.fixtures) {
 panels[0].querySelector('select').value=fixture.family;
 for(let r=0;r<fixture.stages.length;r++)for(const mode of ['backbone','mst','level'])for(const showShortcuts of [false,true])for(const highlight of [false,true]) {
  round.value=String(r);color.value=mode;shortcuts.checked=showShortcuts;next.checked=highlight;render();
  for(const panel of panels) {
   const f=choose(panel),s=f.stages[Math.min(r,f.stages.length-1)],svg=panel.querySelector('svg.graph');
   const visible=s.edges.filter(e=>showShortcuts||f.source_edges[e[2]][5]);
   const lines=svg.children.filter(e=>e.tag==='line');
   const circles=svg.children.filter(e=>e.tag==='circle');
   if(lines.length!==visible.length||circles.length!==s.vertices.length)throw Error('Incorrect drawing counts');
   const highlighted=lines.filter(e=>e.attributes.stroke==='#c76019').length;
   const expected=highlight?visible.filter(e=>s.selected_next.includes(e[2])).length:0;
   if(highlighted!==expected)throw Error('Incorrect selection highlights');
   if(!svg.children.some(e=>e.textContent.includes('showing '+visible.length+' of '+s.edges.length+' remaining edges')))throw Error('Incorrect visibility label');
  }
  checked++;
 }
}
console.log(JSON.stringify({control_combinations:checked,panels_checked:2*checked,status:'pass',scope:'Independent JavaScript execution with DOM stub; browser layout not checked'},null,2));
`;
vm.runInNewContext(source[1]+checks,context,{timeout:10000});
