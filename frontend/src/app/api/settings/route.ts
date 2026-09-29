import { NextResponse } from "next/server";
import { fail, forbidden, sameOrigin } from "@/server/guard";
import { getSettings, putSettings } from "@/server/aws";

export const dynamic = "force-dynamic";

export async function GET() {
  try { return NextResponse.json(await getSettings()); } catch (e) { return fail(e); }
}

export async function PUT(req: Request) {
  if (!sameOrigin(req)) return forbidden();
  try { return NextResponse.json(await putSettings(await req.json())); } catch (e) { return fail(e); }
}
