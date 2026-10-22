import fs from 'node:fs/promises';

export async function populateLecture(presentation,root) {
  const content=JSON.parse(await fs.readFile(`${root}/docs/presentation/lecture_content.json`,'utf8'));
  presentation.slides.keep([]);
  const colors=['#1A638D','#BE5D36','#5B7486'];
  const text=(sl,value,x,y,w,h,size=28,bold=false,color='#1B2933')=>{
    const obj=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
    obj.text=value;obj.text.style={typeface:'Aptos',fontSize:size,bold,color};obj.text.insets=0;return obj;
  };
  for(const spec of content.slides) {
    const sl=presentation.slides.add();sl.setViewportSize(1280,720);sl.background.fill='#FFFFFF';
    if(spec.kind==='cover'){
      text(sl,spec.title,70,110,1140,100,64,true,'#124F78');
      text(sl,spec.body,70,270,1120,185,35);
      text(sl,spec.caption,70,560,1120,100,24);
    } else {
      text(sl,spec.section,62,24,1110,35,21,false,'#4E6879');
      text(sl,`${spec.slide}. ${spec.title}`,62,82,1155,98,42,true,'#124F78');
      if(spec.kind==='chart'){
        text(sl,spec.body,62,196,465,430,26);
        const ch=spec.chart;
        const chart=sl.charts.add(ch.type,{position:{left:555,top:185,width:665,height:405},categories:ch.categories,
          series:ch.series.map((s,i)=>({name:s.name,values:s.values,fill:colors[i],line:{fill:colors[i],width:3},marker:{symbol:'circle',size:6,fill:colors[i]}})),
          hasLegend:ch.series.length>1,legend:{position:'bottom',textStyle:{fontSize:22,fill:'#1B2933'}},
          lineOptions:{smooth:false},barOptions:{direction:'column',grouping:'clustered',gapWidth:100},
          chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
          xAxis:{textStyle:{fontSize:22,fill:'#1B2933'},line:{fill:'#8294A0',width:1},majorGridlines:null},
          yAxis:{title:{text:ch.yTitle,textStyle:{fontSize:22,fill:'#1B2933'}},textStyle:{fontSize:22,fill:'#1B2933'},min:ch.min,max:ch.max,numberFormatCode:ch.format??'0',...(ch.majorUnit?{majorUnit:ch.majorUnit}:{}),majorGridlines:{fill:'#D8E1E8',width:1}},
          dataLabels:{showValue:ch.type==='bar',position:'outEnd',numberFormatCode:ch.format??'0',textStyle:{fontSize:22,bold:true,fill:'#173C55'}}});
        for(const style of [chart.legend.textStyle,chart.dataLabels.textStyle,chart.xAxis.textStyle,chart.yAxis.textStyle,chart.yAxis.title?.textStyle])if(style)style.typeface='Arial';
      }else if(spec.kind==='table'){
        const paragraphs=spec.body.split('\n');
        const lines=paragraphs.reduce((n,line)=>n+(line?Math.ceil(line.length/82):1),0);
        const introHeight=Math.max(95,lines*34+16);
        text(sl,spec.body,62,190,1150,introHeight,27);
        const top=190+introHeight+12;
        const table=sl.tables.add({rows:spec.table.length,columns:spec.table[0].length,left:62,top,width:1150,height:Math.min(630-top,spec.table.length*57),values:spec.table});
        for(let r=0;r<spec.table.length;r++)for(let c=0;c<spec.table[r].length;c++){
          const cell=table.getCell(r,c);cell.fill=r===0?'#E4EDF4':(r%2?'#FFFFFF':'#F3F6F8');
          cell.text.style={typeface:'Aptos',fontSize:24,bold:r===0,color:'#1B2933'};
        }
      }else text(sl,spec.body,62,198,1150,400,30);
      text(sl,spec.caption,62,646,1150,55,21,false,'#405C6C');
    }
    sl.speakerNotes.text=spec.notes;
  }
  return {slides:content.slides.length,nativeChartSlides:content.slides.filter(s=>s.chart).map(s=>s.slide),nativeTableSlides:content.slides.filter(s=>s.table).map(s=>s.slide),bodyFont:'Aptos',chartFont:'Arial'};
}
