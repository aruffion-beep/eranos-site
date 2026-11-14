var CONTACT = ["alain.ruffion","hotmail.fr"].join("@");

/* ---------- contact ---------- */
var mail = document.getElementById("mail");
if (mail){
mail.textContent = CONTACT; mail.href = "mailto:" + CONTACT + "?subject=" + encodeURIComponent("ERANOS Institute : demande d'information");
document.getElementById("mailbtn").href = mail.href;
document.getElementById("copy").addEventListener("click", function(){
  var out = document.getElementById("copied"), no = "Copie impossible ici : sélectionnez l'adresse à gauche.";
  try { navigator.clipboard.writeText(CONTACT).then(function(){ out.textContent = "Adresse copiée."; }, function(){ out.textContent = no; }); } catch(e){ out.textContent = no; }
});
}

/* ---------- paysage : crêtes, îles, reflets ---------- */
function rng(seed){ var s = seed % 2147483647; if (s <= 0) s += 2147483646; return function(){ s = s * 16807 % 2147483647; return (s - 1) / 2147483646; }; }
function ridge(r, W, base, amp, rough, peaks){
  var n = 96, pts = [], ph = [], i, k;
  for (k = 0; k < 5; k++) ph.push([r()*6.28, (k+1)*(0.6 + r()*0.9), 1/(k+1.4)]);
  for (i = 0; i <= n; i++){
    var x = i / n, y = 0;
    for (k = 0; k < 5; k++) y += Math.sin(ph[k][0] + x * 6.28 * ph[k][1] * peaks) * ph[k][2];
    y += (r() - 0.5) * rough;
    pts.push([x * W, base - (y * 0.5 + 0.55) * amp]);
  }
  return pts;
}
function pathOf(pts, bottom){ return "M0 " + bottom + " L" + pts.map(function(p){ return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L") + " L" + pts[pts.length-1][0] + " " + bottom + " Z"; }
function paint(el){
  var seed = +el.getAttribute("data-seed") || 1, H = +el.getAttribute("data-h") || 600, W = 1600, r = rng(seed * 7919);
  var hz = Math.round(H * 0.66), id = "g" + seed, s = "";
  var cols = ["#8ec3d2","#5f9fb8","#3b7f9c","#235f78","#1c5a4f","#12443b"];
  s += '<defs><linearGradient id="'+id+'s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a2a40"/><stop offset=".5" stop-color="#1f6585"/><stop offset=".82" stop-color="#86c5cc"/><stop offset="1" stop-color="#d8eedb"/></linearGradient>'+
       '<linearGradient id="'+id+'w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9ccfd2"/><stop offset=".18" stop-color="#2f7fa0"/><stop offset=".6" stop-color="#0f3d55"/><stop offset="1" stop-color="#08202f"/></linearGradient>'+
       '<radialGradient id="'+id+'g" cx="72%" cy="100%" r="60%"><stop offset="0" stop-color="#f3fbe6" stop-opacity=".85"/><stop offset="1" stop-color="#f3fbe6" stop-opacity="0"/></radialGradient>'+
       '<linearGradient id="'+id+'m" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>';
  s += '<rect width="'+W+'" height="'+hz+'" fill="url(#'+id+'s)"/><rect width="'+W+'" height="'+hz+'" fill="url(#'+id+'g)"/>';
  var layers = [], i;
  for (i = 0; i < 6; i++){
    var amp = H * (0.34 - i * 0.035) * (i < 4 ? 1 : 0.8), base = hz + (i < 4 ? 0 : 2);
    var pts = ridge(r, W + 160, base, amp, i < 2 ? 0.05 : 0.11, 0.7 + i * 0.28);
    if (i >= 4) pts = pts.map(function(p, j, a){ var x = j / (a.length - 1), cut = i === 4 ? Math.max(0, 1 - x * 2.2) : Math.max(0, (x - 0.52) * 2.2); return [p[0], hz - (hz - p[1]) * Math.min(1, cut * 1.25)]; });
    layers.push(pts);
    s += '<g class="layer" data-d="'+((i+1)*0.5)+'"><path d="'+pathOf(pts, hz + 2)+'" fill="'+cols[i]+'" transform="translate(-80 0)"/></g>';
    if (i === 1) s += '<rect class="mistband" x="-100" y="'+(hz - H*0.13)+'" width="'+(W+200)+'" height="'+(H*0.07)+'" fill="url(#'+id+'m)" opacity=".5"/>';
  }
  /* lac */
  s += '<rect y="'+hz+'" width="'+W+'" height="'+(H - hz)+'" fill="url(#'+id+'w)"/>';
  s += '<g opacity=".3" transform="translate(-80 '+(2*hz)+') scale(1 -1)">';
  for (i = 2; i < 6; i++) s += '<path d="'+pathOf(layers[i], hz + 2)+'" fill="'+cols[Math.min(5,i+1)]+'"/>';
  s += '</g><rect y="'+hz+'" width="'+W+'" height="'+(H - hz)+'" fill="url(#'+id+'w)" opacity=".55"/>';
  /* îles de Brissago */
  var ix = W * 0.6, iy = hz + (H - hz) * 0.2;
  s += '<g class="layer" data-d="3.4"><path d="M'+(ix-90)+' '+iy+' q30 -22 70 -20 q26 -14 50 2 q30 2 44 18 Z" fill="#0f3b34"/><path d="M'+(ix+92)+' '+(iy+3)+' q18 -13 38 -11 q20 0 30 11 Z" fill="#0f3b34"/><rect x="'+(ix-96)+'" y="'+iy+'" width="270" height="3" fill="#cfe8d8" opacity=".35"/></g>';
  /* barques de pêcheurs, au loin */
  var fleet = [[0.1,0.38,210,-0.35,-1],[0.16,0.46,150,-0.62,1],[0.22,0.52,170,-0.9,1],[0.3,0.62,115,-0.25,-1],[0.38,0.7,135,-0.55,1],[0.5,0.85,190,-0.8,1],[0.62,0.95,160,-0.4,-1],[0.72,1.05,125,-0.15,1],[0.07,0.34,230,-0.75,1],[0.19,0.48,185,-0.12,-1],[0.27,0.58,145,-0.48,1],[0.44,0.78,175,-0.3,-1],[0.56,0.9,140,-0.68,1]], k = Math.max(0.6, H / 760);
  fleet.forEach(function(b){
    var y = (hz + (H - hz) * b[0]).toFixed(0), sc = (b[1] * k).toFixed(2), dir = b[4], x0 = dir > 0 ? -120 : W + 120, x1 = dir > 0 ? W + 120 : -120;
    var man = '<path d="M-34 0 Q-24 8 0 8 Q26 8 38 -3 L28 0 Z"/><path d="M-9 0 L-7 -13 Q-4 -17 -1 -13 L2 0 Z"/><path d="M-13 -15 L-4 -22 L6 -15 Z"/><path d="M-1 -11 L30 9" fill="none" stroke="#0a2a30" stroke-width="1.3" stroke-linecap="round"/>';
    s += '<g class="boat" transform="translate('+(W*(0.55 + b[0]*0.6)).toFixed(0)+' '+y+')" style="--x0:'+x0+'px;--x1:'+x1+'px;--y:'+y+'px;--t:'+b[2]+'s;--dl:'+(b[2]*b[3]).toFixed(0)+'s"><g transform="scale('+(dir*sc)+' '+sc+')"><g class="bob" fill="#0a2a30">'+man+'</g><g fill="#0a2a30" opacity=".22" transform="translate(0 16) scale(1 -1)">'+man+'</g><rect x="-44" y="7.4" width="90" height="1.2" fill="#d8eedb" opacity=".45"/></g></g>';
  });
  /* reflets */
  s += '<g class="shimmer" stroke="#d8eedb" stroke-linecap="round" opacity=".5">';
  for (i = 0; i < 14; i++){ var y = hz + 10 + (H - hz - 16) * Math.pow(i / 14, 1.4), x1 = r() * W * 0.8; s += '<line x1="'+x1.toFixed(0)+'" y1="'+y.toFixed(0)+'" x2="'+(x1 + 260 + r()*520).toFixed(0)+'" y2="'+y.toFixed(0)+'" stroke-width="'+(0.6 + i*0.07).toFixed(2)+'" stroke-opacity="'+(0.25 + r()*0.4).toFixed(2)+'"/>'; }
  s += '</g>';
  var svg = document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("class","land"); svg.setAttribute("viewBox","0 0 "+W+" "+H); svg.setAttribute("preserveAspectRatio","xMidYMid slice"); svg.setAttribute("aria-hidden","true");
  svg.innerHTML = s; el.insertBefore(svg, el.firstChild);
  var g = document.createElement("div"); g.className = "meander on-dark greek"; el.appendChild(g);
}
document.querySelectorAll(".scene").forEach(paint);
(function(){ /* crêtes du pied de page */
  var r = rng(4242), s = "", cols = ["#0f3d55","#124a4a","#0d3a33"], i;
  for (i = 0; i < 3; i++) s += '<path d="'+pathOf(ridge(r, 1600, 150, 110 - i*26, 0.1, 1 + i*0.5), 150)+'" fill="'+cols[i]+'" opacity="'+(0.55 + i*0.2)+'"/>';
  var f = document.getElementById("footland"); f.innerHTML = s; f.parentNode.style.background = "linear-gradient(180deg,var(--paper) 0,var(--paper) 40px,var(--abyss) 150px)";
})();

/* parallaxe douce */
var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!still){
  var mx = 0, sy = 0, tick = false;
  function move(){ tick = false;
    document.querySelectorAll(".view.on .layer").forEach(function(l){ var d = +l.getAttribute("data-d"); l.style.transform = "translate(" + (mx * d * -9).toFixed(1) + "px," + (sy * d * 0.05).toFixed(1) + "px)"; });
  }
  function ask(){ if (!tick){ tick = true; requestAnimationFrame(move); } }
  window.addEventListener("mousemove", function(e){ mx = e.clientX / window.innerWidth - 0.5; ask(); }, {passive:true});
  window.addEventListener("scroll", function(){ sy = Math.min(window.scrollY, 700); ask(); }, {passive:true});
}

/* ---------- menu et apparition ---------- */
var navEl = document.getElementById("nav"), burger = document.getElementById("burger");
burger.addEventListener("click", function(){ var o = navEl.classList.toggle("open"); burger.setAttribute("aria-expanded", o ? "true" : "false"); });
var io = ("IntersectionObserver" in window) ? new IntersectionObserver(function(es){ es.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target); } }); }, {rootMargin:"0px 0px -8% 0px"}) : null;
document.querySelectorAll(".rv").forEach(function(el){ if (io) io.observe(el); else el.classList.add("in"); });

