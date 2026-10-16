const API_BASE_URL = "";

export class ApiError extends Error {
  constructor(message, code, status) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const payload = await response.json().catch(() => ({
    success: false,
    message: "Invalid server response"
  }));

  if (!response.ok) {
    throw new ApiError(
      payload.message || "Request failed",
      payload.code || "REQUEST_FAILED",
      response.status
    );
  }

  return payload;
}

export async function getBooks(status = "AVAILABLE") {
  const query = new URLSearchParams({ status });

  return request(`/api/books?${query.toString()}`, {
    method: "GET"
  });
}

export async function getAvailableBooks() {
  return getBooks("AVAILABLE");
}

export async function createBorrowRequest({ bookId, userId }) {
  return request("/api/borrow-requests", {
    method: "POST",
    body: JSON.stringify({
      bookId,
      userId
    })
  });
}