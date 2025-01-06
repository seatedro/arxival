import type { Metadata } from "next";
import { Newsreader, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";

const newsreader = Newsreader({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-news",
});
const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-source",
});

export const metadata: Metadata = {
  title: "Research Paper Search",
  description: "Search and analyze research papers",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${newsreader.variable} ${sourceSerif.variable}`}
    >
      <body className="bg-background/10 font-serif">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <ThemeToggle />
          <div
            className="-z-[1] pointer-events-none absolute inset-0 bg-repeat bg-[size:180px]"
            style={{ backgroundImage: "url(/noise.png)" }}
          ></div>
        </ThemeProvider>
      </body>
    </html>
  );
}
