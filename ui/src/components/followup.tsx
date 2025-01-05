import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'

type FollowupInputProps = {
  onSubmit: (query: string) => void
  disabled?: boolean
}

export function FollowupInput({ onSubmit, disabled }: FollowupInputProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || disabled) return

    onSubmit(query.trim())
    setQuery('')
  }

  return (
    <form onSubmit={handleSubmit} className="mt-6 animate-in fade-in slide-in-from-bottom-4">
      <div className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a follow-up question..."
          className="flex-1"
          disabled={disabled}
        />
        <Button type="submit" size="icon" disabled={disabled || !query.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  )
}
