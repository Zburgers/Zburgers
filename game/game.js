import { createGame, flap, step } from './physics.mjs';

const $ = id => document.getElementById(id);
const canvas = $('game'), ctx = canvas.getContext('2d');
const bird = new Image(); bird.src = './bird.svg';
let state = createGame(), phase = 'ready', last = 0, accumulator = 0, sceneTime = 0;
let sound = false, audio, particles = [], best = 0;
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
function loadBest() {
  try { best = Math.max(0, Number(localStorage.getItem(`flappy-commit-${$('difficulty').value}`)) || 0); } catch { best = 0; }
  $('best').textContent = String(best).padStart(2, '0');
}
loadBest();
function tone(frequency, duration = .07) {
  if (!sound) return;
  try {
    audio ??= new (window.AudioContext || window.webkitAudioContext)();
    if (audio.state === 'suspended') audio.resume().catch(() => {});
    const oscillator = audio.createOscillator(), gain = audio.createGain();
    oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(frequency, audio.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(frequency * .65, audio.currentTime + duration);
    gain.gain.setValueAtTime(.055, audio.currentTime);
    gain.gain.exponentialRampToValueAtTime(.001, audio.currentTime + duration);
    oscillator.connect(gain).connect(audio.destination); oscillator.start(); oscillator.stop(audio.currentTime + duration);
  } catch { sound = false; $('sound').textContent = 'Sound unavailable'; $('sound').setAttribute('aria-pressed', 'false'); }
}
function overlay(message, hint, label) {
  $('message').textContent = message; $('hint').textContent = hint; $('start').textContent = label; $('overlay').hidden = false;
}
function start() {
  state = createGame($('difficulty').value); particles = []; accumulator = 0;
  phase = 'playing'; $('overlay').hidden = true; $('difficulty').disabled = true;
  $('score').textContent = '00'; $('status').textContent = 'In flight · P / Esc to pause';
  $('pause').textContent = 'Pause'; $('pause').setAttribute('aria-label', 'Pause game');
  canvas.focus({ preventScroll: true }); flap(state); tone(620);
}
function pause() {
  if (phase === 'playing') {
    phase = 'paused'; overlay('Catch your breath.', 'Your flight is right where you left it.', 'Resume flight');
    $('pause').textContent = 'Resume'; $('pause').setAttribute('aria-label', 'Resume game'); $('status').textContent = 'Flight paused';
  } else if (phase === 'paused') {
    phase = 'playing'; accumulator = 0; $('overlay').hidden = true;
    $('pause').textContent = 'Pause'; $('pause').setAttribute('aria-label', 'Pause game'); $('status').textContent = 'In flight · P / Esc to pause'; canvas.focus({ preventScroll: true });
  }
}
function input() {
  if (phase === 'paused') return pause();
  if (phase !== 'playing') return start();
  flap(state); tone(620);
  if (!reducedMotion) for (let i = 0; i < 4; i++) particles.push({x:state.x-20,y:state.y+10,vx:-50-Math.random()*70,vy:Math.random()*50,life:.5});
}
$('start').onclick = input;
canvas.addEventListener('pointerdown', event => { event.preventDefault(); input(); });
window.addEventListener('keydown', event => {
  if (event.target instanceof HTMLSelectElement || (event.target instanceof HTMLButtonElement && [' ', 'Enter'].includes(event.key))) return;
  if (event.repeat) return;
  if ([' ', 'ArrowUp'].includes(event.key)) { event.preventDefault(); input(); }
  if (['p', 'P', 'Escape'].includes(event.key)) { event.preventDefault(); pause(); }
  if (['r', 'R'].includes(event.key)) start();
});
$('pause').onclick = pause;
$('sound').onclick = () => { sound = !sound; $('sound').textContent = sound ? 'Sound on' : 'Sound off'; $('sound').setAttribute('aria-pressed', String(sound)); tone(500); };
$('difficulty').onchange = () => { loadBest(); state = createGame($('difficulty').value); phase = 'ready'; $('score').textContent = '00'; overlay('The sky is yours.', 'Space, click or tap to spread your wings.', 'Take flight'); };
document.addEventListener('visibilitychange', () => { if (document.hidden && phase === 'playing') pause(); });
window.addEventListener('blur', () => { if (phase === 'playing') pause(); });

function rect(x,y,w,h,color,r=0) { ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill(); }
function cloud(x,y,scale) {
  ctx.save(); ctx.translate(x,y); ctx.scale(scale,scale); ctx.fillStyle='#8ca4b520';
  ctx.beginPath();ctx.ellipse(0,0,60,13,0,0,7);ctx.ellipse(-24,-9,27,16,0,0,7);ctx.ellipse(12,-16,32,22,0,0,7);ctx.fill();ctx.restore();
}
function pipeArt(pipe) {
  const top = pipe.center-state.gap/2, bottom = pipe.center+state.gap/2;
  const gradient=ctx.createLinearGradient(pipe.x,0,pipe.x+72,0);
  gradient.addColorStop(0,'#395f66');gradient.addColorStop(.2,'#659184');gradient.addColorStop(.7,'#416e70');gradient.addColorStop(1,'#294c58');
  rect(pipe.x,0,72,top,gradient);rect(pipe.x,bottom,72,492-bottom,gradient);
  rect(pipe.x+7,0,3,top,'#a6c5a54d');rect(pipe.x+7,bottom,3,492-bottom,'#a6c5a54d');
  for (const y of [top-23,bottom]) { rect(pipe.x-5,y,82,23,'#233f4c',4);rect(pipe.x-3,y+2,78,16,'#709a89',3);rect(pipe.x,y+3,72,3,'#c4d3a0'); }
  for(let y=30;y<492;y+=45) if(y<top-28||y>bottom+30){rect(pipe.x+53,y,9,4,'#183c4a');rect(pipe.x+18,y,6,4,'#a2b79155');}
  ctx.fillStyle='#cee7bc';for(const y of [top-12,bottom+10]){ctx.beginPath();ctx.arc(pipe.x+8,y,2,0,7);ctx.arc(pipe.x+65,y,2,0,7);ctx.fill();}
}
function draw(dt) {
  const sky=ctx.createLinearGradient(0,0,0,520);sky.addColorStop(0,'#142238');sky.addColorStop(.55,'#33465f');sky.addColorStop(1,'#987b7d');rect(0,0,900,520,sky);
  for(let i=0;i<65;i++){const sx=(i*137.3)%900,sy=(i*73.7)%290;ctx.globalAlpha=.3+.4*Math.sin(i+sceneTime*.4);rect(sx,sy,i%6===0?2:1,i%6===0?2:1,'#ffe6bf');}ctx.globalAlpha=1;
  const glow=ctx.createRadialGradient(724,101,5,724,101,100);glow.addColorStop(0,'#f9dcae44');glow.addColorStop(1,'#f9dcae00');rect(624,1,200,200,glow);
  ctx.fillStyle='#f0d7b2';ctx.beginPath();ctx.arc(724,101,33,0,7);ctx.fill();ctx.fillStyle='#e2bf9340';ctx.beginPath();ctx.arc(710,93,8,0,7);ctx.arc(733,116,6,0,7);ctx.fill();
  for(let i=0;i<4;i++) cloud(((i*310-sceneTime*9)%1250+1250)%1250-120,85+i*40,.6+i*.22);
  for(let layer=0;layer<3;layer++) {
    const width=layer===0?90:55, speed=(layer+1)*.1,base=layer===0?400:492;
    const offset=state.distance*speed;
    for(let i=-2;i<24;i++){const bx=i*width-offset%(width*12),height=50+((i+48)*79+layer*47)%150;rect(bx,base-height,width-4,height,['#25394d','#23364a','#1d2b3d'][layer]);
      if(layer===2) for(let row=0;row<height-12;row+=17)for(let col=0;col<3;col++)if((i+row+col)%3!==0)rect(bx+9+col*13,base-height+12+row,4,6,'#eac49250');
    }
  }
  state.pipes.forEach(pipeArt);
  rect(0,492,900,28,'#182838');rect(0,492,900,3,'#b8c397');rect(0,496,900,5,'#557476');
  for(let i=-1;i<35;i++)rect(i*30-state.distance%30,505,18,3,'#324657');
  particles=particles.filter(p=>p.life>0);for(const p of particles){p.x+=p.vx*dt;p.y+=p.vy*dt;p.life-=dt;ctx.globalAlpha=Math.max(0,p.life*1.8);rect(p.x,p.y,3,3,'#f4d498');}ctx.globalAlpha=1;
  const y=phase==='ready'?245+Math.sin(sceneTime*3)*7:state.y;
  ctx.save();ctx.translate(state.x,y);ctx.rotate(phase==='playing'?Math.max(-.4,Math.min(.9,state.velocity/600)):-.1);
  if(bird.complete&&bird.naturalWidth) ctx.drawImage(bird,-31,-26,66,55);ctx.restore();
  // A vignette frames the scene without obscuring the obstacle edges.
  const vignette=ctx.createRadialGradient(450,245,170,450,245,580);vignette.addColorStop(0,'#07122200');vignette.addColorStop(1,'#07122266');rect(0,0,900,520,vignette);
}
function frame(timestamp) {
  const dt=Math.min((timestamp-last)/1000||0, .1);last=timestamp;
  if(phase==='playing'||(!reducedMotion&&phase==='ready'))sceneTime+=dt;
  if(phase==='playing') {
    accumulator+=dt;
    while(accumulator>=1/120&&state.alive) {step(state,1/120);accumulator-=1/120;}
    const shown=Number($('score').textContent);if(state.score!==shown){$('score').textContent=String(state.score).padStart(2,'0');tone(920,.13);}
    if(!state.alive){phase='over';$('difficulty').disabled=false;best=Math.max(best,state.score);
      try{localStorage.setItem(`flappy-commit-${$('difficulty').value}`,String(best));}catch{}
      $('best').textContent=String(best).padStart(2,'0');tone(190,.2);overlay('A beautiful crash.',`${state.score} gates cleared · personal best ${best}`,'Fly again');$('status').textContent=`Flight complete. Score ${state.score}. Ready to try again.`;
    }
  }
  draw(phase==='playing'?dt:0);requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
