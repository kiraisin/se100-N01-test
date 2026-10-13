function getHeaders(env) {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
  };
}

export function json(data, status = 200, env = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: getHeaders(env)
  });
}

export function options(env = {}) {
  return new Response(null, {
    status: 204,
    headers: getHeaders(env)
  });
}

export async function readJson(request) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}