function removeListItemById(listId, itemId, isSkill = false) {
  const list = document.getElementById(listId);
  if (!list) return;
  const item = document.getElementById(itemId);
  if (item) {
    item.classList.add("fade-out");
    setTimeout(() => {
      // Remove the item from the DOM after fade-out
      if (isSkill) {
        // For skills, check if this was the last skill in its group
        const groupListItem = item.closest("li.list-group-item");
        if (groupListItem) {
          item.remove();
          // Check if there are any remaining skills in this group
          const remainingSkills = groupListItem.querySelectorAll(
            "ul.list-inline > li"
          );
          if (remainingSkills.length === 0) {
            groupListItem.classList.add("fade-out");
            setTimeout(() => {
              groupListItem.remove();
            }, 400);
          }
        }
      } else {
        item.remove();
      }
    }, 400);
  }
}

function deleteBio(bioId) {
  fetch("/delete-bio", {
    method: "POST",
    body: JSON.stringify({ bioId: bioId }),
  }).then((_res) => {
    removeListItemById("bio", "bio-" + bioId);
  });
}

function deleteEducation(educationId) {
  fetch("/delete-education", {
    method: "POST",
    body: JSON.stringify({ educationId: educationId }),
  }).then((_res) => {
    removeListItemById("education", "education-" + educationId);
  });
}

function deleteExperience(experienceId) {
  fetch("/delete-experience", {
    method: "POST",
    body: JSON.stringify({ experienceId: experienceId }),
  }).then((_res) => {
    removeListItemById("experience", "experience-" + experienceId);
  });
}

function deleteProject(projectId) {
  fetch("/delete-project", {
    method: "POST",
    body: JSON.stringify({ projectId: projectId }),
  }).then((_res) => {
    removeListItemById("project", "project-" + projectId);
  });
}

function deleteSkill(skillId) {
  fetch("/delete-skill", {
    method: "POST",
    body: JSON.stringify({ skillId: skillId }),
  }).then((_res) => {
    removeListItemById("skill", "skill-" + skillId, true);
  });
}

function sendEditRequest(url, payload) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then((res) => {
    if (!res.ok) {
      throw new Error("Failed to update");
    }
    return res.json();
  });
}

function runEdit(url, payload) {
  return sendEditRequest(url, payload)
    .then(() => refreshProfileLists())
    .catch((error) => {
      console.error(error);
      alert("Could not save changes. Please try again.");
    });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function showInlineEditor(itemId, contentHtml, onSave, focusSelector) {
  const item = document.getElementById(itemId);
  if (!item) return;

  item.style.display = "block";
  item.style.width = "100%";

  item.innerHTML = `
    <div class="w-100">
      ${contentHtml}
      <div class="d-flex gap-2 mt-3">
        <button type="button" class="btn btn-sm btn-primary" data-inline-save>Save</button>
        <button type="button" class="btn btn-sm btn-outline-secondary" data-inline-cancel>Cancel</button>
      </div>
    </div>
  `;

  const saveBtn = item.querySelector("[data-inline-save]");
  const cancelBtn = item.querySelector("[data-inline-cancel]");
  const focusEl = focusSelector ? item.querySelector(focusSelector) : null;

  if (focusEl) focusEl.focus();

  saveBtn?.addEventListener("click", () => onSave(item));
  cancelBtn?.addEventListener("click", () => refreshProfileLists());
}

function refreshProfileLists() {
  return fetch(window.location.pathname)
    .then((res) => res.text())
    .then((html) => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      ["bio", "education", "experience", "project", "skill"].forEach((id) => {
        const currentList = document.getElementById(id);
        const newList = doc.getElementById(id);
        if (currentList && newList) {
          currentList.innerHTML = newList.innerHTML;
        }
      });
      if (typeof window.syncSkillGroupOptionsFromHtml === "function") {
        window.syncSkillGroupOptionsFromHtml(doc);
      }
      if (typeof window.setupCollapsibleSections === "function") {
        window.setupCollapsibleSections();
      }
    });
}

function editBio(bioId, currentBio) {
  const itemId = `bio-${bioId}`;
  showInlineEditor(
    itemId,
    `
      <label class="form-label mb-2">Edit Bio</label>
      <textarea class="form-control" rows="3" data-bio-text>${escapeHtml(currentBio || "")}</textarea>
    `,
    (item) => {
      const bio = item.querySelector("[data-bio-text]")?.value?.trim() || "";
      if (!bio) return;
      runEdit("/edit-bio", { bioId, bio });
    },
    "[data-bio-text]"
  );
}

