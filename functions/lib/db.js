import { createClient } from "@supabase/supabase-js";

export function getDatabase(env) {
  const secretKey =
    env.SUPABASE_SECRET_KEY ||
    env.SUPABASE_SERVICE_ROLE_KEY;

  if (!env.SUPABASE_URL || !secretKey) {
    throw new Error("Supabase environment variables are missing");
  }

  return createClient(env.SUPABASE_URL, secretKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  });
}