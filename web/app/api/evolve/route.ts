import Anthropic from "@anthropic-ai/sdk";
import { NextResponse } from "next/server";
import { data } from "@/lib/data";
import { SYSTEM, mutatePrompt, extractJson, validateSpec } from "@/lib/llm";

// Calls Claude → must run on the Node runtime, not edge.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Mirror the offline engine: model + optional Anthropic-compatible gateway base URL.
const MODEL = process.env.DARWIN_MODEL || "claude-opus-4-8";
const BASE_URL = process.env.ANTHROPIC_BASE_URL || undefined;

// Best-effort guard so a public endpoint can't be hammered into burning your key.
// (Serverless is multi-instance, so this is a soft limit per warm instance.)
const HITS = new Map<string, number[]>();
const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 6;

function rateLimited(ip: string): boolean {
  const now = Date.now();
  const recent = (HITS.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  HITS.set(ip, recent);
  return recent.length > MAX_PER_WINDOW;
}

export async function POST(req: Request) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    return NextResponse.json(
      { error: "Live evolution is offline — no ANTHROPIC_API_KEY configured on the server." },
      { status: 503 },
    );
  }

  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
  if (rateLimited(ip)) {
    return NextResponse.json(
      { error: "Slow down — too many live evolutions. Try again in a moment." },
      { status: 429 },
    );
  }

  try {
    const client = new Anthropic({ apiKey: key, baseURL: BASE_URL });
    const prompt = mutatePrompt(data.champion, data.metrics, data.fearGreed.value);

    // No extended thinking → fast, snappy demo response. Bounded output.
    const msg = await client.messages.create({
      model: MODEL,
      max_tokens: 1500,
      system: SYSTEM,
      messages: [{ role: "user", content: prompt }],
    });

    const text = msg.content
      .filter((b): b is Anthropic.TextBlock => b.type === "text")
      .map((b) => b.text)
      .join("");

    const spec = validateSpec(extractJson(text));
    return NextResponse.json({ spec, model: msg.model });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Live evolution failed.";
    // Surface a clean, user-facing reason; never leak the key or stack.
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
