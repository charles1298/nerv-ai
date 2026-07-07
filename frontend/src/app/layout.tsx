import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "NERV AI — Tutoria Inteligente",
  description: "Sistema de Inteligência Educacional Adaptativa alinhado à BNCC",
  manifest: "/manifest.json",
  icons: { icon: "/icon.svg" },
};

export const viewport = {
  themeColor: "#7C3AED",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-nerv-bg font-body text-nerv-text antialiased">
        {children}
      </body>
    </html>
  );
}
