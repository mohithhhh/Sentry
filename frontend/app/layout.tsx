import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sentry",
  description: "TODO: fill in project description",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
