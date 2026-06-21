import { ImageResponse } from "next/og";
import { data, pct, num } from "@/lib/data";

export const runtime = "edge";
export const alt = "Darwin — evolutionary trading-strategy foundry for BNB Chain";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  const m = data.metrics;
  const stats = [
    { label: "Return", value: pct(m.totalReturn, 1) },
    { label: "Sharpe", value: num(m.sharpe, 2) },
    { label: "Max DD", value: pct(m.maxDrawdown, 1) },
    { label: "Adherence", value: `${(m.ruleAdherence * 100).toFixed(0)}%` },
  ];

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px",
          position: "relative",
          background: "linear-gradient(135deg, #0A0A0B 0%, #14120a 55%, #0a0f0c 100%)",
          color: "white",
          fontFamily: "sans-serif",
        }}
      >
        {/* accent glows */}
        <div
          style={{
            position: "absolute",
            top: -160,
            right: -120,
            width: 520,
            height: 520,
            borderRadius: 9999,
            background: "radial-gradient(circle, rgba(240,185,11,0.35), rgba(240,185,11,0))",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: -180,
            left: -120,
            width: 520,
            height: 520,
            borderRadius: 9999,
            background: "radial-gradient(circle, rgba(16,185,129,0.28), rgba(16,185,129,0))",
          }}
        />
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "linear-gradient(135deg, #F0B90B, #10B981)",
              fontSize: 32,
            }}
          >
            🧬
          </div>
          <div style={{ fontSize: 34, fontWeight: 700, letterSpacing: -1 }}>Darwin</div>
          <div
            style={{
              marginLeft: 8,
              fontSize: 18,
              color: "#F0B90B",
              border: "1px solid rgba(240,185,11,0.4)",
              borderRadius: 999,
              padding: "6px 16px",
            }}
          >
            BNB Hack · Track 2
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ fontSize: 68, fontWeight: 800, lineHeight: 1.05, letterSpacing: -2, maxWidth: 980 }}>
            Evolutionary trading-strategy foundry
          </div>
          <div style={{ fontSize: 28, color: "#a1a1aa", maxWidth: 920 }}>
            A population of strategies, bred on live CoinMarketCap data into a champion — with an on-chain identity on BNB Chain.
          </div>
        </div>

        <div style={{ display: "flex", gap: 18 }}>
          {stats.map((s) => (
            <div
              key={s.label}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 4,
                padding: "20px 28px",
                borderRadius: 18,
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div style={{ fontSize: 40, fontWeight: 700, color: "#34D399" }}>{s.value}</div>
              <div style={{ fontSize: 20, color: "#71717a" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size }
  );
}