function editEducation(
  educationId,
  currentUni,
  currentLocation,
  currentDegree,
  currentStartYear,
  currentEndYear
) {
  const itemId = `education-${educationId}`;
  showInlineEditor(
    itemId,
    `
      <div class="row g-2">
        <div class="col-md-6"><input class="form-control" data-edu-uni value="${escapeHtml(currentUni || "")}" placeholder="Institution name" /></div>
        <div class="col-md-6"><input class="form-control" data-edu-location value="${escapeHtml(currentLocation || "")}" placeholder="Location" /></div>
        <div class="col-md-6"><input class="form-control" data-edu-degree value="${escapeHtml(currentDegree || "")}" placeholder="Degree" /></div>
        <div class="col-md-3"><input class="form-control" data-edu-start value="${escapeHtml(currentStartYear || "")}" placeholder="Start year" /></div>
        <div class="col-md-3"><input class="form-control" data-edu-end value="${escapeHtml(currentEndYear || "")}" placeholder="End year" /></div>
      </div>
    `,
    (item) => {
      runEdit("/edit-education", {
        educationId,
        uni: item.querySelector("[data-edu-uni]")?.value?.trim() || "",
        location: item.querySelector("[data-edu-location]")?.value?.trim() || "",
        degree: item.querySelector("[data-edu-degree]")?.value?.trim() || "",
        start_year: item.querySelector("[data-edu-start]")?.value?.trim() || "",
        end_year: item.querySelector("[data-edu-end]")?.value?.trim() || "",
      });
    },
    "[data-edu-uni]"
  );
}

function editExperience(
  experienceId,
  currentRole,
  currentCompany,
  currentDescription,
  currentStartDate,
  currentEndDate
) {
  const itemId = `experience-${experienceId}`;
  showInlineEditor(
    itemId,
    `
      <div class="row g-2">
        <div class="col-md-6"><input class="form-control" data-exp-role value="${escapeHtml(currentRole || "")}" placeholder="Role" /></div>
        <div class="col-md-6"><input class="form-control" data-exp-comp value="${escapeHtml(currentCompany || "")}" placeholder="Company" /></div>
        <div class="col-12"><textarea class="form-control" rows="3" data-exp-desc placeholder="Description">${escapeHtml(currentDescription || "")}</textarea></div>
        <div class="col-md-6"><input type="date" class="form-control" data-exp-start value="${escapeHtml(currentStartDate || "")}" /></div>
        <div class="col-md-6"><input type="date" class="form-control" data-exp-end value="${escapeHtml(currentEndDate || "")}" /></div>
      </div>
    `,
    (item) => {
      runEdit("/edit-experience", {
        experienceId,
        role: item.querySelector("[data-exp-role]")?.value?.trim() || "",
        comp: item.querySelector("[data-exp-comp]")?.value?.trim() || "",
        desc: item.querySelector("[data-exp-desc]")?.value?.trim() || "",
        start_date: item.querySelector("[data-exp-start]")?.value?.trim() || "",
        end_date: item.querySelector("[data-exp-end]")?.value?.trim() || "",
      });
    },
    "[data-exp-role]"
  );
}

function editProject(projectId, currentProj, currentTool, currentDesc, currentLink) {
  const itemId = `project-${projectId}`;
  showInlineEditor(
    itemId,
    `
      <div class="row g-2">
        <div class="col-md-6"><input class="form-control" data-proj-title value="${escapeHtml(currentProj || "")}" placeholder="Project title" /></div>
        <div class="col-md-6"><input class="form-control" data-proj-tool value="${escapeHtml(currentTool || "")}" placeholder="Tool/Tech" /></div>
        <div class="col-12"><input type="url" class="form-control" data-proj-link value="${escapeHtml(currentLink || "")}" placeholder="Project link (optional)" /></div>
        <div class="col-12"><textarea class="form-control" rows="3" data-proj-desc placeholder="Description">${escapeHtml(currentDesc || "")}</textarea></div>
      </div>
    `,
    (item) => {
      runEdit("/edit-project", {
        projectId,
        proj: item.querySelector("[data-proj-title]")?.value?.trim() || "",
        tool: item.querySelector("[data-proj-tool]")?.value?.trim() || "",
        desc: item.querySelector("[data-proj-desc]")?.value?.trim() || "",
        link: item.querySelector("[data-proj-link]")?.value?.trim() || "",
      });
    },
    "[data-proj-title]"
  );
}

