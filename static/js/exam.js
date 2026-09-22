(function () {
  "use strict";

  var body = document.querySelector(".exam-body");
  var slides = Array.prototype.slice.call(document.querySelectorAll(".question-slide"));
  var navButtons = Array.prototype.slice.call(document.querySelectorAll("#qnav-grid button"));
  var prevBtn = document.getElementById("prev-btn");
  var nextBtn = document.getElementById("next-btn");
  var submitBtn = document.getElementById("submit-btn");
  var submitBtnSide = document.getElementById("submit-btn-side");
  var form = document.getElementById("exam-form");
  var timerEl = document.getElementById("timer");

  var total = slides.length;
  var current = 0;
  var submitted = false;

  function showSlide(index) {
    if (index < 0 || index >= total) return;
    slides[current].style.display = "none";
    current = index;
    slides[current].style.display = "";

    navButtons.forEach(function (btn) {
      btn.classList.toggle("current", parseInt(btn.dataset.index, 10) === current);
    });

    prevBtn.disabled = current === 0;
    var isLast = current === total - 1;
    nextBtn.style.display = isLast ? "none" : "";
    submitBtn.style.display = isLast ? "" : "none";
  }

  function refreshAnsweredState() {
    slides.forEach(function (slide, i) {
      var answered = slide.querySelector('input[type="radio"]:checked') !== null;
      var navBtn = navButtons[i];
      if (navBtn) {
        navBtn.classList.toggle("answered", answered);
      }
      var options = slide.querySelectorAll(".option");
      options.forEach(function (opt) {
        var input = opt.querySelector("input");
        opt.classList.toggle("selected", input.checked);
      });
    });
  }

  navButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      showSlide(parseInt(btn.dataset.index, 10));
    });
  });

  prevBtn.addEventListener("click", function () {
    showSlide(current - 1);
  });

  nextBtn.addEventListener("click", function () {
    showSlide(current + 1);
  });

  form.addEventListener("change", refreshAnsweredState);

  function doSubmit() {
    if (submitted) return;
    submitted = true;
    form.submit();
  }

  function confirmSubmit() {
    var answeredCount = navButtons.filter(function (btn) {
      return btn.classList.contains("answered");
    }).length;
    var unanswered = total - answeredCount;
    var message = unanswered > 0
      ? "You have " + unanswered + " unanswered question(s). Submit anyway?"
      : "Submit your exam now? You cannot change your answers afterward.";
    if (window.confirm(message)) {
      doSubmit();
    }
  }

  submitBtn.addEventListener("click", confirmSubmit);
  submitBtnSide.addEventListener("click", confirmSubmit);

  // Warn on accidental navigation away.
  window.addEventListener("beforeunload", function (e) {
    if (submitted) return;
    e.preventDefault();
    e.returnValue = "";
  });

  // ---------------------------------------------------------------------
  // Countdown timer
  // ---------------------------------------------------------------------
  var durationSeconds = parseInt(body.dataset.durationSeconds, 10) || 0;
  var remaining = durationSeconds;

  function formatTime(totalSeconds) {
    var m = Math.floor(totalSeconds / 60);
    var s = totalSeconds % 60;
    return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
  }

  function tick() {
    if (submitted) return;
    timerEl.textContent = formatTime(Math.max(remaining, 0));
    timerEl.classList.toggle("low-time", remaining <= 60);

    if (remaining <= 0) {
      submitted = true;
      alert("Time is up. Your exam is being submitted automatically.");
      form.submit();
      return;
    }
    remaining -= 1;
    window.setTimeout(tick, 1000);
  }

  showSlide(0);
  refreshAnsweredState();
  tick();
})();
