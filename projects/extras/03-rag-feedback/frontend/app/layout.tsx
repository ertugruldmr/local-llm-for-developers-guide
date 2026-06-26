import type { ReactNode } from "react";

export const metadata = {
  title: "Product-Feedback RAG Assistant",
  description: "Grounded, cited answers over a local product-feedback corpus",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: "#F0EEE6", color: "#1A1915" }}>
        {children}
      </body>
    </html>
  );
}
