import {
  getAvailableBooks,
  createBorrowRequest,
  ApiError
} from "../data/data.js";

const currentUserId = "user-uuid";

async function loadBooks() {
  const result = await getAvailableBooks();

  const booksContainer = document.querySelector("#books");

  booksContainer.innerHTML = result.books
    .map(
      (book) => `
        <article class="book-card">
          <h3>${book.title}</h3>
          <p>${book.author || "Unknown author"}</p>
          <button
            class="borrow-button"
            data-book-id="${book.id}"
          >
            Borrow
          </button>
        </article>
      `
    )
    .join("");

  document
    .querySelectorAll(".borrow-button")
    .forEach((button) => {
      button.addEventListener("click", () => {
        submitBorrowRequest(button.dataset.bookId);
      });
    });
}

async function submitBorrowRequest(bookId) {
  try {
    const result = await createBorrowRequest({
      bookId,
      userId: currentUserId
    });

    alert(result.message);
    console.log("Created request:", result.borrowRequest);
  } catch (error) {
    if (error instanceof ApiError) {
      alert(error.message);
      return;
    }

    alert("Unexpected error");
    console.error(error);
  }
}

loadBooks().catch((error) => {
  console.error(error);
  alert("Unable to load books");
});