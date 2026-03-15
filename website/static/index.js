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

function refreshProfileLists() {
  fetch(window.location.pathname)
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
    });
}

function editBio(bioId, currentBio) {
  const updatedBio = prompt("Edit bio:", currentBio || "");
  if (updatedBio === null) return;
  if (!updatedBio.trim()) return;
  sendEditRequest("/edit-bio", { bioId: bioId, bio: updatedBio.trim() }).then(
    refreshProfileLists
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
  const uni = prompt("Institution name:", currentUni || "");
  if (uni === null) return;
  const location = prompt("Location:", currentLocation || "");
  if (location === null) return;
  const degree = prompt("Degree:", currentDegree || "");
  if (degree === null) return;
  const startYear = prompt("Start year:", currentStartYear || "");
  if (startYear === null) return;
  const endYear = prompt("End year:", currentEndYear || "");
  if (endYear === null) return;

  sendEditRequest("/edit-education", {
    educationId: educationId,
    uni: uni.trim(),
    location: location.trim(),
    degree: degree.trim(),
    start_year: startYear.trim(),
    end_year: endYear.trim(),
  }).then(refreshProfileLists);
}

function editExperience(
  experienceId,
  currentRole,
  currentCompany,
  currentDescription,
  currentStartDate,
  currentEndDate
) {
  const role = prompt("Role:", currentRole || "");
  if (role === null) return;
  const comp = prompt("Company:", currentCompany || "");
  if (comp === null) return;
  const desc = prompt("Description:", currentDescription || "");
  if (desc === null) return;
  const startDate = prompt("Start date (YYYY-MM-DD):", currentStartDate || "");
  if (startDate === null) return;
  const endDate = prompt(
    "End date (YYYY-MM-DD, leave blank if ongoing):",
    currentEndDate || ""
  );
  if (endDate === null) return;

  sendEditRequest("/edit-experience", {
    experienceId: experienceId,
    role: role.trim(),
    comp: comp.trim(),
    desc: desc.trim(),
    start_date: startDate.trim(),
    end_date: endDate.trim(),
  }).then(refreshProfileLists);
}

function editProject(projectId, currentProj, currentTool, currentDesc) {
  const proj = prompt("Project title:", currentProj || "");
  if (proj === null) return;
  const tool = prompt("Tool/Tech used:", currentTool || "");
  if (tool === null) return;
  const desc = prompt("Description:", currentDesc || "");
  if (desc === null) return;

  sendEditRequest("/edit-project", {
    projectId: projectId,
    proj: proj.trim(),
    tool: tool.trim(),
    desc: desc.trim(),
  }).then(refreshProfileLists);
}

function editSkill(skillId, currentSkill, currentGroup) {
  const data = prompt("Skill name:", currentSkill || "");
  if (data === null) return;
  if (!data.trim()) return;
  const group = prompt("Skill group:", currentGroup || "");
  if (group === null) return;

  sendEditRequest("/edit-skill", {
    skillId: skillId,
    data: data.trim(),
    group: group.trim(),
  }).then(refreshProfileLists);
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
  setupSkillGroupDropdowns();
});
