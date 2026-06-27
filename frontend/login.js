const EYE_OPEN = '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>';
const EYE_OFF  = '<line x1="17.94" y1="11.12" x2="12" y2="17.07"/><path d="M10.73 5.08A10.43 10.43 0 0112 5c7 0 10 7 10 7a13.16 13.16 0 01-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 002 12s3 7 10 7a9.74 9.74 0 005.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/>';

/* ── Panels (Sign In / Register) ── */
var cardEl     = document.getElementById('card');
var panSignin  = document.getElementById('panel-signin');
var panSignup  = document.getElementById('panel-signup');
var footerText = document.getElementById('footer-text');
var cardTitle  = document.getElementById('card-title');
var currentTab = 'signin';

function switchTab(tab) {
  currentTab = tab;
  panSignin.classList.toggle('active', tab === 'signin');
  panSignup.classList.toggle('active', tab === 'signup');
  cardEl.classList.toggle('is-register', tab === 'signup');
  cardTitle.innerHTML = tab === "signin" ? "Welcome <span>Back</span>" : "Create <span>Account</span>";
  renderFooter();
}

function renderFooter() {
  if (currentTab === 'signin') {
    footerText.innerHTML = "Don't have an account? <button class=\"link-btn\" id=\"footer-link\">Register</button> quickly";
  } else {
    footerText.innerHTML = "Already have an account? <button class=\"link-btn\" id=\"footer-link\">Sign In</button>";
  }
  document.getElementById('footer-link').addEventListener('click', function() {
    switchTab(currentTab === 'signin' ? 'signup' : 'signin');
  });
}

document.getElementById('footer-link').addEventListener('click', function() { switchTab('signup'); });

/* ── Password toggles ── */
function makeEyeToggle(inputId, iconId, btnId) {
  document.getElementById(btnId).addEventListener('click', function() {
    var inp  = document.getElementById(inputId);
    var icon = document.getElementById(iconId);
    var visible = inp.type === 'text';
    inp.type = visible ? 'password' : 'text';
    icon.innerHTML = visible ? EYE_OPEN : EYE_OFF;
  });
}
makeEyeToggle('si-password', 'si-eye-icon', 'si-eye-btn');
makeEyeToggle('su-password', 'su-eye-icon', 'su-eye-btn');

/* ── Checkbox ── */
document.getElementById('remember-row').addEventListener('click', function() {
  document.getElementById('checkbox').classList.toggle('checked');
});

/* ── Clear name ── */
var suName   = document.getElementById('su-name');
var clearBtn = document.getElementById('clear-btn');
suName.addEventListener('input', function() {
  clearBtn.style.display = suName.value ? 'flex' : 'none';
});
clearBtn.addEventListener('click', function() {
  suName.value = '';
  clearBtn.style.display = 'none';
  suName.focus();
});

/* ── Date of birth custom dropdowns (Month / Day / Year) ── */
function closeAllSelects() {
  document.querySelectorAll('.custom-select.open').forEach(function(w) {
    w.classList.remove('open');
  });
}
document.addEventListener('click', function() {
  closeAllSelects();
});

function buildCustomSelect(wrapperId, items) {
  var wrapper = document.getElementById(wrapperId);
  var trigger = wrapper.querySelector('.custom-select-trigger');
  var label   = wrapper.querySelector('.custom-select-label');
  var menu    = wrapper.querySelector('.custom-select-menu');
  menu.addEventListener('click', function(e) { e.stopPropagation(); });

  items.forEach(function(item) {
    var opt = document.createElement('div');
    opt.className = 'custom-select-option';
    opt.textContent = item.label;
    opt.dataset.value = item.value;
    opt.addEventListener('click', function(e) {
      e.stopPropagation();
      trigger.dataset.value = item.value;
      label.textContent = item.label;
      menu.querySelectorAll('.custom-select-option').forEach(function(o) {
        o.classList.remove('selected');
      });
      opt.classList.add('selected');
      wrapper.classList.remove('open');
    });
    menu.appendChild(opt);
  });

  trigger.addEventListener('click', function(e) {
    e.stopPropagation();
    var isOpen = wrapper.classList.contains('open');
    closeAllSelects();
    if (!isOpen) wrapper.classList.add('open');
  });
}

