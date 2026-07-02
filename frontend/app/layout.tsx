import React from 'react';
import './globals.css';

export const metadata = {
  title: 'Instagram Growth OS',
  description: 'Apify + AI Powered Instagram Engagement Analyzer',
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
