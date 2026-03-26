import { NextRequest, NextResponse } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; levelId: string }> },
) {
  try {
    const { orgId, levelId } = await params;
    const token = await getAccessToken();
    const res = await fetch(
      `${BACKEND_URL}/api/organizations/${orgId}/experience-levels/${levelId}/`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (res.status === 204) return new NextResponse(null, { status: 204 });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return errorResponse(error);
  }
}