(function initDob() {
  var months = ['January','February','March','April','May','June',
                'July','August','September','October','November','December']
    .map(function(name, i) { return { value: i + 1, label: name }; });

  var days = [];
  for (var d = 1; d <= 31; d++) days.push({ value: d, label: String(d) });

  var years = [];
  var currentYear = new Date().getFullYear();
  var maxYear = currentYear - 13;
  var minYear = currentYear - 100;
  for (var y = maxYear; y >= minYear; y--) years.push({ value: y, label: String(y) });

  buildCustomSelect('su-dob-month', months);
  buildCustomSelect('su-dob-day', days);
  buildCustomSelect('su-dob-year', years);
})();

/* ══════════════════════════════════════════════════════════
   API / FETCH SECTION
══════════════════════════════════════════════════════════ */

const API = "http://localhost:8000";

/* ── Helper: show inline error ── */
function showError(msg) {
  let el = document.getElementById("form-error");
  if (!el) {
    el = document.createElement("p");
    el.id = "form-error";
    el.style.cssText = "color:#ff4d4d;font-size:13px;text-align:center;margin:8px 0 0;";
  }
  el.textContent = msg;
  const activePanel = currentTab === "signin" ? panSignin : panSignup;
  const btn = activePanel.querySelector(".btn-primary");
  activePanel.insertBefore(el, btn);
}

function clearError() {
  const el = document.getElementById("form-error");
  if (el) el.remove();
}

/* ── Helper: get DOB from custom selects ── */
function getDOB() {
  const m = document.querySelector("#su-dob-month .custom-select-trigger").dataset.value;
  const d = document.querySelector("#su-dob-day .custom-select-trigger").dataset.value;
  const y = document.querySelector("#su-dob-year .custom-select-trigger").dataset.value;
  if (!m || !d || !y) return null;
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

/* ── LOGIN ── */
panSignin.querySelector(".btn-primary").addEventListener("click", async function () {
  clearError();
  const email    = document.getElementById("si-email").value.trim();
  const password = document.getElementById("si-password").value;

  if (!email || !password) return showError("Please fill in all fields.");

  this.textContent = "LOGGING IN...";
  this.disabled = true;

  try {
    const res  = await fetch(`${API}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || "Login failed.");
    } else {
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user",  JSON.stringify(data.user));
      window.location.href = "dashboard.html";
    }
  } catch (err) {
    showError("Network error. Is the server running?");
  } finally {
    this.textContent = "LOGIN";
    this.disabled = false;
  }
});

/* ── REGISTER ── */
panSignup.querySelector(".btn-primary").addEventListener("click", async function () {
  clearError();

  const name     = document.getElementById("su-name").value.trim();
  const email    = document.getElementById("su-email").value.trim();
  const phone    = document.getElementById("su-mobile").value.trim() || null;
  const password = document.getElementById("su-password").value;
  const income   = parseFloat(document.getElementById("su-income").value) || null;
  const savings  = parseFloat(document.getElementById("su-savings-goal").value) || null;
  const dob      = getDOB();

  if (!name || !email || !password) return showError("Name, email and password are required.");
  if (password.length < 6)          return showError("Password must be at least 6 characters.");

  this.textContent = "CREATING...";
  this.disabled = true;

  try {
    const res  = await fetch(`${API}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        password,
        phone,
        dob,
        monthly_income:       income,
        monthly_savings_goal: savings
      })
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || "Registration failed.");
    } else {
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user",  JSON.stringify(data.user));
      window.location.href = "dashboard.html";
    }
  } catch (err) {
    showError("Network error. Is the server running?");
  } finally {
    this.textContent = "CREATE ACCOUNT";
    this.disabled = false;
  }
});