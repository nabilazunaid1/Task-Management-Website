
// ---------------------------------------
// 1. Find HTML elements
// ---------------------------------------
const authSection = document.getElementById("authSection");
const dashboardSection = document.getElementById("dashboardSection");

const authForm = document.getElementById("authForm");
const authTitle = document.getElementById("authTitle");
const authButton = document.getElementById("authButton");
const authMessage = document.getElementById("authMessage");
const switchAuth = document.getElementById("switchAuth");
const switchText = document.getElementById("switchText");

const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");

const welcomeText = document.getElementById("welcomeText");
const logoutButton = document.getElementById("logoutButton");

const taskForm = document.getElementById("taskForm");
const taskInput = document.getElementById("taskInput");
const priorityInput = document.getElementById("priorityInput");
const dueDateInput = document.getElementById("dueDateInput");

const searchInput = document.getElementById("searchInput");
const taskList = document.getElementById("taskList");
const filterButtons = document.querySelectorAll("[data-filter]");

let csrfToken = "";
let isRegistering = false;
let allTasks = [];
let currentFilter = "all";


// ---------------------------------------
// 2. Helper for API requests
// ---------------------------------------
async function apiRequest(url, options = {}) {
    const headers = {
        ...(options.headers || {})
    };

    const method = (options.method || "GET").toUpperCase();

    if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
        headers["X-CSRF-Token"] = csrfToken;
    }

    const response = await fetch(url, {
        ...options,
        headers,
        credentials: "same-origin"
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}


// ---------------------------------------
// 3. Show login or dashboard
// ---------------------------------------
function showAuth() {
    authSection.hidden = false;
    dashboardSection.hidden = true;

    allTasks = [];
    taskList.replaceChildren();
    searchInput.value = "";
    currentFilter = "all";
}

function showDashboard(user) {
    authSection.hidden = true;
    dashboardSection.hidden = false;

    welcomeText.textContent = `Logged in as ${user.email}`;
    authMessage.textContent = "";

    loadTasks();
}


// ---------------------------------------
// 4. Check existing login session
// ---------------------------------------
async function checkSession() {
    try {
        const data = await apiRequest("/api/me");

        csrfToken = data.csrf_token;

        if (data.user) {
            showDashboard(data.user);
        } else {
            showAuth();
        }

    } catch (error) {
        showAuth();
        authMessage.textContent = error.message;
    }
}


// ---------------------------------------
// 5. Switch login / registration
// ---------------------------------------
switchAuth.addEventListener("click", () => {
    isRegistering = !isRegistering;

    authTitle.textContent = isRegistering
        ? "Create Account"
        : "Log In";

    authButton.textContent = isRegistering
        ? "Register"
        : "Log In";

    switchText.textContent = isRegistering
        ? "Already have an account?"
        : "Don't have an account?";

    switchAuth.textContent = isRegistering
        ? "Log In"
        : "Register";

    passwordInput.value = "";
    passwordInput.minLength = isRegistering ? 12 : 1;
    authMessage.textContent = "";
});


// ---------------------------------------
// 6. Register or log in
// ---------------------------------------
authForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    const endpoint = isRegistering
        ? "/api/register"
        : "/api/login";

    try {
        const data = await apiRequest(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        passwordInput.value = "";

        if (isRegistering) {
            authMessage.style.color = "green";
            authMessage.textContent =
                "Registration successful! Click Log In below.";
        } else {
            csrfToken = data.csrf_token;
            showDashboard(data.user);
        }

    } catch (error) {
        authMessage.style.color = "#dc2626";
        authMessage.textContent = error.message;
    }
});


// ---------------------------------------
// 7. Logout
// ---------------------------------------
logoutButton.addEventListener("click", async () => {
    try {
        const data = await apiRequest("/api/logout", {
            method: "POST"
        });

        csrfToken = data.csrf_token;

        showAuth();

    } catch (error) {
        alert(error.message);
    }
});


// ---------------------------------------
// 8. Load private tasks
// ---------------------------------------
async function loadTasks() {
    try {
        allTasks = await apiRequest("/api/tasks");
        displayTasks();

    } catch (error) {
        alert(error.message);
    }
}