function editSkill(skillId, currentSkill, currentGroup) {
  const itemId = `skill-${skillId}`;
  showInlineEditor(
    itemId,
    `
      <div class="row g-2">
        <div class="col-md-6"><input class="form-control" data-skill-name value="${escapeHtml(currentSkill || "")}" placeholder="Skill" /></div>
        <div class="col-md-6"><input class="form-control" data-skill-group value="${escapeHtml(currentGroup || "")}" placeholder="Group" /></div>
      </div>
    `,
    (item) => {
      const data = item.querySelector("[data-skill-name]")?.value?.trim() || "";
      if (!data) return;
      runEdit("/edit-skill", {
        skillId,
        data,
        group: item.querySelector("[data-skill-group]")?.value?.trim() || "",
      });
    },
    "[data-skill-name]"
  );
}

// Generic AJAX form handler
function handleProfileForm(formId, listId) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const formData = new FormData(form);
    fetch(window.location.pathname, {
      method: "POST",
      body: formData,
    })
      .then((res) => res.text())
      .then((html) => {
        // Parse the returned HTML and update the relevant list
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const newList = doc.getElementById(listId);
        if (newList) {
          document.getElementById(listId).innerHTML = newList.innerHTML;
        }
        if (typeof window.syncSkillGroupOptionsFromHtml === "function") {
          window.syncSkillGroupOptionsFromHtml(doc);
        }
        form.reset();
      });
  });
}

// Attach handlers for all forms
handleProfileForm("bio-form", "bio");
handleProfileForm("education-form", "education");
handleProfileForm("experience-form", "experience");
handleProfileForm("project-form", "project");
handleProfileForm("skill-form", "skill");

function setupGitHubProjectImport() {
  const importBtn = document.getElementById("github_import_btn");
  const repoInput = document.getElementById("github_repo_input");
  const status = document.getElementById("github_import_status");
  const repoDropdown = document.querySelector("[data-github-repo-dropdown]");
  const repoMenu = document.querySelector("[data-github-repo-menu]");
  const titleInput = document.getElementById("proj");
  const toolInput = document.getElementById("tool");
  const linkInput = document.getElementById("proj_link");
  const descInput = document.getElementById("proj_desc");

  if (
    !importBtn ||
    !repoInput ||
    !status ||
    !repoDropdown ||
    !repoMenu ||
    !titleInput ||
    !toolInput ||
    !linkInput ||
    !descInput
  ) {
    return;
  }

  let repoOptions = [];
  let selectedRepoFullName = "";

  const setStatus = (message, className = "text-muted") => {
    status.textContent = message;
    status.className = className;
  };

  const closeRepoMenu = () => {
    repoMenu.classList.remove("is-open");
    repoMenu.innerHTML = "";
  };

  const buildLocalFallback = (repoValue) => {
    const raw = String(repoValue || "").trim();
    if (!raw) return null;

    let fullName = raw;
    if (!fullName.includes("/")) {
      const knownOwner = repoOptions[0]?.full_name?.split("/")?.[0] || "github-user";
      fullName = `${knownOwner}/${fullName}`;
    }

    const repoName = fullName.split("/").pop() || fullName;
    return {
      proj: repoName,
      tool: "",
      desc: "Could not auto-import details from GitHub. Please review and edit before saving.",
      link: `https://github.com/${fullName}`,
    };
  };

  const applyProjectValues = (payload) => {
    titleInput.value = payload?.proj || "";
    toolInput.value = payload?.tool || "";
    linkInput.value = payload?.link || "";
    descInput.value = payload?.desc || "";
  };

  const renderRepoMenu = (query) => {
    const search = String(query || "").trim().toLowerCase();
    const filtered = repoOptions.filter((repo) => {
      const fullName = (repo.full_name || "").toLowerCase();
      const name = (repo.name || "").toLowerCase();
      return !search || fullName.includes(search) || name.includes(search);
    });

    if (!filtered.length) {
      closeRepoMenu();
      return;
    }

    repoMenu.innerHTML = filtered
      .slice(0, 20)
      .map(
        (repo) =>
          `<button type="button" class="skill-group-option" data-repo-full-name="${escapeHtml(repo.full_name)}" data-repo-name="${escapeHtml(repo.name)}">${escapeHtml(repo.full_name)}</button>`
      )
      .join("");
    repoMenu.classList.add("is-open");
  };

  const loadRepos = () => {
    if (repoOptions.length) return Promise.resolve();

    setStatus("Loading repositories from your GitHub profile...");
    return fetch("/github-repos")
      .then(async (res) => {
        const payload = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(payload.error || "Could not load repositories.");
        }
        repoOptions = Array.isArray(payload.repos) ? payload.repos : [];
        if (!repoOptions.length) {
          setStatus("No public repositories found for your GitHub account.", "text-muted");
        } else {
          setStatus(`Found ${repoOptions.length} repositories. Start typing to filter.`, "text-muted");
        }
      })
      .catch((error) => {
        const message = error?.message || "Could not load repositories.";
        setStatus(`${message} You can still type a repo and import with fallback.`, "text-danger");
      });
  };

  repoInput.addEventListener("focus", () => {
    loadRepos().then(() => renderRepoMenu(repoInput.value));
  });

  repoInput.addEventListener("input", () => {
    selectedRepoFullName = "";
    renderRepoMenu(repoInput.value);
  });

  repoMenu.addEventListener("mousedown", (event) => {
    const option = event.target.closest(".skill-group-option");
    if (!option) return;
    event.preventDefault();
    selectedRepoFullName = option.dataset.repoFullName || "";
    repoInput.value = option.dataset.repoName || selectedRepoFullName;
    closeRepoMenu();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-github-repo-dropdown]")) {
      closeRepoMenu();
    }
  });

  importBtn.addEventListener("click", () => {
    const typedValue = repoInput.value.trim();
    const matchedRepo =
      repoOptions.find((repo) => repo.name === typedValue || repo.full_name === typedValue) || null;
    const repo = selectedRepoFullName || matchedRepo?.full_name || typedValue;

    if (!repo) {
      setStatus("Select a repository first.", "text-danger");
      return;
    }

    importBtn.disabled = true;
    setStatus("Importing from GitHub...");

    fetch("/import-github-project", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo }),
    })
      .then(async (res) => {
        const payload = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw {
            message: payload.error || "Could not import repository.",
            fallback: payload.fallback || null,
          };
        }
        return payload;
      })
      .then((payload) => {
        applyProjectValues(payload);
        setStatus("Repository imported. Review and click Add Project.", "text-success");
      })
      .catch((error) => {
        const fallback = error?.fallback || buildLocalFallback(repo);
        if (fallback) {
          applyProjectValues(fallback);
          setStatus(
            `${error?.message || "Import failed."} Filled basic project details as fallback; review and save.`,
            "text-warning"
          );
        } else {
          setStatus(error?.message || "Import failed.", "text-danger");
        }
      })
      .finally(() => {
        importBtn.disabled = false;
      });
  });
}

