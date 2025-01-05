import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import { SearchBar } from '@/components/search-bar'
import { Results } from '@/components/results'
import { Skeleton } from '@/components/ui/skeleton'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

async function SearchResults({ query }: { query: string }) {
  // Move the fetch into a separate component to trigger Suspense
  const res = await fetch(
    `${BACKEND_URL}/api/query?q=${encodeURIComponent(query)}`,
    { cache: 'no-store' }
  )

  if (!res.ok) throw new Error('Failed to fetch results')
  const results = await res.json()

  return <Results response={results} initialQuery={query} />
}

function LoadingSkeleton() {
  return (
    <div className="space-y-8">
      {/* Title skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
      </div>

      {/* Content sections skeleton */}
      {[0, 1, 2].map((i) => (
        <div key={i} className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-[95%]" />
            <Skeleton className="h-4 w-[90%]" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default async function SearchPage({
  searchParams
}: {
  searchParams: { q?: string }
}) {
  const query = searchParams.q

  if (!query) {
    notFound()
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="border-b">
        <div className="max-w-5xl mx-auto p-4">
          <SearchBar />
        </div>
      </div>
      <div className="max-w-5xl mx-auto p-6">
        <Suspense fallback={<LoadingSkeleton />}>
          <SearchResults query={query} />
        </Suspense>
      </div>
    </main>
  )
}
