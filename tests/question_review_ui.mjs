// Lightweight unit checks for the local page's save/resume logic. This uses a
// minimal in-memory DOM fixture, not a browser or real human-review answers.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const template=await fs.readFile(new URL('../scripts/templates/question_review.html',import.meta.url),'utf8');
class Element {
 constructor(){this.children=[];this.listeners={};this.value='';this.textContent='';}
 append(...items){this.children.push(...items);}
 replaceChildren(){this.children=[];}
 addEventListener(name,callback){this.listeners[name]=callback;}
 click(){this.clicked=true;}
 focus(){this.focused=true;}
}
const ids=Object.fromEntries(['review-data','cards','reviewer','message','progress','save','resume'].map(k=>[k,new Element()]));
const original={schema_version:1,sample_id:'fictional-ui-test',rows:[
 {review_id:'question-001',corpus:'fictional',text:'When is the hearing?',text_sha256:'fixture1',human_question:'',reviewer:'',notes:''},
 {review_id:'question-002',corpus:'fictional',text:'The hearing ended.',text_sha256:'fixture2',human_question:'',reviewer:'',notes:''}]};
ids['review-data'].textContent=JSON.stringify(original);
const downloads=[];
const context=vm.createContext({document:{getElementById:id=>ids[id],createElement:()=>new Element()},
 structuredClone,Blob,URL:{createObjectURL:blob=>{downloads.push(blob);return 'blob:fixture';},revokeObjectURL:()=>{}},setTimeout:fn=>fn()});
vm.runInContext(template.match(/<script>\s*([\s\S]*?)<\/script>/)[1],context);
assert.equal(ids.cards.children.length,2);
assert.equal(ids.progress.textContent,'0 / 2 answered');
const select=()=>ids.cards.children[0].children[2].children[0];
select().value='yes';select().listeners.change();
assert.equal(ids.progress.textContent,'1 / 2 answered');
ids.save.listeners.click();assert.equal(downloads.length,0);
assert.match(ids.message.textContent,/Enter your name/);
ids.reviewer.value='Fictional test reviewer';ids.save.listeners.click();
const saved=JSON.parse(await downloads[0].text());
assert.equal(saved.rows[0].human_question,'yes');
assert.equal(saved.rows[0].reviewer,'Fictional test reviewer');
select().value='unsure';select().listeners.change();
assert.equal(ids.progress.textContent,'0 / 2 answered, 1 unsure');
const resume=async data=>ids.resume.listeners.change({target:{files:[{text:async()=>JSON.stringify(data)}],value:'fixture'}});
await resume(saved);assert.equal(ids.progress.textContent,'1 / 2 answered');
assert.equal(select().value,'yes');
const stale=structuredClone(saved);stale.rows[0].text='Changed source';
await resume(stale);assert.match(ids.message.textContent,/does not match/);
assert.equal(select().value,'yes');
const duplicate=structuredClone(saved);duplicate.rows[1]=duplicate.rows[0];
await resume(duplicate);assert.match(ids.message.textContent,/does not match/);
await resume(original);assert.equal(ids.progress.textContent,'0 / 2 answered');
assert.equal(select().value,'');
console.log('PASS: blank state, answer counter, reviewer guard, JSON download, resume, invalid-import preservation, reset.');