// ---------------------------------------
// 9. Display, search and filter tasks
// ---------------------------------------
function displayTasks() {
    const searchText = searchInput.value.toLowerCase();

    let tasks = allTasks.filter(task =>
        task.title.toLowerCase().includes(searchText)
    );

    if (currentFilter === "pending") {
        tasks = tasks.filter(task => !task.completed);
    }

    if (currentFilter === "completed") {
        tasks = tasks.filter(task => Boolean(task.completed));
    }

    taskList.replaceChildren();

    if (tasks.length === 0) {
        const message = document.createElement("li");
        message.textContent = "No matching tasks found.";
        taskList.appendChild(message);
        return;
    }

    tasks.forEach(task => {
        const li = document.createElement("li");

        const header = document.createElement("div");
        header.className = "task-header";

        const title = document.createElement("span");
        title.className = "task-name";
        title.textContent = task.title;

        if (task.completed) {
            title.classList.add("completed");
        }

        title.addEventListener("click", () => {
            toggleComplete(task);
        });

        const editButton = document.createElement("button");
        editButton.textContent = "Edit";
        editButton.className = "edit-btn";

        editButton.addEventListener("click", () => {
            showEditForm(li, task);
        });

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-btn";

        deleteButton.addEventListener("click", () => {
            deleteTask(task.id);
        });

        header.append(title, editButton, deleteButton);

        const details = document.createElement("div");
        details.className = "task-details";

        const priority = document.createElement("span");
        priority.className =
            `priority-badge priority-${task.priority}`;
        priority.textContent = `${task.priority} Priority`;

        const date = document.createElement("span");
        date.textContent = task.due_date
            ? `Due: ${task.due_date}`
            : "No due date";

        details.append(priority, date);

        li.append(header, details);
        taskList.appendChild(li);
    });
}


// ---------------------------------------
// 10. Add a task
// ---------------------------------------
taskForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const title = taskInput.value.trim();

    if (!title) return;

    try {
        await apiRequest("/api/tasks", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title,
                priority: priorityInput.value,
                due_date: dueDateInput.value || null
            })
        });

        taskForm.reset();
        await loadTasks();

    } catch (error) {
        alert(error.message);
    }
});


// ---------------------------------------
// 11. Save task changes
// ---------------------------------------
async function saveTask(id, task) {
    return apiRequest(`/api/tasks/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(task)
    });
}


// ---------------------------------------
// 12. Complete or uncomplete task
// ---------------------------------------
async function toggleComplete(task) {
    try {
        await saveTask(task.id, {
            title: task.title,
            completed: !Boolean(task.completed),
            priority: task.priority,
            due_date: task.due_date
        });

        await loadTasks();

    } catch (error) {
        alert(error.message);
    }
}


// ---------------------------------------
// 13. Edit task
// ---------------------------------------
function showEditForm(li, task) {
    li.replaceChildren();

    const form = document.createElement("form");
    form.className = "edit-form";

    const titleInput = document.createElement("input");
    titleInput.value = task.title;
    titleInput.maxLength = 100;
    titleInput.required = true;

    const prioritySelect = document.createElement("select");

    ["Low", "Medium", "High"].forEach(value => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        prioritySelect.appendChild(option);
    });

    prioritySelect.value = task.priority;

    const dateInput = document.createElement("input");
    dateInput.type = "date";
    dateInput.value = task.due_date || "";

    const saveButton = document.createElement("button");
    saveButton.type = "submit";
    saveButton.textContent = "Save";

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.textContent = "Cancel";

    cancelButton.addEventListener("click", displayTasks);

    form.append(
        titleInput,
        prioritySelect,
        dateInput,
        saveButton,
        cancelButton
    );

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            await saveTask(task.id, {
                title: titleInput.value.trim(),
                completed: Boolean(task.completed),
                priority: prioritySelect.value,
                due_date: dateInput.value || null
            });

            await loadTasks();

        } catch (error) {
            alert(error.message);
        }
    });

    li.appendChild(form);
}


// ---------------------------------------
// 14. Delete task
// ---------------------------------------
async function deleteTask(id) {
    try {
        await apiRequest(`/api/tasks/${id}`, {
            method: "DELETE"
        });

        await loadTasks();

    } catch (error) {
        alert(error.message);
    }
}


// ---------------------------------------
// 15. Search and filter
// ---------------------------------------
searchInput.addEventListener("input", displayTasks);

filterButtons.forEach(button => {
    button.addEventListener("click", () => {
        currentFilter = button.dataset.filter;

        filterButtons.forEach(btn => {
            btn.classList.toggle(
                "active",
                btn === button
            );
        });

        displayTasks();
    });
});

document.querySelector(
    '[data-filter="all"]'
).classList.add("active");


// ---------------------------------------
// 16. Start the application
// ---------------------------------------
checkSession();
