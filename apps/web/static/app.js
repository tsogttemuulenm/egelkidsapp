(() => {
  const $ = (id) => document.getElementById(id);

  const LS_KEY = "egel_kids_progress_v1";

  const state = {
    op: "add",
    mode: "play", // play | learn
    stage: 0,
    unit: 56,
    show_grid: true,
    show_marks: true,
    color_mode: 1,
    align: "right",
    sub_pos: "top",
    show_remainder: true,

    // current problem
    a: 12,
    b: 8,
    correct: null,
    correct_q: null,
    correct_r: 0,

    // game progress
    level: { add: 1, sub: 1, mul: 1, div: 1 },
    stars: 0,
    streak: 0,
    allowRemainder: false,
  };

  const tabs = Array.from(document.querySelectorAll(".tab"));
  const svgHost = $("svgHost");
  const toast = $("toast");
  const hintText = $("hintText");

  function loadProgress(){
    try{
      const raw = localStorage.getItem(LS_KEY);
      if(!raw) return;
      const p = JSON.parse(raw);
      if(p && typeof p === "object"){
        state.level = p.level || state.level;
        state.stars = Number(p.stars || 0);
        state.streak = Number(p.streak || 0);
      }
    }catch(_){}
  }
  function saveProgress(){
    const p = { level: state.level, stars: state.stars, streak: state.streak };
    localStorage.setItem(LS_KEY, JSON.stringify(p));
  }

  function setToast(msg, kind="info"){
    toast.className = "toast " + kind;
    toast.textContent = msg;
  }

  function celebrate(){
    // light confetti without canvas
    const n = 22;
    for(let i=0;i<n;i++){
      const d = document.createElement("div");
      d.className = "confetti";
      d.style.left = (Math.random()*100) + "vw";
      d.style.background = `hsl(${Math.floor(Math.random()*360)}, 90%, 60%)`;
      d.style.animationDuration = (900 + Math.random()*900) + "ms";
      document.body.appendChild(d);
      setTimeout(()=>d.remove(), 2000);
    }
  }

  function setMode(mode){
    state.mode = mode;
    $("modePlay").classList.toggle("active", mode==="play");
    $("modeLearn").classList.toggle("active", mode==="learn");
    $("learnPanel").style.display = (mode==="learn") ? "block" : "none";
    // in play mode: start at stage 0
    state.stage = (mode==="play") ? 0 : Number($("stage").value||3);
    $("tracePanel").style.display = "none";
    setToast(mode==="play" ? "Тоглоом эхэллээ! 💪" : "Суралцах горим ✅", "info");
    refreshUI();
    render();
  }

  function setOp(op){
    state.op = op;
    tabs.forEach(b => b.classList.toggle("active", b.dataset.op === op));
    // show div-only blocks
    document.querySelectorAll(".divOnly").forEach(el => {
      el.style.display = (op === "div") ? "" : "none";
    });

    // update learn mode b min
    if (op === "div") {
      $("b").min = "1";
      if (Number($("b").value) === 0) $("b").value = "56";
    } else {
      $("b").min = "0";
    }

    // new problem when switching in play mode
    state.stage = (state.mode==="play") ? 0 : state.stage;
    if(state.mode==="play"){
      newProblem();
    }else{
      // learn mode uses inputs
      state.a = Number($("a").value||0);
      state.b = Number($("b").value||0);
      computeCorrect();
      refreshUI();
      render();
    }
  }

  function clamp(n, lo, hi){ return Math.max(lo, Math.min(hi, n)); }

  function pow10(k){ return Math.pow(10, k); }

  function randNDigits(d, allowZero=true){
    // d=1 -> [0..9] (or [1..9] if allowZero=false)
    // d>=2 -> [10^(d-1) .. 10^d-1]
    if(d <= 1){
      return randInt(allowZero ? 0 : 1, 9);
    }
    const lo = pow10(d-1);
    const hi = pow10(d) - 1;
    return randInt(lo, hi);
  }

  function digitsForLevel(stepEvery2Levels, level, minDigits, maxDigits){
    // Example: every 2 levels increase digits by 1
    const d = minDigits + Math.floor((Math.max(1, level) - 1) / stepEvery2Levels);
    return clamp(d, minDigits, maxDigits);
  }

  // Level progression rule (as requested):
  // Level increases => number of digits in the problem data increases.
  function digitSpec(op, level){
    if(op === "add" || op === "sub"){
      // L1-2: 1 digit, L3-4: 2 digits, ... up to 6 digits
      const d = digitsForLevel(2, level, 1, 6);
      return {aDigits: d, bDigits: d};
    }
    if(op === "mul"){
      // L1-2: 1 digit, L3-4: 2 digits, ... up to 5 digits
      const d = digitsForLevel(2, level, 1, 5);
      return {aDigits: d, bDigits: d};
    }
    // div
    // Divisor grows a bit slower; quotient grows with level; dividend digits grows automatically.
    const divDigits = digitsForLevel(3, level, 1, 4);  // 1..4 digits
    const qDigits   = digitsForLevel(2, level, 1, 4);  // 1..4 digits
    return {divisorDigits: divDigits, quotientDigits: qDigits};
  }


  function randInt(lo, hi){
    return Math.floor(lo + Math.random()*(hi-lo+1));
  }

  function makeDivProblem(level){
    const spec = digitSpec("div", level);
    const dDigits = spec.divisorDigits;
    const qDigits = spec.quotientDigits;

    // divisor: 1-digit -> 2..9, else N-digits
    const divisor = (dDigits === 1)
      ? randInt(2, 9)
      : randNDigits(dDigits, false);

    // quotient: N digits (avoid 0)
    const q = (qDigits === 1)
      ? randInt(1, 9)
      : randNDigits(qDigits, false);

    let r = 0;
    if(state.allowRemainder && level >= 4){
      r = randInt(0, Math.max(0, divisor-1));
    }
    const dividend = divisor*q + r;
    return {a: dividend, b: divisor, q, r};
  }

  function newProblem(){
    const lvl = state.level[state.op] || 1;

    if(state.op==="div"){
      const p = makeDivProblem(lvl);
      state.a = p.a; state.b = p.b;
      state.correct_q = p.q; state.correct_r = p.r;
      state.correct = null;
    } else if(state.op==="add") {
      const spec = digitSpec("add", lvl);
      state.a = randNDigits(spec.aDigits, true);
      state.b = randNDigits(spec.bDigits, true);
    } else if(state.op==="sub") {
      const spec = digitSpec("sub", lvl);
      const x = randNDigits(spec.aDigits, true);
      const y = randNDigits(spec.bDigits, true);
      state.a = Math.max(x, y);
      state.b = Math.min(x, y);
    } else if(state.op==="mul") {
      const spec = digitSpec("mul", lvl);
      state.a = randNDigits(spec.aDigits, true);
      state.b = randNDigits(spec.bDigits, true);
    }

    computeCorrect();
    state.stage = 0;
    $("tracePanel").style.display = "none";
    setToast("Шинэ бодлого! 😊", "info");
    refreshUI();
    render();
    focusAnswer();
  }

  function computeCorrect(){
    const a = Number(state.a||0);
    const b = Number(state.b||0);
    if(state.op==="add"){
      state.correct = a + b;
    } else if(state.op==="sub"){
      state.correct = a - b;
    } else if(state.op==="mul"){
      state.correct = a * b;
    } else if(state.op==="div"){
      if(b<=0){ state.correct_q=0; state.correct_r=0; return; }
      state.correct_q = Math.floor(a / b);
      state.correct_r = a % b;
    }
  }

  function refreshUI(){
    $("stars").textContent = String(state.stars);
    $("streak").textContent = String(state.streak);
    const lvl = state.level[state.op] || 1;
    $("levelBadge").textContent = `Level ${lvl}`;

    // expression
    const opSym = state.op==="add" ? "+" : state.op==="sub" ? "−" : state.op==="mul" ? "×" : "÷";
    $("expr").textContent = `${state.a} ${opSym} ${state.b} = ?`;

    // div toggle
    if(state.op==="div"){
      $("ansBoxSimple").style.display = "none";
      $("ansBoxDiv").style.display = "block";
      $("useRemainder").checked = state.allowRemainder;
    } else {
      $("ansBoxSimple").style.display = "block";
      $("ansBoxDiv").style.display = "none";
    }

    // learn panel mirrors state
    $("unitVal").textContent = String(state.unit);
    hintText.textContent = (state.mode==="play")
      ? "💡 “Алхам ахиулах” дарж дүрслэлийг бага багаар хар!"
      : "Тохируулга хийгээд “Зурах” дар.";

    // clear inputs in play mode
    if(state.mode==="play"){
      $("ans").value = "";
      if(state.op==="div"){
        $("q").value = "";
        $("r").value = "0";
      }
    }
  }

  function focusAnswer(){
    if(state.op==="div") $("q").focus();
    else $("ans").focus();
  }

  function getRenderParams(){
    const params = new URLSearchParams();
    params.set("op", state.op);
    params.set("a", String(state.a));
    params.set("b", String(state.b));
    params.set("unit", String(state.unit));
    params.set("stage", String(state.stage));
    params.set("show_grid", String(state.show_grid));
    params.set("show_marks", String(state.show_marks));
    params.set("color_mode", String(state.color_mode));
    if(state.op==="div"){
      params.set("align", state.align);
      params.set("sub_pos", state.sub_pos);
      params.set("show_remainder", String(state.show_remainder));
    }
    return params;
  }

  async function render(){
    const params = getRenderParams();
    const url = `/api/render?${params.toString()}`;
    svgHost.innerHTML = `<div class="placeholder">⏳ Зурж байна…</div>`;
    try{
      const res = await fetch(url);
      if(!res.ok) throw new Error(await res.text());
      const svg = await res.text();
      svgHost.innerHTML = svg;
    }catch(err){
      svgHost.innerHTML = `<div class="placeholder">⚠️ Алдаа: ${String(err)}</div>`;
    }
  }

  async function showTrace(){
    const params = new URLSearchParams();
    params.set("op", state.op);
    params.set("a", String(state.a));
    params.set("b", String(state.b));
    const url = `/api/trace?${params.toString()}`;
    try{
      const res = await fetch(url);
      if(!res.ok) throw new Error(await res.text());
      const data = await res.json();
      $("tracePanel").style.display = "block";
      $("traceBox").textContent = JSON.stringify(data, null, 2);
    }catch(err){
      setToast("Тайлбар авч чадсангүй 😅", "bad");
    }
  }

  function checkAnswer(){
    if(state.op==="div"){
      const uq = Number(($("q").value||"").trim());
      const ur = Number(($("r").value||"0").trim());
      const ok = (uq === state.correct_q) && (ur === state.correct_r);
      onCheckResult(ok, `Зөв: q=${state.correct_q}, r=${state.correct_r}`);
      return;
    }
    const v = Number(($("ans").value||"").trim());
    const ok = (v === state.correct);
    onCheckResult(ok, `Зөв: ${state.correct}`);
  }

  function onCheckResult(ok, solutionText){
    if(ok){
      state.streak += 1;
      // stars reward: stage used (less hints -> more stars)
      const reward = (state.stage<=1) ? 3 : (state.stage===2 ? 2 : 1);
      state.stars += reward;

      // level up every 5 streak on this op
      if(state.streak % 5 === 0){
        state.level[state.op] = clamp((state.level[state.op]||1) + 1, 1, 10);
        setToast(`🎉 Мундаг! Level ${state.level[state.op]} боллоо (+${reward}⭐)`, "ok");
      } else {
        setToast(`✅ Зөв! +${reward}⭐`, "ok");
      }

      celebrate();
      state.stage = 3;
      saveProgress();
      render();

      // auto next
      setTimeout(()=>newProblem(), 900);
    } else {
      state.streak = 0;
      setToast(`❌ Буруу. ${solutionText}`, "bad");
      // give a gentle hint by increasing stage once
      state.stage = clamp(state.stage + 1, 0, 3);
      render();
      saveProgress();
    }
    refreshUI();
  }

  function hintStep(){
    state.stage = clamp(state.stage + 1, 0, 3);
    setToast(`💡 Stage: ${state.stage}`, "info");
    render();
  }

  function revealAll(){
    state.stage = 3;
    setToast("👀 Бүрэн дүрслэл", "info");
    render();
  }

  // Learn panel wiring
  function syncFromLearnUI(){
    state.a = Number($("a").value||0);
    state.b = Number($("b").value||0);
    state.stage = Number($("stage").value||3);
    state.unit = Number($("unit").value||56);
    state.show_grid = $("showGrid").checked;
    state.show_marks = $("showMarks").checked;
    state.color_mode = Number($("colorMode").value||1);

    if(state.op==="div"){
      state.align = $("align").value || "right";
      state.sub_pos = $("subPos").value || "top";
      state.show_remainder = $("showRemainder").checked;
      if(state.b<=0) state.b = 1;
      $("b").value = String(state.b);
    }
    computeCorrect();
    render();
  }

  // events
  tabs.forEach(btn => btn.addEventListener("click", () => setOp(btn.dataset.op)));
  $("modePlay").addEventListener("click", () => setMode("play"));
  $("modeLearn").addEventListener("click", () => setMode("learn"));

  $("newBtn").addEventListener("click", () => newProblem());
  $("checkBtn").addEventListener("click", () => checkAnswer());
  $("hintBtn").addEventListener("click", () => hintStep());
  $("solveBtn").addEventListener("click", () => revealAll());
  $("traceBtn").addEventListener("click", () => showTrace());

  $("useRemainder").addEventListener("change", (e) => {
    state.allowRemainder = !!e.target.checked;
    newProblem();
  });

  // Learn panel
  $("renderBtn").addEventListener("click", () => syncFromLearnUI());
  ["a","b","stage","unit","showGrid","showMarks","colorMode","align","subPos","showRemainder"].forEach(id=>{
    const el = $(id);
    if(!el) return;
    el.addEventListener("input", ()=> {
      if(state.mode==="learn"){
        if(id==="unit") $("unitVal").textContent = String($("unit").value);
        syncFromLearnUI();
      }
    });
  });

  // Enter key submit
  document.addEventListener("keydown", (e) => {
    if(e.key === "Enter"){
      if(state.mode==="play"){
        checkAnswer();
      } else {
        syncFromLearnUI();
      }
    }
  });

  // init
  loadProgress();
  // defaults
  state.unit = Number($("unit").value||56);
  state.color_mode = Number($("colorMode").value||1);
  state.show_grid = $("showGrid").checked;
  state.show_marks = $("showMarks").checked;

  // start play mode with a new problem
  setMode("play");
  setOp("add");
})();