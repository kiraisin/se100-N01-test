
import { createBorrowRequest } from "./data.js";

export function validateBorrowRequest(book, user) {
  if (!book) {
    return {
      valid: false,
      message: "Book not found."
    };
  }

  if (!user) {
    return {
      valid: false,
      message: "User not found."
    };
  }

  if (
    user.account_status !== "ACTIVE" ||
    user.late_return_count >= 3
  ) {
    return {
      valid: false,
      message: "Your account is locked."
    };
  }

  if (book.status !== "AVAILABLE") {
    return {
      valid: false,
      message: "Book is not available."
    };
  }

  if (book.owner_user_id === user.id) {
    return {
      valid: false,
      message: "You cannot borrow your own book."
    };
  }

  return {
    valid: true,
    message: "Borrow request is valid."
  };
}

export async function submitBorrowRequest(book, user) {
  const validation = validateBorrowRequest(book, user);

  if (!validation.valid) {
    return {
      success: false,
      message: validation.message
    };
  }

  try {
    // data.js sends the request to the backend API.
    // The backend checks duplicate requests and other rules.
    const result = await createBorrowRequest({
      bookId: book.id
    });

    return {
      success: true,
      message: result.message || "Borrow request created successfully.",
      borrowRequest: result.borrowRequest
    };
  } catch (error) {
    return {
      success: false,
      message: error.message || "Failed to create borrow request."
    };
  }
}
