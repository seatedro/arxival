import { NextRequest } from "next/server";
import { getOrCreateUser } from "@/lib/db";

export async function POST(req: NextRequest) {
  const body = await req.json();

  if (!body.id || !body.userAgent) {
    return Response.json({ error: "Missing required fields" }, { status: 400 });
  }

  try {
    const user = await getOrCreateUser(body.id, body.userAgent);
    return Response.json(user);
  } catch (error) {
    console.error("Failed to create/update user:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}
