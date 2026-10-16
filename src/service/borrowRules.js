
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
     // createBorrowRequest() calls the API function in data.js.
  // If the API returns an unsuccessful HTTP status, data.js
  // throws an ApiError using `throw new ApiError(...)`.
  // That error travels back here and jumps to the catch block.
  // So the success return below only runs if the call succeeds.
    const result = await createBorrowRequest({
      bookId: book.id
    });

    return {
      success: true,
      message: result.message || "Borrow request created successfully.",
      borrowRequest: result.borrowRequest
    };
  } catch (error) {
     // Handles errors thrown by data.js, including API errors.
    return {
      success: false,
      message: error.message || "Failed to create borrow request."
    };
  }
}
