const book = {
  id: "book-01",
  ownerId: "user-02",
  status: "AVAILABLE"
};

const userId = "user-01";

export function validateBorrowRequest(book, userId) {
  if (!book) {
    return { valid: false, message: "Book not found." };
  }

  if (book.status !== "AVAILABLE") {
    return { valid: false, message: "Book is not available." };
  }

  if (book.ownerId === userId) {
    return { valid: false, message: "You cannot borrow your own book." };
  }

  return { valid: true, message: "Borrow request is valid." };
}

export async function createBorrowRequest(book, userId) {
    
  const validation = validateBorrowRequest(book, userId);

  if (!validation.valid) {
    return {
      success: false,
      message: validation.message
    };
  }

  const response = await fetch("/api/borrow-requests", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      bookId: book.id,
      borrowerId: userId
    })
  });

  const result = await response.json();

  if (!response.ok) {
    return {
      success: false,
      message: result.message || "Failed to create borrow request."
    };
  }

  return {
    success: true,
    message: "Borrow request created.",
    borrowRequest: result
  };
}