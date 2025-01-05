'use client'

import { useState, useEffect } from 'react'
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Menu } from 'lucide-react'

type HistoryItem = {
  query: string
  timestamp: number
  url: string
}

export function Sidebar() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const storedHistory = localStorage.getItem('searchHistory')
    if (storedHistory) {
      setHistory(JSON.parse(storedHistory))
    }

    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const SidebarContent = () => (
    <div className="w-full h-full bg-background border-r">
      <h2 className="text-lg font-semibold p-4">Search History</h2>
      <ScrollArea className="h-[calc(100vh-60px)]">
        {history.map((item, index) => (
          <a
            key={index}
            href={item.url}
            className="block p-4 hover:bg-accent transition-colors"
          >
            <p className="font-medium truncate">{item.query}</p>
            <p className="text-sm text-muted-foreground">
              {new Date(item.timestamp).toLocaleString()}
            </p>
          </a>
        ))}
      </ScrollArea>
    </div>
  )

  if (isMobile) {
    return (
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="outline" size="icon" className="md:hidden">
            <Menu className="h-4 w-4" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-4/5">
          <SidebarContent />
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <aside className="hidden md:block w-1/5 min-w-[250px]">
      <SidebarContent />
    </aside>
  )
}

