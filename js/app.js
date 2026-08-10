/*
 * TaskBoard — vanilla JavaScript, no backend.
 * Tasks are kept in the browser's localStorage, so there is no server-side
 * database. Nginx only ever serves the static files; all logic runs here.
 */
(function () {
  "use strict";

  const STORAGE_KEY = "taskboard.tasks.v1";

  /** @type {{id:string, text:string, priority:string, done:boolean}[]} */
  let tasks = [];
  let currentFilter = "all";

  // --- Elements ------------------------------------------------------------
  const form = document.getElementById("task-form");
  const input = document.getElementById("task-input");
  const priority = document.getElementById("task-priority");
  const list = document.getElementById("task-list");
  const emptyState = document.getElementById("empty-state");
  const countActive = document.getElementById("count-active");
  const countDone = document.getElementById("count-done");
  const clearDoneBtn = document.getElementById("clear-done");
  const filterButtons = document.querySelectorAll(".filter");

  // --- Persistence ---------------------------------------------------------
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      tasks = raw ? JSON.parse(raw) : [];
    } catch (err) {
      console.warn("Could not read saved tasks:", err);
      tasks = [];
    }
  }

  function save() {
    try 
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
    } catch (err) {
      console.warn("Could not save tasks:", err);
    }
  }

  // --- Helpers -------------------------------------------------------------
  function makeId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  function visibleTasks() {
    if (currentFilter === "active") return tasks.filter((t) => !t.done);
    if (currentFilter === "done") return tasks.filter((t) => t.done);
    return tasks;
  }

  // --- Rendering -----------------------------------------------------------
  function render() {
    list.innerHTML = "";
    const shown = visibleTasks();

    shown.forEach((task) => {
      const li = document.createElement("li");
      li.className = "task-item priority-" + task.priority + (task.done ? " done" : "");
      li.dataset.id = task.id;

      const check = document.createElement("input");
      check.type = "checkbox";
      check.className = "task-check";
      check.checked = task.done;
      check.setAttribute("aria-label", "Mark complete");
      check.addEventListener("change", () => toggle(task.id));

      const span = document.createElement("span");
      span.className = "task-text";
      span.textContent = task.text;

      const badge = document.createElement("span");
      badge.className = "task-badge";
      badge.textContent = task.priority;

      const del = document.createElement("button");
      del.className = "task-delete";
      del.innerHTML = "&times;";
      del.title = "Delete task";
      del.setAttribute("aria-label", "Delete task");
      del.addEventListener("click", () => remove(task.id));

      li.append(check, span, badge, del);
      list.appendChild(li);
    });

    const activeCount = tasks.filter((t) => !t.done).length;
    const doneCount = tasks.length - activeCount;
    countActive.textContent = String(activeCount);
    countDone.textContent = String(doneCount);

    emptyState.classList.toggle("hidden", shown.length > 0);
  }

  // --- Actions -------------------------------------------------------------
  function add(text, prio) {
    tasks.unshift({ id: makeId(), text: text, priority: prio, done: false });
    save();
    render();
  }

  function toggle(id) {
    const task = tasks.find((t) => t.id === id);
    if (task) {
      task.done = !task.done;
      save();
      render();
    }
  }

  function remove(id) {
    tasks = tasks.filter((t) => t.id !== id);
    save();
    render();
  }

  function clearDone() {
    tasks = tasks.filter((t) => !t.done);
    save();
    render();
  }

  // --- Events --------------------------------------------------------------
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    add(text, priority.value);
    input.value = "";
    input.focus();
  });

  clearDoneBtn.addEventListener("click", clearDone);

  filterButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentFilter = btn.dataset.filter;
      render();
    });
  });

  // --- Init ----------------------------------------------------------------
  load();
  render();
})();
