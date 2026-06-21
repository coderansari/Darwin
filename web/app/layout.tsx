import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const sans = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

const TITLE = "Darwin — evolutionary trading-strategy foundry for BNB Chain";
const DESC =
  "Darwin evolves a population of backtestable trading strategies on live CoinMarketCap data into a risk-respecting champion — with an on-chain ERC-8004 identity on BNB Chain.";

export const metadata: Metadata = {
  title: TITLE,
  description: DESC,
  metadataBase: new URL("https://darwin-foundry.vercel.app"),
  applicationName: "Darwin",
  keywords: ["BNB Chain", "trading", "evolutionary algorithm", "CoinMarketCap", "AI agent", "backtest"],
  openGraph: {
    title: TITLE,
    description: DESC,
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESC,
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon.png", type: "image/png" },
    ],
    apple: "/apple-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#0A0A0B",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <div className="page-bg" />
        {children}
      </body>
    </html>
  );
}
