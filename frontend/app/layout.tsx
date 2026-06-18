// /home/workdir/attachments/layout.tsx
import React from 'react';
import './globals.css';

export const metadata = {
  title: 'Social Growth Intelligence',
  description: 'Instagram • x • Facebook Performance Analyst & Strategist',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-black">
      <body className="antialiased m-0 p-0">
        {children}
      </body>
    </html>
  );
}