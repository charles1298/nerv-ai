import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "NERV AI — Tutoria Inteligente",
  description: "Sistema de Inteligência Educacional Adaptativa alinhado à BNCC",
  manifest: "/manifest.json",
  icons: { icon: "/nerv-mark.png" },
};

export const viewport = {
  // Equivalente em hex de oklch(0.82 0.15 165): a barra do navegador nao aceita oklch.
  themeColor: "#38DEA8",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