// Dynamic resume search on homepage
function setupResumeSearch() {
  const searchInput = document.querySelector(
    '.search-bar input[name="search"]'
  );
  if (!searchInput) return;
  searchInput.addEventListener("input", function () {
    const query = searchInput.value.trim().toLowerCase();
    const cards = document.querySelectorAll(".card.h-100");
    let anyVisible = false;
    cards.forEach((card) => {
      const title = card
        .querySelector(".card-title")
        .textContent.trim()
        .toLowerCase();
      if (query === "" || title.includes(query)) {
        card.parentElement.style.display = "";
        anyVisible = true;
      } else {
        card.parentElement.style.display = "none";
      }
    });
    // Show/hide the 'No resumes found' message
    const noResumesMsg = document.querySelector(
      ".col-12.text-center.text-muted"
    );
    if (noResumesMsg) {
      noResumesMsg.style.display = anyVisible ? "none" : "";
    }
  });
}

function setupCollapsibleSections() {
  const sections = document.querySelectorAll(".editor-section[data-collapsible]");
  if (!sections.length) return;

  sections.forEach((section, index) => {
    const title = section.querySelector(":scope > .section-title");
    if (!title) return;
    if (section.querySelector(":scope > .section-toggle")) return;

    const label = (title.textContent || "Section").trim();
    const storageKey = `profileSection:${label}`;
    const body = document.createElement("div");
    body.className = "section-body";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "section-toggle";
    button.setAttribute("aria-expanded", "true");
    button.setAttribute("aria-controls", `section-body-${index + 1}`);
    button.innerHTML = `${title.outerHTML}<span class="section-chevron" aria-hidden="true"><i class="fa-solid fa-chevron-down"></i></span>`;

    title.remove();

    while (section.firstChild) {
      body.appendChild(section.firstChild);
    }

    body.id = `section-body-${index + 1}`;
    section.appendChild(button);
    section.appendChild(body);

    const setCollapsed = (collapsed) => {
      body.classList.toggle("is-collapsed", collapsed);
      button.setAttribute("aria-expanded", String(!collapsed));
    };

    const saved = localStorage.getItem(storageKey);
    setCollapsed(saved ? saved === "collapsed" : true);

    button.addEventListener("click", () => {
      const isCollapsed = body.classList.toggle("is-collapsed");
      button.setAttribute("aria-expanded", String(!isCollapsed));
      localStorage.setItem(storageKey, isCollapsed ? "collapsed" : "expanded");
    });
  });
}

