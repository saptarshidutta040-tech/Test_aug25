import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ZomatoAI — Find Your Perfect Restaurant',
  description: 'AI-powered restaurant recommendations from 9,200+ Zomato restaurants. Powered by Groq LLM.',
  keywords: ['restaurant', 'AI', 'Zomato', 'recommendation', 'Bangalore', 'food'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-background text-on-surface font-body min-h-screen flex flex-col pt-16"
            style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/cubes.png')" }}>

        {/* Atmospheric gradients */}
        <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-[-1]">
          <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-tertiary/5 rounded-full blur-[150px]" />
        </div>

        {/* Top Nav */}
        <nav className="fixed top-0 left-0 w-full z-50 glass-panel border-t-0 border-l-0 border-r-0 rounded-none">
          <div className="flex justify-between items-center px-container-margin h-16 max-w-7xl mx-auto">
            <div className="text-headline-md font-headline font-black text-primary drop-shadow-[0_0_8px_rgba(125,211,252,0.3)]">
              ZomatoAI
            </div>
            <div className="hidden md:flex gap-md">
              <a href="#" className="text-primary font-bold border-b-2 border-primary pb-1 text-label-md hover:text-primary transition-colors duration-200">Discover</a>
              <a href="#" className="text-on-surface-variant text-label-md hover:text-primary transition-colors duration-200">Trending</a>
              <a href="#" className="text-on-surface-variant text-label-md hover:text-primary transition-colors duration-200">Saved</a>
            </div>
            <button className="hover:text-primary transition-colors duration-200 text-on-surface-variant">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>account_circle</span>
            </button>
          </div>
        </nav>

        {/* Page content */}
        <main className="flex-grow flex flex-col relative w-full max-w-7xl mx-auto px-container-margin py-xl">
          {children}
        </main>

        {/* Footer */}
        <footer className="w-full py-base px-container-margin flex flex-col md:flex-row justify-between items-center gap-xs glass-panel border-b-0 border-l-0 border-r-0 rounded-none mt-auto">
          <div className="text-on-surface-variant text-label-sm">Powered by Groq LLM &amp; Zomato Data</div>
          <div className="flex gap-md">
            <a href="#" className="text-on-surface-variant text-label-sm hover:text-primary transition-colors">Privacy Policy</a>
            <a href="#" className="text-on-surface-variant text-label-sm hover:text-primary transition-colors">Terms of Service</a>
            <a href="#" className="text-on-surface-variant text-label-sm hover:text-primary transition-colors">API Status</a>
          </div>
        </footer>
      </body>
    </html>
  );
}
