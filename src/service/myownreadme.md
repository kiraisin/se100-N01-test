## Calling the API to Create a Borrow Request

After validating a borrow request, we use `fetch()` to send a `POST` request to the backend API so it can save the request to the database.

### 1. Send the request

```js
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
```

- `fetch()` sends an HTTP request to the API endpoint.
- `method: "POST"` indicates that we want to create a new borrow request.
- `headers` tells the backend that the request body is JSON.
- `JSON.stringify()` converts the JavaScript object into a JSON string so it can be sent in the HTTP request body.
- `await` waits for the server to return an HTTP response before continuing.
- `response` is a `Response` object. It contains information about the HTTP response, including its status and the methods used to read its body.

We send the book ID and borrower ID because these identify the book being requested and the student making the request. The backend can generate other fields, such as the request ID, status, and creation timestamp.

### 2. Read the response body

```js
const result = await response.json();
```

The backend processes the request and, if successful, may return the saved borrow request as JSON.

For example:

```json
{
  "id": "request-001",
  "bookId": "book-123",
  "borrowerId": "user-456",
  "status": "PENDING",
  "createdAt": "2026-10-12T10:30:00.000Z"
}
```

`response.json()` reads the response body and parses the JSON into a JavaScript value. In this example, `result` becomes a JavaScript object containing the saved request's data, including its generated ID.

The exact response fields depend on the API implementation.

### 3. Check whether the request succeeded

```js
if (!response.ok) {
  return {
    success: false,
    message: result.message || "Failed to create borrow request."
  };
}
```

`response.ok` is `true` when the HTTP status is in the 200–299 range. If the response indicates failure, the function returns a failure result with an error message.

### 4. Return the saved request

```js
return {
  success: true,
  message: "Borrow request created.",
  borrowRequest: result
};
```

Here, `result` is the data returned by the API. We put it inside `borrowRequest` so the calling code can access the saved request and its fields.

The function's returned object has two levels:

- The outer object contains the result of the operation, including `success` and `message`.
- `borrowRequest` contains the request data returned by the backend.

The API is responsible for saving the request to the database. Returning `result` does not save it again; it simply passes the response data back to the code that called the function.

**Overall flow:** validate the request → send a `POST` request → backend validates and saves the request → receive the HTTP response → parse the response body → return the result.

*Note: The endpoint and response format above are examples. They must match the actual API contract agreed upon by the team.*