window.setupCollapsibleSections = setupCollapsibleSections;

function setupInlineEditButtons() {
  if (window.__inlineEditButtonsBound) return;
  window.__inlineEditButtonsBound = true;

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-inline-edit]");
    if (!button) return;

    event.preventDefault();
    event.stopPropagation();

    const type = button.dataset.inlineEdit;
    const id = button.dataset.id;
    if (!type || !id) return;

    if (type === "bio") {
      editBio(id, button.dataset.bio || "");
      return;
    }

    if (type === "education") {
      editEducation(
        id,
        button.dataset.uni || "",
        button.dataset.location || "",
        button.dataset.degree || "",
        button.dataset.start || "",
        button.dataset.end || ""
      );
      return;
    }

    if (type === "experience") {
      editExperience(
        id,
        button.dataset.role || "",
        button.dataset.comp || "",
        button.dataset.desc || "",
        button.dataset.startDate || "",
        button.dataset.endDate || ""
      );
      return;
    }

    if (type === "project") {
      editProject(
        id,
        button.dataset.proj || "",
        button.dataset.tool || "",
        button.dataset.desc || "",
        button.dataset.link || ""
      );
      return;
    }

    if (type === "skill") {
      editSkill(id, button.dataset.skill || "", button.dataset.group || "");
    }
  });
}

function setupResumeBuilder() {
  const form = document.querySelector("form[data-resume-builder]");
  if (!form) return;

  const sections = form.querySelectorAll("[data-resume-section]");

  const updateSectionCount = (name) => {
    const count = form.querySelectorAll(`input[name=\"${name}\"]:checked`).length;
    const target = form.querySelector(`[data-selected-count=\"${name}\"]`);
    if (target) target.textContent = String(count);
  };

  const syncCard = (card) => {
    const toggle = card.querySelector("[data-option-toggle]");
    const fields = card.querySelector("[data-option-fields]");
    if (!toggle || !fields) return;
    const checked = toggle.checked;
    card.classList.toggle("is-unselected", !checked);
    fields.querySelectorAll("input, textarea, select").forEach((field) => {
      field.disabled = !checked;
    });
  };

  sections.forEach((section) => {
    const toggleBtn = section.querySelector("[data-resume-section-toggle]");
    const body = section.querySelector("[data-resume-section-body]");
    if (toggleBtn && body) {
      toggleBtn.addEventListener("click", () => {
        body.classList.toggle("is-collapsed");
        const expanded = !body.classList.contains("is-collapsed");
        toggleBtn.setAttribute("aria-expanded", String(expanded));
      });
    }

    section.querySelectorAll("[data-option-card]").forEach((card) => {
      syncCard(card);
      const checkbox = card.querySelector("[data-option-toggle]");
      checkbox?.addEventListener("change", () => {
        syncCard(card);
        if (checkbox.name) updateSectionCount(checkbox.name);
      });
    });
  });

  form.querySelectorAll("[data-select-all]").forEach((button) => {
    button.addEventListener("click", () => {
      const name = button.getAttribute("data-select-all");
      if (!name) return;
      form.querySelectorAll(`input[name=\"${name}\"]`).forEach((checkbox) => {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event("change", { bubbles: true }));
      });
      updateSectionCount(name);
    });
  });

  form.querySelectorAll("[data-clear-all]").forEach((button) => {
    button.addEventListener("click", () => {
      const name = button.getAttribute("data-clear-all");
      if (!name) return;
      form.querySelectorAll(`input[name=\"${name}\"]`).forEach((checkbox) => {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event("change", { bubbles: true }));
      });
      updateSectionCount(name);
    });
  });

  ["bios", "educations", "experiences", "projects", "skill_groups"].forEach(updateSectionCount);
}