/* ---------- boîte de dialogue : écrire à l'institut ---------- */
(function(){
  var dlg = document.getElementById("dlg"), form = document.getElementById("wform"), st = document.getElementById("f-status"), send = document.getElementById("f-send");
  if (!dlg || !form) return;
  document.addEventListener("click", function(ev){
    var b = ev.target.closest ? ev.target.closest("[data-write]") : null;
    if (!b) return;
    ev.preventDefault();
    var s = b.getAttribute("data-write");
    if (s) document.getElementById("f-obj").value = s;
    st.textContent = ""; st.className = "";
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    document.getElementById("f-name").focus();
  });
  document.getElementById("dlg-x").addEventListener("click", function(){ dlg.close(); });
  dlg.addEventListener("click", function(ev){ if (ev.target === dlg) dlg.close(); });
  form.addEventListener("submit", function(ev){
    ev.preventDefault();
    if (!form.checkValidity()){ form.reportValidity(); return; }
    var d = {}; new FormData(form).forEach(function(v, k){ d[k] = v; });
    if (d._honey){ return; }
    d._subject = "Site ERANOS Institute : " + d.objet;
    d._template = "table";
    d._replyto = d.email;
    send.disabled = true; st.className = ""; st.textContent = "Envoi en cours…";
    fetch("https://formsubmit.co/ajax/" + CONTACT, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(d) })
      .then(function(r){ return r.json().then(function(j){ return { ok: r.ok, j: j }; }); })
      .then(function(r){
        if (r.ok && String(r.j.success) === "true"){ st.className = "ok"; st.textContent = "Message envoyé. Merci, nous vous répondons sous 24 à 72 heures."; form.reset(); }
        else { throw new Error("refus"); }
      })
      .catch(function(){ st.className = "ko"; st.textContent = "L'envoi n'a pas abouti. Écrivez-nous à " + CONTACT + " ou appelez le +33 6 29 76 83 90."; })
      .then(function(){ send.disabled = false; });
  });
})();
