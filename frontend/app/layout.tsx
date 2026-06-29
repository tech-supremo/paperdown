import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Paperdown — PDF to Markdown",
  description: "Convert PDF documents to clean Markdown locally.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
