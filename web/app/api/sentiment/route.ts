import { NextResponse } from "next/server";

// Server-side CMC fetch — the key never reaches the browser.
export const runtime = "nodejs";
export const revalidate = 600; // cache the live value for 10 minutes

function classify(v: number): string {
  if (v < 25) return "Extreme Fear";
  if (v < 45) return "Fear";
  if (v < 55) return "Neutral";
  if (v < 75) return "Greed";
  return "Extreme Greed";
}

export async function GET() {
  const key = process.env.CMC_PRO_API_KEY;
  if (!key) {
    return NextResponse.json({ live: false, reason: "no CMC_PRO_API_KEY configured" }, { status: 200 });
  }
  try {
    const res = await fetch("https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest", {
      headers: { "X-CMC_PRO_API_KEY": key, Accept: "application/json" },
      next: { revalidate: 600 },
    });
    const payload = await res.json();
    const ec = payload?.status?.error_code;
    if (ec && String(ec) !== "0") {
      return NextResponse.json({ live: false, reason: `CMC error ${ec}` }, { status: 200 });
    }
    const value = Math.round(Number(payload?.data?.value));
    if (!Number.isFinite(value)) {
      return NextResponse.json({ live: false, reason: "no value in CMC response" }, { status: 200 });
    }
    return NextResponse.json({
      live: true,
      value,
      classification: payload?.data?.value_classification || classify(value),
      source: "CoinMarketCap",
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : "fetch failed";
    return NextResponse.json({ live: false, reason }, { status: 200 });
  }
}