function setupResumeFormatDropdown() {
  const dropdown = document.querySelector("[data-format-dropdown]");
  if (!dropdown) return;

  const input = dropdown.querySelector("[data-format-input]");
  const menu = dropdown.querySelector("[data-format-menu]");
  const select = dropdown.querySelector("[data-format-select]");
  if (!input || !menu || !select) return;

  const options = Array.from(select.options).map((option) => ({
    value: option.value,
    label: option.text,
  }));

  const selectedOption = options.find((option) => option.value === select.value);
  input.value = selectedOption ? selectedOption.label : options[0]?.label || "";

  const closeMenu = () => {
    menu.classList.remove("is-open");
    menu.innerHTML = "";
  };

  const openMenu = () => {
    menu.innerHTML = options
      .map(
        (option) =>
          `<button type="button" class="skill-group-option" data-format-value="${option.value}">${option.label}</button>`
      )
      .join("");
    menu.classList.add("is-open");
  };

  input.addEventListener("click", (event) => {
    event.stopPropagation();
    if (menu.classList.contains("is-open")) {
      closeMenu();
      return;
    }
    openMenu();
  });

  menu.addEventListener("mousedown", (event) => {
    const optionButton = event.target.closest(".skill-group-option");
    if (!optionButton) return;
    event.preventDefault();
    const value = optionButton.dataset.formatValue || "classic";
    const chosen = options.find((option) => option.value === value);
    select.value = value;
    input.value = chosen ? chosen.label : input.value;
    closeMenu();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-format-dropdown]")) {
      closeMenu();
    }
  });
}

function setupSkillGroupDropdowns() {
  const optionsDataNode = document.getElementById("skill-group-options-data");
  if (!optionsDataNode) return;

  const normalizeOptions = (values) =>
    [...new Set((values || []).map((value) => String(value).trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b));

  const parseOptionsNode = (node) => {
    try {
      return normalizeOptions(JSON.parse(node?.textContent || "[]"));
    } catch (_error) {
      return [];
    }
  };

  let options = parseOptionsNode(optionsDataNode);

  const setOptions = (values) => {
    options = normalizeOptions(values);
    optionsDataNode.textContent = JSON.stringify(options);
  };

  window.syncSkillGroupOptionsFromHtml = (doc) => {
    const nextNode = doc.getElementById("skill-group-options-data");
    if (!nextNode) return;
    setOptions(parseOptionsNode(nextNode));
  };

  window.addSkillGroupOption = (groupName) => {
    const candidate = String(groupName || "").trim();
    if (!candidate) return;
    if (options.includes(candidate)) return;
    setOptions([...options, candidate]);
  };

  const dropdowns = document.querySelectorAll("[data-skill-group-dropdown]");
  if (!dropdowns.length) return;

  const closeAllMenus = () => {
    document.querySelectorAll("[data-skill-group-menu]").forEach((menu) => {
      menu.classList.remove("is-open");
      menu.innerHTML = "";
    });
  };

  const renderMenu = (menu, inputValue) => {
    const query = (inputValue || "").trim().toLowerCase();
    const filtered = options.filter((item) => item.toLowerCase().includes(query));

    if (!filtered.length) {
      menu.classList.remove("is-open");
      menu.innerHTML = "";
      return;
    }

    menu.innerHTML = filtered
      .map(
        (item) =>
          `<button type="button" class="skill-group-option" data-group-value="${item.replace(/"/g, "&quot;")}">${item}</button>`
      )
      .join("");

    menu.classList.add("is-open");
  };

  dropdowns.forEach((dropdown) => {
    const input = dropdown.querySelector("[data-skill-group-input]");
    const menu = dropdown.querySelector("[data-skill-group-menu]");
    if (!input || !menu) return;

    input.addEventListener("focus", () => {
      closeAllMenus();
      renderMenu(menu, input.value);
    });

    input.addEventListener("input", () => {
      renderMenu(menu, input.value);
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        menu.classList.remove("is-open");
        menu.innerHTML = "";
      }
    });

    menu.addEventListener("mousedown", (event) => {
      const optionButton = event.target.closest(".skill-group-option");
      if (!optionButton) return;
      event.preventDefault();
      input.value = optionButton.dataset.groupValue || "";
      menu.classList.remove("is-open");
      menu.innerHTML = "";
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-skill-group-dropdown]")) {
      closeAllMenus();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupResumeSearch();
  setupResumeFormatDropdown();
  setupSkillGroupDropdowns();
  setupGitHubProjectImport();
  setupCollapsibleSections();
  setupInlineEditButtons();
  setupResumeBuilder();
});
