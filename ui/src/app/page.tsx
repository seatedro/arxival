"use client";

import { SearchBar } from '@/components/search-bar'
import { History } from '@/components/history'

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-6 bg-background text-foreground">
      <div className="flex-1 w-full max-w-3xl flex flex-col items-center justify-center gap-8">
        <h1 className="text-4xl font-bold text-center">Research Paper Search</h1>
        <SearchBar />
      </div>
      <div className="w-full max-w-3xl mt-12">
        <History />
      </div>
    </main>
  )
}
