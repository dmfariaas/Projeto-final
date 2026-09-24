import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root=process.cwd();
const out=path.join(root,'tmp','academico');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(root,'4992220_Metricas_Qualidade.xlsx')));
const mode=process.argv[2]||'inspect';
const indicators=wb.worksheets.getItem('Indicadores');
if(mode==='inspect'){
  const blob=await wb.render({sheetName:'Indicadores',range:'A1:F18',scale:1.3,format:'png'});
  await fs.writeFile(path.join(out,'planilha_antes.png'),new Uint8Array(await blob.arrayBuffer()));
  console.log((await wb.inspect({kind:'table',range:'Indicadores!A15:D18',include:'values,formulas',tableMaxRows:4,tableMaxCols:4})).ndjson);
}else{
  const source=path.join(root,'4992220_Projeto_Qualidade_Completo','Projeto_Qualidade_4992220','evidencias');
  const ui=JSON.parse(await fs.readFile(path.join(source,'interface.json'),'utf8'));
  const tests=wb.worksheets.getItem('Testes');
  const ids=tests.getRange('A6:A51').values.flat();
  for(const row of ui.tests){
    const n=ids.indexOf(row.id);assert.ok(n>=0,row.id);
    tests.getRange(`D${n+6}`).values=[[row.duration_ms]];
  }
  indicators.getRange('B17').formulas=[['=SMALL(Carga!B6:B205,ROUNDUP(COUNT(Carga!B6:B205)*0.95,0))']];
  indicators.getRange('A37').values=[['P95 calculado a partir das 200 amostras: posto mais próximo (95%).']];
  indicators.getRange('D27').values=[['Período completo, com observações regulares; ver Apêndice B.']];
  wb.recalculate();
  const value=indicators.getRange('B17').values[0][0];assert.ok(Math.abs(value-162.7)<0.0001,String(value));
  assert.equal(indicators.getRange('B16').values[0][0],46);
  assert.equal(indicators.getRange('B9').values[0][0],'Não medido');
  assert.equal(indicators.getRange('B10').values[0][0],'Não medido');
  const carga=wb.worksheets.getItem('Carga');
  const old=carga.getRange('B6:B205').values;
  carga.getRange('B6:B205').values=old.map(([v])=>[v+100]);
  assert.ok(Math.abs(indicators.getRange('B17').values[0][0]-262.7)<0.0001);
  carga.getRange('B6:B205').values=old;
  indicators.getRange('B27:B28').values=[[1000],[0]];
  assert.equal(indicators.getRange('B9').values[0][0],1);
  indicators.getRange('B27:B28').values=[[null],[null]];
  indicators.getRange('B29:B30').values=[[10],[9]];
  assert.equal(indicators.getRange('B10').values[0][0],0.9);
  indicators.getRange('B29:B30').values=[[null],[null]];
  wb.recalculate();
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20}})).ndjson);
  for(const [sheetName,range] of [['Indicadores','A1:F18'],['Indicadores','A22:F37'],['Testes','A40:F51'],['Carga','A1:D14']]){
    const blob=await wb.render({sheetName,range,scale:1.3,format:'png'});
    await fs.writeFile(path.join(out,`${sheetName}_${range.split(':')[0]}.png`),new Uint8Array(await blob.arrayBuffer()));
  }
  const output=await SpreadsheetFile.exportXlsx(wb);
  await output.save(path.join(out,'4992220_Metricas_Qualidade.xlsx'));
  console.log('Planilha revisada, recálculo e casos de entrada conferidos.');
}
