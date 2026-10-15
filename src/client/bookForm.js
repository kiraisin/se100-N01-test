export function renderBookForm(formEl, books, onSubmit) {
  formEl.replaceChildren();

  if (books.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "Chưa có sách nào khả dụng.";
    formEl.append(empty);
    return;
  }

  for (const book of books) {
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "bookId";
    radio.value = book.id;

    const label = document.createElement("label");
    label.append(radio, ` ${book.title} — người cho mượn: ${book.ownerUserId}`);
    formEl.append(label);
  }

  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Mượn";
  button.disabled = true;
  formEl.append(button);

  formEl.onchange = () => updateButton(formEl);
  formEl.onsubmit = (event) => {
    event.preventDefault();
    const chosen = selectedBookId(formEl);
    if (chosen) onSubmit(chosen);
  };
}

export function setSubmitting(formEl, isSubmitting) {
  formEl.dataset.submitting = String(isSubmitting);
  updateButton(formEl);
}

function updateButton(formEl) {
  const button = formEl.querySelector("button");
  if (!button) return;
  button.disabled =
    formEl.dataset.submitting === "true" || !selectedBookId(formEl);
}

function selectedBookId(formEl) {
  return formEl.querySelector('input[name="bookId"]:checked')?.value;
}
