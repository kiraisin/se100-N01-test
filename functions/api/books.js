import { getDatabase } from "../lib/db.js";
import { json, options } from "../lib/http.js";

const ALLOWED_STATUSES = new Set([
  "AVAILABLE",
  "RESERVED",
  "ON_LOAN",
  "INACTIVE"
]);

export async function onRequestOptions({ env }) {
  return options(env);
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);

  // Mặc định frontend chỉ lấy sách khả dụng.
  const status = url.searchParams.get("status") || "AVAILABLE";

  if (!ALLOWED_STATUSES.has(status)) {
    return json(
      {
        success: false,
        code: "INVALID_BOOK_STATUS",
        message: "Invalid book status"
      },
      400,
      env
    );
  }

  try {
    const database = getDatabase(env);

    const { data, error } = await database
      .from("books")
      .select(
        "id, owner_user_id, title, author, isbn, description, status, created_at"
      )
      .eq("status", status)
      .order("created_at", { ascending: false });

    if (error) {
      console.error(error);

      return json(
        {
          success: false,
          code: "DATABASE_ERROR",
          message: "Unable to load books"
        },
        500,
        env
      );
    }

    const books = data.map((book) => ({
      id: book.id,
      ownerUserId: book.owner_user_id,
      title: book.title,
      author: book.author,
      isbn: book.isbn,
      description: book.description,
      status: book.status,
      createdAt: book.created_at
    }));

    return json(
      {
        success: true,
        books
      },
      200,
      env
    );
  } catch (error) {
    console.error(error);

    return json(
      {
        success: false,
        code: "INTERNAL_ERROR",
        message: "Internal server error"
      },
      500,
      env
    );
  }
}