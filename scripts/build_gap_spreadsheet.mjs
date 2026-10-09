// Optional development workbook builder. Requires @oai/artifact-tool in the
// artifact runtime, not the Hearing Lens application's Python dependencies.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const [inputPath, destination, preparedDate='2026-10-06'] = process.argv.slice(2);
if (!inputPath || !destination) throw Error('Usage: build_gap_spreadsheet.mjs input.json output-folder [YYYY-MM-DD]');
if (!/^\d{4}-\d{2}-\d{2}$/.test(preparedDate) || !Number.isFinite(Date.parse(preparedDate)) ||
    new Date(preparedDate).toISOString().slice(0,10)!==preparedDate) throw Error('Use a valid preparation date.');
const input = JSON.parse(await fs.readFile(inputPath, 'utf8'));
await fs.mkdir(destination, {recursive:true});
const outputPath = path.join(destination, `Hearing_Lens_Gap_Check_${preparedDate}.xlsx`);
try { await fs.access(outputPath); throw Error('Output exists; preserve the reviewed workbook.'); }
catch(error) { if(error.code !== 'ENOENT') throw error; }
const wb = Workbook.create();
const check = wb.worksheets.add('Gap check'), source = wb.worksheets.add('Source groups');
for(const sheet of [check,source]) sheet.showGridLines=false;
check.tabColor='#234B72';
check.getRange('A1:I36').format.font={name:'Arial',size:11,color:'#202936'};
check.getRange('A1:I36').format.rowHeight=24;
check.getRange('A1:A36').format.columnWidth=26;
check.getRange('B1:I36').format.columnWidth=15;
check.getRange('H1:H36').format.columnWidth=25;
check.getRange('I1:I36').format.columnWidth=14;
check.getRange('A2').values=[['Representation-gap calculation check']];
check.getRange('A2').format.font={size:16,bold:true};
check.getRange('A3').values=[[`Fictional 1,000-comment sample. Prepared ${preparedDate}.`]];
check.getRange('A4').values=[['Formula check completed by software. Human hand-check remains pending.']];
check.getRange('A4').format.font={color:'#8A4B08'};
check.getRange('A6:I6').values=[['Group','Count','Known rows','Reference','Participation','Gap (pp)','Ratio','Flag','Check']];
const sourceEnd=input.source_rows.length+1;
source.getRange('A1:B1').values=[['Role','Housing tenure']];
source.getRange(`A2:B${sourceEnd}`).values=input.source_rows;
source.getRange(`A1:B${sourceEnd}`).format.font={name:'Arial',size:11};
source.getRange(`A1:B${sourceEnd}`).format.columnWidth=27;
source.getRange('D2').values=[['Source: '+input.source]];
source.getRange('D3').values=[['SHA-256: '+input.source_sha256]];
source.getRange('D4').values=[['One fictional comment per row. No missing categories or dropped rows in this fixture.']];
source.getRange('D5').values=[['Reference shares: scripts/validate_gaps.py, REFERENCES. These are fictional assumptions.']];
source.getRange('D2:D5').format.font={name:'Arial',size:11};
source.freezePanes.freezeRows(1);
for(const [index,row] of input.pipeline_rows.entries()) {
 const r=7+index, p=21+index, col=row.field==='subgroup__role'?'A':'B';
 const ref=input.references[row.field][row.group];
 check.getRange(`A${r}`).values=[[row.group]];
 check.getRange(`D${r}`).values=[[Number(ref.replace('%',''))/100]];
 check.getRange(`B${r}:C${r}`).formulas=[[
   `=COUNTIFS('Source groups'!$${col}$2:$${col}$${sourceEnd},A${r})`,
   `=ROWS('Source groups'!$${col}$2:$${col}$${sourceEnd})-COUNTBLANK('Source groups'!$${col}$2:$${col}$${sourceEnd})`]];
 check.getRange(`E${r}:I${r}`).formulas=[[
   `=IF(C${r}=0,"n.a.",B${r}/C${r})`,
   `=IF(C${r}=0,"n.a.",100*(E${r}-D${r}))`,
   `=IF(OR(C${r}=0,D${r}=0),"n.a.",E${r}/D${r})`,
   `=IF(D${r}=0,"zero_reference",IF(B${r}<0.75*D${r}*C${r},"underrepresented",IF(B${r}>1.25*D${r}*C${r},"overrepresented","within_range")))`,
   `=IF(AND(B${r}=B${p},ROUND(D${r}-C${p},12)=0,ROUND(E${r}-D${p},12)=0,ROUND(F${r}-E${p},12)=0,ROUND(G${r}-F${p},12)=0,H${r}=G${p}),"Match","Difference")`]];
 check.getRange(`A${p}:G${p}`).values=[[row.group,row.count,row.reference_share,row.participation_share,row.gap_percentage_points,row.representation_ratio,row.flag]];
}
check.getRange('D7:E14').setNumberFormat('0.0%');
check.getRange('F7:F14').setNumberFormat('0.000');
check.getRange('G7:G14').setNumberFormat('0.000000');
check.getRange('B7:C14').setNumberFormat('#,##0');
check.getRange('D7:D14').format.fill='#FFF2CC';
check.getRange('A16').values=[['Participation = count / known rows. Gap (pp) = 100 × (participation − reference). Ratio = participation / reference.']];
check.getRange('A17').values=[['Checks round numerical differences to 12 decimals. Counts and flags must agree exactly. Amber cells are fictional inputs.']];
check.getRange('A18').values=[['This fixed fixture has no groups below 10. Separate automated tests cover suppression and missing-group behavior.']];
check.getRange('A20:G20').values=[['Pipeline snapshot','Count','Reference','Participation','Gap (pp)','Ratio','Flag']];
check.getRange('C21:D28').setNumberFormat('0.0%');
check.getRange('E21:E28').setNumberFormat('0.000');
check.getRange('F21:F28').setNumberFormat('0.000000');
check.getRange('G21:G28').format.columnWidth=25;
check.getRange('H7:H14').format.horizontalAlignment='center';
check.getRange('G21:G28').format.horizontalAlignment='center';
check.getRange('A30').values=[['Human check: use the source categories to verify counts and work through the formulas.']];
check.getRange('A31').values=[['Example: Parent 541 / 1,000 = 54.1%; (54.1% − 40%) × 100 = 14.1 pp; 54.1% / 40% = 1.3525.']];
check.getRange('A32').values=[['A person still needs to check these calculations to complete the brief’s hand-computed check.']];
check.getRange('A34:B35').values=[['Reviewed by',null],['Review date',null]];
check.getRange('B34:C35').format.fill='#FFF2CC';
for(const range of [check.getRange('A6:I6'),check.getRange('A20:G20'),source.getRange('A1:B1')]) {
 range.format.fill='#234B72';range.format.font={name:'Arial',size:11,color:'#FFFFFF',bold:true};
 range.format.horizontalAlignment='center';range.format.rowHeight=28;
}
check.getRange('I7:I14').conditionalFormats.add('cellIs',{operator:'equal',formula:'"Difference"',format:{fill:'#FCE4D6',font:{color:'#9C0006',bold:true}}});
// Test a changed baseline, restore it, and verify actual formula recalculation.
const original=check.getRange('D7').values[0][0];
check.getRange('D7').values=[[0]];wb.recalculate();
if(check.getRange('G7').values[0][0]!=='n.a.'||check.getRange('H7').values[0][0]!=='zero_reference')throw Error('Zero reference handling failed.');
check.getRange('D7').values=[[original/2]];wb.recalculate();
if(check.getRange('I7').values[0][0]!=='Difference')throw Error('Input change did not affect comparison.');
check.getRange('D7').values=[[original]];wb.recalculate();
const calculated=check.getRange('A7:I14').values;
if(calculated.some(row=>row[8]!=='Match'))throw Error('Spreadsheet differs from pipeline: '+JSON.stringify(calculated));
for(const [i,row] of calculated.entries()) {
 const expected=input.pipeline_rows[i];
 for(const [col,key] of [[3,'reference_share'],[4,'participation_share'],[5,'gap_percentage_points'],[6,'representation_ratio']])
  if(Math.abs(row[col]-expected[key])>1e-12)throw Error('Independent numeric comparison failed.');
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan'});
await fs.writeFile(path.join(destination,'spreadsheet-formula-inspection.txt'),errors.ndjson);
const inspection=await wb.inspect({kind:'table',range:'Gap check!A6:I14',include:'values,formulas',tableMaxRows:9,tableMaxCols:9});
await fs.writeFile(path.join(destination,'spreadsheet-calculation-inspection.txt'),inspection.ndjson);
for(const [name,range,file] of [['Gap check','A1:I35','gap-check-preview.png'],['Source groups','A1:L8','source-groups-preview.png']]) {
 const preview=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(destination,file),new Uint8Array(await preview.arrayBuffer()));
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(outputPath);
await fs.writeFile(path.join(destination,'spreadsheet-validation.json'),JSON.stringify({source_sha256:input.source_sha256,checked_groups:calculated.length,all_match:true,tolerance:1e-12,counts_and_flags:'exact',baseline_recalculation_checked:true,human_review:'pending',native_excel_recalculation:'not tested',rows:calculated},null,2));
console.log(JSON.stringify({outputPath,checked_groups:calculated.length,all_match:true,human_review:'pending'}));
