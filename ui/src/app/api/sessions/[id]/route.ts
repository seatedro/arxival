import { getSession, makeSessionPublic, verifySessionAccess } from "@/lib/db";
import { NextRequest } from "next/server";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const userId = req.headers.get("X-User-Id");

  try {
    const p = await params;
    console.log(p);
    const session = await getSession(p.id);
    if (!session) {
      return Response.json({ error: "Session not found" }, { status: 404 });
    }

    if (userId && !(await verifySessionAccess(p.id, userId))) {
      return Response.json({ error: "Unauthorized" }, { status: 403 });
    }

    return Response.json(session);
  } catch (error) {
    console.error("Failed to get session:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const p = await params;
  const userId = req.headers.get("X-User-Id");

  try {
    const session = await getSession(p.id);
    if (!session) {
      return Response.json({ error: "Session not found" }, { status: 404 });
    }

    if (userId && !(await verifySessionAccess(p.id, userId))) {
      return Response.json({ error: "Unauthorized" }, { status: 403 });
    }

    await makeSessionPublic(p.id);

    return Response.json({ message: "Chat made public!" });
  } catch (error) {
    console.error("Failed to get session:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}
