export function createGame(mode = 'classic', random = Math.random) {
  const gap = mode === 'chill' ? 194 : 160;
  return { y: 245, velocity: 0, x: 215, radius: 15, pipes: [], score: 0,
    distance: 0, elapsed: 0, alive: true, gap, random, speed: mode === 'chill' ? 155 : 185 };
}
export function flap(state) { if (state.alive) state.velocity = -310; }
export function step(state, dt) {
  if (!state.alive) return;
  state.elapsed += dt;
  state.velocity += 850 * dt;
  state.y += state.velocity * dt;
  const dx = state.speed * dt;
  state.distance += dx;
  if (!state.pipes.length || state.pipes.at(-1).x <= 610) {
    // Keep successive openings reachable at the fixed flight speed.
    const previous = state.pipes.at(-1)?.center ?? 245;
    const center = Math.max(145, Math.min(355, previous + (state.random() - .5) * 140));
    state.pipes.push({ x: 940, center, scored: false });
  }
  for (const pipe of state.pipes) {
    pipe.x -= dx;
    const overlaps = state.x + state.radius > pipe.x - 5 && state.x - state.radius < pipe.x + 77;
    if (overlaps && (state.y - state.radius < pipe.center - state.gap / 2 || state.y + state.radius > pipe.center + state.gap / 2)) state.alive = false;
    if (!pipe.scored && pipe.x + 77 < state.x - state.radius) { pipe.scored = true; state.score++; }
  }
  state.pipes = state.pipes.filter(pipe => pipe.x > -90);
  if (state.y - state.radius <= 0 || state.y + state.radius >= 492) state.alive = false;
}
