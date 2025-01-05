'use client'

import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search } from 'lucide-react'
import { useSession } from '@/hooks'

export function SearchBar() {
  const router = useRouter()
  const { createNewSession } = useSession()

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const query = formData.get('query')?.toString()

    e.currentTarget.querySelector('button')?.setAttribute('disabled', 'true')

    const session = await createNewSession()

    if (!query?.trim()) return

    // Add to history
    const historyItem = {
      query: query.trim(),
      timestamp: Date.now(),
      url: `/search?q=${encodeURIComponent(query.trim())}&session=${session.id}`,
      sessionId: session.id
    }

    const history = JSON.parse(localStorage.getItem('searchHistory') || '[]')
    localStorage.setItem(
      'searchHistory',
      JSON.stringify([historyItem, ...history].slice(0, 50))
    )

    // Navigate to results
    router.push(historyItem.url)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            name="query"
            type="text"
            placeholder="What would you like to research?"
            className="pl-10 py-6 text-lg"
            required
          />
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground"
          />
        </div>
        <Button type="submit" size="lg">
          Search
        </Button>
      </div>
    </form>
  )
}
