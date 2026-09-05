import assert from 'node:assert/strict';
import { createGame, flap, step } from './physics.mjs';
const idle=createGame();for(let i=0;i<300;i++)step(idle,1/120);assert.equal(idle.alive,false,'falling hits the ground');
const hit=createGame();hit.pipes=[{x:210,center:400,scored:false}];step(hit,1/120);assert.equal(hit.alive,false,'pipe collision');
const safe=createGame();safe.pipes=[{x:210,center:245,scored:false}];step(safe,1/120);assert.equal(safe.alive,true,'gap stays open');
function fly(hz) {const s=createGame('classic',()=>.5);for(let i=0;i<hz*30&&s.alive;i++){if(s.y>245&&s.velocity>0)flap(s);step(s,1/hz);}return s;}
for(const hz of [60,120,144]){const s=fly(hz);assert(s.alive,`survive at ${hz}Hz`);assert(s.score>=12,`score at ${hz}Hz`);}
assert.equal(fly(60).score,fly(120).score,'score independent of frame rate');
assert(createGame('chill').gap>createGame().gap);
console.log('Flight checks passed: collisions, gaps, scoring, 30-second playable runs at 60/120/144Hz.');
