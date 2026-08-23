// THE ARCHITECTURE — neural map generator (browser-eval'd by run_script; no imports).
// Usage: const {svg,data} = buildMap(JSON.parse(sourceJson));
// Source shape: {current, nodes:{KEY:{x,y,r,name,sub,flag}}, edges:[[s,t,grade,label],...]}
// Grades: A solid amber 3.0 · B solid faint 2.2 · C dashed 9,7 red · O dotted 2,7 faint.
function buildMap(SRC){
  const BG="#141210",INK="#e9e3d6",SOFT="#b9b0a0",FAINT="#8a8172",AMBER="#d98a2b",AMBER_HI="#e9a94e",RED="#c0562f",RULE="#3a352d";
  const GRADE={A:{stroke:AMBER,width:3.0,dash:null},B:{stroke:FAINT,width:2.2,dash:null},C:{stroke:RED,width:2.0,dash:"9,7"},O:{stroke:FAINT,width:2.0,dash:"2,7"}};
  const NODES=SRC.nodes, EDGES=SRC.edges;
  const esc=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const wrap=(t,w)=>{if(!t)return[];const out=[];let cur="";for(const word of t.split(/\s+/)){const trial=(cur+" "+word).trim();if(trial.length<=w)cur=trial;else{if(cur)out.push(cur);cur=word;}}if(cur)out.push(cur);return out;};
  const keys=Object.keys(NODES);
  const xs=keys.map(k=>NODES[k].x), ys=keys.map(k=>NODES[k].y);
  const VB_X=Math.min(...xs)-210, VB_Y=Math.min(...ys)-150, VB_W=(Math.max(...xs)-Math.min(...xs))+420, VB_H=(Math.max(...ys)-Math.min(...ys))+300;
  function trim(x1,y1,r1,x2,y2,r2,extra=4){const dx=x2-x1,dy=y2-y1,d=Math.hypot(dx,dy)||1,ux=dx/d,uy=dy/d;return [x1+ux*(r1+extra),y1+uy*(r1+extra),x2-ux*(r2+extra),y2-uy*(r2+extra)];}
  function parallelOffsets(pairs){const seen={};pairs.forEach((p,i)=>{const k=[p[0],p[1]].sort().join("|");(seen[k]=seen[k]||[]).push(i);});const off=pairs.map(()=>0);for(const k in seen){const idxs=seen[k];if(idxs.length<2)continue;const spread=34,start=-spread*(idxs.length-1)/2;idxs.forEach((i,n)=>off[i]=start+n*spread);}return off;}
  function obstacles(){const obs=[];for(const k of keys){const n=NODES[k];obs.push({x:n.x,y:n.y,w:2*n.r+10,h:2*n.r+10});const lines=wrap(n.sub,30);if(lines.length){const w=Math.max(...lines.map(l=>l.length))*5.6+14,h=lines.length*14+8;obs.push({x:n.x,y:n.y+n.r+19+(lines.length-1)*7-4,w,h});}}return obs;}
  function relax(labels,iterations=400){const obs=obstacles();
    const ov=(a,b,padx=9,pady=7.5)=>{const dx=b.x-a.x,dy=b.y-a.y,ox=(a.w+b.w)/2+padx-Math.abs(dx),oy=(a.h+b.h)/2+pady-Math.abs(dy);return (ox>0&&oy>0)?[dx,dy,ox,oy]:null;};
    for(let it=0;it<iterations;it++){let moved=false;const cool=1-(it/iterations)*0.55;
      for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j],h=ov(a,b);if(!h)continue;const[dx,dy,ox,oy]=h;
        if(oy<=ox){const push=(oy*0.62+1)*cool,s=dy>=0?1:-1;a.y-=push*s;b.y+=push*s;}else{const push=(ox*0.62+1)*cool,s=dx>=0?1:-1;a.x-=push*s;b.x+=push*s;}moved=true;}
      for(const L of labels)for(const O of obs){const h=ov(L,O,9,8);if(!h)continue;const[dx,dy,ox,oy]=h;
        if(oy<=ox){const s=dy>=0?1:-1;L.y-=(oy*1.15+1.2)*cool*s;}else{const s=dx>=0?1:-1;L.x-=(ox*1.15+1.2)*cool*s;}moved=true;}
      for(const L of labels){L.x+=(L.ax-L.x)*0.022;L.y+=(L.ay-L.y)*0.022;}
      if(!moved&&it>40)break;}
    return labels;}
  const offs=parallelOffsets(EDGES);
  const edgeSvg=[],labels=[];
  EDGES.forEach((e,i)=>{const[s,t,g,lab]=e;const A=NODES[s],B=NODES[t];
    const[sx,sy,ex,ey]=trim(A.x,A.y,A.r,B.x,B.y,B.r);
    const dx=ex-sx,dy=ey-sy,d=Math.hypot(dx,dy)||1,px=-dy/d,py=dx/d,off=offs[i];
    const mx=(sx+ex)/2+px*off,my=(sy+ey)/2+py*off;const st=GRADE[g];
    const dash=st.dash?` stroke-dasharray="${st.dash}"`:"";
    const path=Math.abs(off)>0.01?`M ${sx.toFixed(1)} ${sy.toFixed(1)} Q ${mx.toFixed(1)} ${my.toFixed(1)} ${ex.toFixed(1)} ${ey.toFixed(1)}`:`M ${sx.toFixed(1)} ${sy.toFixed(1)} L ${ex.toFixed(1)} ${ey.toFixed(1)}`;
    edgeSvg.push(`<path class="nm-edge" data-i="${i}" data-s="${s}" data-t="${t}" data-g="${g}" d="${path}" fill="none" stroke="${st.stroke}" stroke-width="${st.width}" stroke-linecap="round"${dash} marker-end="url(#nm-ar-${g})" opacity="${g==="A"?0.95:0.8}"/>`);
    const lx=(sx+ex)/2+px*off*0.5, ly=(sy+ey)/2+py*off*0.5;
    labels.push({x:lx,y:ly,ax:lx,ay:ly,w:lab.length*5.9+20,h:20,text:lab,grade:g,i,s,t});});
  relax(labels);
  const labSvg=labels.map(L=>{const colour=L.grade==="A"?AMBER_HI:(L.grade==="C"?RED:SOFT);
    const drift=Math.hypot(L.x-L.ax,L.y-L.ay);
    const leader=drift>16?`<line x1="${L.ax.toFixed(1)}" y1="${L.ay.toFixed(1)}" x2="${L.x.toFixed(1)}" y2="${L.y.toFixed(1)}" stroke="${RULE}" stroke-width="0.9" stroke-dasharray="1,4" opacity="0.75"/>`:"";
    return `<g class="nm-lab" data-i="${L.i}" data-s="${L.s}" data-t="${L.t}">${leader}<rect x="${(L.x-L.w/2).toFixed(1)}" y="${(L.y-10).toFixed(1)}" width="${L.w.toFixed(1)}" height="20" rx="10" fill="${BG}" stroke="${RULE}" stroke-width="1" opacity="0.94"/><text x="${L.x.toFixed(1)}" y="${(L.y+4).toFixed(1)}" text-anchor="middle" font-size="11.5" fill="${colour}" letter-spacing="0.02em">${esc(L.text)}</text></g>`;}).join("\n");
  const nodeSvg=keys.map(k=>{const n=NODES[k];
    const core=n.core===true, isNew=n.flag==="new", isUpd=n.flag==="updated";
    const ring=isNew?AMBER_HI:(isUpd?AMBER:RULE), ringW=(isNew||isUpd)?2.6:1.6, fill=core?AMBER:BG;
    let p=`<g class="nm-node${core?" core":""}" data-key="${k}" tabindex="0" role="button" aria-label="${esc(n.name)} — open dossier"><title>${esc(n.name)}</title>`;
    if(isNew) p+=`<circle cx="${n.x}" cy="${n.y}" r="${n.r+9}" fill="none" stroke="${AMBER_HI}" stroke-width="1" stroke-dasharray="3,5" opacity="0.55"/>`;
    p+=`<circle class="nm-hit" cx="${n.x}" cy="${n.y}" r="${n.r+14}" fill="transparent"/>`;
    p+=`<circle class="nm-disc" cx="${n.x}" cy="${n.y}" r="${n.r}" fill="${fill}" stroke="${ring}" stroke-width="${ringW}"/>`;
    const nl=wrap(n.name,9), fs=core?14:12, sy0=n.y-(nl.length-1)*(fs*0.58);
    nl.forEach((line,li)=>{p+=`<text class="nm-name" x="${n.x}" y="${(sy0+li*(fs+2)+fs*0.35).toFixed(1)}" text-anchor="middle" font-size="${fs}" font-weight="600" letter-spacing="0.09em" fill="${core?BG:INK}">${esc(line)}</text>`;});
    wrap(n.sub,30).forEach((line,li)=>{const ty=n.y+n.r+19+li*14, bw=line.length*5.6+12;
      p+=`<rect x="${(n.x-bw/2).toFixed(1)}" y="${(ty-10).toFixed(1)}" width="${bw.toFixed(1)}" height="14" fill="${BG}" opacity="0.92"/><text class="nm-sub" x="${n.x}" y="${ty}" text-anchor="middle" font-size="11" fill="${FAINT}">${esc(line)}</text>`;});
    return p+"</g>";}).join("\n");
  const DEFS=`<defs>${["A","B","C","O"].map(g=>`<marker id="nm-ar-${g}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0.5,0.8 L7.4,4 L0.5,7.2 z" fill="${GRADE[g].stroke}"/></marker>`).join("")}</defs>`;
  const svg=`<svg class="nm-svg" viewBox="${VB_X} ${VB_Y} ${VB_W} ${VB_H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Neural map: ${keys.length} nodes, ${EDGES.length} edges, graded by evidence">\n${DEFS}\n<g class="nm-edges">\n${edgeSvg.join("\n")}\n</g>\n<g class="nm-labs">\n${labSvg}\n</g>\n<g class="nm-nodes">\n${nodeSvg}\n</g>\n</svg>`;
  const data={current:SRC.current,nodes:{},edges:EDGES.map(([s,t,g,l])=>({s,t,g,l}))};
  for(const k of keys){data.nodes[k]={name:NODES[k].name,sub:NODES[k].sub,flag:NODES[k].flag||""};}
  return {svg,data};
}
