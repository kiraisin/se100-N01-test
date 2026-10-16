import { getDatabase } from "../lib/db.js";
import { json, options, readJson } from "../lib/http.js";

export async function onRequestOptions({ env }) {
  return options(env);
}

export async function onRequestPost({ request, env }) {
  const body = await readJson(request);

  const bookId = body?.bookId;
  const userId = body?.userId;

  if (!bookId || !userId) {
    return json(
      {
        success: false,
        code: "INVALID_REQUEST",
        message: "bookId and userId are required"
      },
      400,
      env
    );
  }

  try {
    const database = getDatabase(env);

    const { data: user, error: userError } = await database
      .from("users")
      .select("id, account_status, late_return_count")
      .eq("id", userId)
      .maybeSingle();

    if (userError) {
      console.error(userError);

      return json(
        {
          success: false,
          code: "DATABASE_ERROR",
          message: "Unable to check user"
        },
        500,
        env
      );
    }

    if (!user) {
      return json(
        {
          success: false,
          code: "USER_NOT_FOUND",
          message: "User does not exist"
        },
        404,
        env
      );
    }

    if (
      user.account_status !== "ACTIVE" ||
      user.late_return_count >= 3
    ) {
      return json(
        {
          success: false,
          code: "USER_BLOCKED",
          message: "User is not allowed to borrow books"
        },
        403,
        env
      );
    }

    const { data: book, error: bookError } = await database
      .from("books")
      .select("id, owner_user_id, status")
      .eq("id", bookId)
      .maybeSingle();

    if (bookError) {
      console.error(bookError);

      return json(
        {
          success: false,
          code: "DATABASE_ERROR",
          message: "Unable to check book"
        },
        500,
        env
      );
    }

    if (!book) {
      return json(
        {
          success: false,
          code: "BOOK_NOT_FOUND",
          message: "Book does not exist"
        },
        404,
        env
      );
    }

    if (book.owner_user_id === userId) {
      return json(
        {
          success: false,
          code: "CANNOT_BORROW_OWN_BOOK",
          message: "You cannot borrow your own book"
        },
        409,
        env
      );
    }

    if (book.status !== "AVAILABLE") {
      return json(
        {
          success: false,
          code: "BOOK_UNAVAILABLE",
          message: "This book is not available for borrowing"
        },
        409,
        env
      );
    }

    const { data: existingRequest, error: duplicateError } =
      await database
        .from("borrow_requests")
        .select("id")
        .eq("book_id", bookId)
        .eq("borrower_user_id", userId)
        .eq("status", "PENDING")
        .maybeSingle();

    if (duplicateError) {
      console.error(duplicateError);

      return json(
        {
          success: false,
          code: "DATABASE_ERROR",
          message: "Unable to check existing request"
        },
        500,
        env
      );
    }

    if (existingRequest) {
      return json(
        {
          success: false,
          code: "DUPLICATE_BORROW_REQUEST",
          message: "You already have a pending request for this book"
        },
        409,
        env
      );
    }

    const { data: createdRequest, error: insertError } =
      await database
        .from("borrow_requests")
        .insert({
          book_id: bookId,
          borrower_user_id: userId,
          status: "PENDING"
        })
        .select(
          "id, book_id, borrower_user_id, status, requested_at"
        )
        .single();

    if (insertError) {
      console.error(insertError);

      return json(
        {
          success: false,
          code: "CREATE_REQUEST_FAILED",
          message: "Unable to create borrow request"
        },
        500,
        env
      );
    }

    return json(
      {
        success: true,
        message: "Borrow request created successfully",
        borrowRequest: {
          id: createdRequest.id,
          bookId: createdRequest.book_id,
          borrowerUserId: createdRequest.borrower_user_id,
          status: createdRequest.status,
          requestedAt: createdRequest.requested_at
        }
      },
      201,
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