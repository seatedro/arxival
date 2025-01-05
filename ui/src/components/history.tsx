'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ScrollArea } from '@/components/ui/scroll-area'

type HistoryItem = {
  query: string
  timestamp: number
  url: string
}

export function History() {
  const [history, setHistory] = useState<HistoryItem[]>([])

  useEffect(() => {
    const storedHistory = localStorage.getItem('searchHistory')
    if (storedHistory) {
      setHistory(JSON.parse(storedHistory))
    }
  }, [])

  if (history.length === 0) return null

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Recent Searches</h2>
      <ScrollArea className="h-[300px] rounded-md border p-4">
        <div className="space-y-4">
          {history.map((item, index) => (
            <Link
              key={index}
              href={item.url}
              className="block p-3 rounded-lg hover:bg-muted transition-colors"
            >
              <p className="font-medium">{item.query}</p>
              <p className="text-sm text-muted-foreground">
                {new Date(item.timestamp).toLocaleString()}
              </p>
            </Link>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
